# server/dashboard/staff/routers/invoice.py
"""
Router pentru gestionarea facturilor și ofertelor.
"""
from __future__ import annotations
import pprint
import traceback
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Query, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Invoice, InvoiceType, Cart, Order, Client, CartItem, OrderItem
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, date_only, get_invoice_status, get_local_timezone
from server.dashboard.utils import decimal_to_float
from services.models.invoice_service import InvoiceService
from services.models.cart_service import CartService

from services.dashboard.pdf_service_reportlab import PDFService
from services.dashboard.email_service import EmailService
from services.dashboard.telegram_invoice_service import TelegramInvoiceService

import logging

logger = logging.getLogger(__name__)

invoice_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")


templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['date_only'] = date_only
templates.env.filters['to_float'] = decimal_to_float
templates.env.filters['get_invoice_status'] = get_invoice_status


# Debug - verifică că filtrul e înregistrat
# print("DEBUG: Filters registered:", list(templates.env.filters.keys()))


@invoice_router.get("/", response_class=HTMLResponse)
async def invoice_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        invoice_type: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,  # active, expired, converted
        client_id: Optional[int] = Query(None),
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă toate invoice-urile cu filtre."""

    # Get current time in local timezone for proper comparison
    local_tz = get_local_timezone()
    now_local = datetime.now(local_tz)
    now_utc = datetime.utcnow()

    print(f"DEBUG: Current UTC time: {now_utc}")
    print(f"DEBUG: Current local time: {now_local}")

    # Query de bază
    query = select(Invoice).options(
        selectinload(Invoice.cart).selectinload(Cart.client),
        selectinload(Invoice.order).selectinload(Order.client)
    )

    # Filtre
    filters = []

    if invoice_type:
        filters.append(Invoice.invoice_type == InvoiceType(invoice_type))

    if search:
        filters.append(
            or_(
                Invoice.invoice_number.ilike(f"%{search}%"),
                Invoice.client_name.ilike(f"%{search}%"),
                Invoice.client_email.ilike(f"%{search}%")
            )
        )

    if status:
        if status == "active":
            filters.append(
                and_(
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.valid_until > now_utc,
                    Invoice.converted_to_order == False
                )
            )
        elif status == "expired":
            filters.append(
                and_(
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.valid_until <= now_utc,
                    Invoice.converted_to_order == False
                )
            )
        elif status == "converted":
            filters.append(Invoice.converted_to_order == True)

    if client_id:
        # Filtrare prin cart sau order
        query = query.outerjoin(Cart).outerjoin(Order).where(
            or_(
                Cart.client_id == client_id,
                Order.client_id == client_id
            )
        )

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count(Invoice.id))
    if filters:
        total_query = total_query.where(and_(*filters))

    if client_id:
        total_query = total_query.outerjoin(Cart).outerjoin(Order).where(
            or_(
                Cart.client_id == client_id,
                Order.client_id == client_id
            )
        )

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare și paginare
    offset = (page - 1) * per_page
    query = query.order_by(Invoice.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    invoices = result.scalars().all()

    # Adaugă status calculat pentru fiecare invoice
    for invoice in invoices:
        if invoice.is_quote:
            if invoice.converted_to_order:
                invoice.calculated_status = "converted"
                invoice.status_badge = "bg-success"
                invoice.status_text = "Convertită"
            elif invoice.valid_until and invoice.valid_until < now_utc:
                invoice.calculated_status = "expired"
                invoice.status_badge = "bg-danger"
                invoice.status_text = "Expirată"
            else:
                invoice.calculated_status = "active"
                invoice.status_badge = "bg-primary"  # Albastru în loc de galben
                invoice.status_text = "Activă"
        else:  # is_invoice
            if invoice.is_cancelled:
                invoice.calculated_status = "cancelled"
                invoice.status_badge = "bg-danger"
                invoice.status_text = "Anulată"
            else:
                invoice.calculated_status = "issued"
                invoice.status_badge = "bg-success"  # Verde în loc de info
                invoice.status_text = "Emisă"

        # Debug pentru primele 3
        if invoices.index(invoice) < 3:
            print(f"DEBUG Set for {invoice.invoice_number}: badge={invoice.status_badge}, text={invoice.status_text}")

    # Client info pentru filtrare
    filtered_client = None
    if client_id:
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        filtered_client = client_result.scalar_one_or_none()

    # Statistici
    stats = {
        "total_quotes": await db.scalar(
            select(func.count(Invoice.id))
            .where(Invoice.invoice_type == InvoiceType.QUOTE)
        ),
        "active_quotes": await db.scalar(
            select(func.count(Invoice.id))
            .where(
                and_(
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.valid_until > now_utc,
                    Invoice.converted_to_order == False
                )
            )
        ),
        "total_invoices": await db.scalar(
            select(func.count(Invoice.id))
            .where(Invoice.invoice_type == InvoiceType.INVOICE)
        ),
        "conversion_rate": 0  # To be calculated
    }

    # Calcul rată conversie
    if stats["total_quotes"] > 0:
        converted = await db.scalar(
            select(func.count(Invoice.id))
            .where(
                and_(
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.converted_to_order == True
                )
            )
        )
        stats["conversion_rate"] = (converted / stats["total_quotes"]) * 100

    # Navigare înapoi pentru client
    back_url = None
    back_text = None
    page_title = "Facturi și Oferte"

    if filtered_client:
        back_url = f"/dashboard/staff/client/{client_id}"
        back_text = f"Înapoi la {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"
        page_title = f"Facturi - {filtered_client.first_name or 'Client'} {filtered_client.last_name or ''}"

    context = await get_template_context(request, staff)
    context.update({
        "page_title": page_title,
        "invoices": invoices,
        "stats": stats,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
        "type_filter": invoice_type,
        "status_filter": status,
        "search_query": search,
        "client_filter": client_id,
        "filtered_client": filtered_client,
        "back_url": back_url,
        "back_text": back_text,
        "now": now_utc,  # Use UTC time for comparison
        "now_local": now_local,  # Also pass local time if needed
        "user": staff  # Pentru can_delete în template
    })

    return templates.TemplateResponse("invoice/list.html", context)


@invoice_router.get("/{invoice_id}", response_class=HTMLResponse)
async def invoice_detail(
        request: Request,
        invoice_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii invoice cu preview."""

    result = await db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(
            selectinload(Invoice.cart)
            .selectinload(Cart.items)
            .selectinload(CartItem.product),
            selectinload(Invoice.cart)
            .selectinload(Cart.client),
            selectinload(Invoice.order)
            .selectinload(Order.items)
            .selectinload(OrderItem.product),
            selectinload(Invoice.order)
            .selectinload(Order.client)
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice negăsit")

    # Obține items și client pentru afișare
    items = []
    client = None

    if invoice.is_quote and invoice.cart:
        items = invoice.cart.items
        client = invoice.cart.client
    elif invoice.is_invoice and invoice.order:
        items = invoice.order.items
        client = invoice.order.client

    # Verifică dacă este expirat (pentru oferte)
    is_expired = False
    if invoice.is_quote and invoice.valid_until:
        is_expired = invoice.valid_until < datetime.utcnow()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": invoice.display_name,
        "invoice": invoice,
        "items": items,
        "client": client,
        "is_expired": is_expired,
        "now": datetime.utcnow(),
        # Calculează valorile pentru template
        "subtotal": float(invoice.total_amount) / 1.2,
        "tva_amount": float(invoice.total_amount) - (float(invoice.total_amount) / 1.2),
        "total": float(invoice.total_amount)
    })

    return templates.TemplateResponse("invoice/detail.html", context)


@invoice_router.post("/{invoice_id}/cancel")
async def cancel_invoice(
        invoice_id: int,
        reason: str = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Anulează o factură (nu o șterge!)."""

    try:
        invoice = await InvoiceService.cancel_invoice(
            db=db,
            invoice_id=invoice_id,
            reason=reason,
            staff_id=staff.id
        )

        logger.info(f"Invoice {invoice.invoice_number} cancelled by {staff.email}. Reason: {reason}")

        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?success=cancelled",
            status_code=303
        )

    except ValueError as e:
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error={str(e)}",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error cancelling invoice: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error=cancel_failed",
            status_code=303
        )


@invoice_router.post("/quote/generate")
async def generate_quote(
        cart_id: int = Form(...),
        valid_days: int = Form(3),  # Default 3 zile
        notes: Optional[str] = Form(None),
        send_email: bool = Form(False),
        send_telegram: bool = Form(False),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Generează ofertă din coș cu PDF."""

    print(f"DEBUG: Starting quote generation for cart {cart_id}")
    print(f"DEBUG: Valid days: {valid_days}, Notes: {notes}")
    print(f"DEBUG: Send email: {send_email}, Send telegram: {send_telegram}")

    try:

        # Verifică dacă coșul există
        cart_check = await db.execute(
            select(Cart).where(Cart.id == cart_id)
        )
        cart_exists = cart_check.scalar_one_or_none()
        if not cart_exists:
            print(f"ERROR: Cart {cart_id} not found!")
            return RedirectResponse(
                url=f"/dashboard/staff/cart?error=cart_not_found",
                status_code=303
            )

        # Verifică dacă coșul există deja o ofertă activă
        existing = await db.execute(
            select(Invoice)
            .where(
                and_(
                    Invoice.cart_id == cart_id,
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.valid_until > datetime.utcnow(),
                    Invoice.converted_to_order == False
                )
            )
        )
        if existing.scalar_one_or_none():
            print(f"DEBUG: Active quote already exists for cart {cart_id}")
            return RedirectResponse(
                url=f"/dashboard/staff/cart/{cart_id}?error=active_quote_exists",
                status_code=303
            )

        print(f"DEBUG: Creating quote from cart...")

        # Generează oferta
        invoice = await InvoiceService.create_quote_from_cart(
            db=db,
            cart_id=cart_id,
            valid_days=valid_days,
            notes=notes
        )

        print(f"DEBUG: Quote created with ID {invoice.id}, number {invoice.invoice_number}")

        # Generează PDF
        try:
            print(f"DEBUG: Generating PDF...")
            pdf_path = await PDFService.generate_invoice_pdf(invoice, db)
            print(f"DEBUG: PDF generation returned: {pdf_path}")

            if pdf_path:
                invoice.document_path = pdf_path
                await db.commit()
                print(f"DEBUG: PDF path saved to database: {pdf_path}")
                # Verifică în DB
                await db.refresh(invoice)
                print(f"DEBUG: Invoice document_path after refresh: {invoice.document_path}")
            else:
                print(f"ERROR: PDF generation returned None or empty path")

        except Exception as pdf_error:
            print(f"ERROR generating PDF: {str(pdf_error)}")
            print(f"ERROR type: {type(pdf_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            # NU arunca excepția, continuă fără PDF
            invoice.document_path = None
            await db.commit()
            print(f"WARNING: Continuing without PDF due to error")

        # Trimite notificări dacă e cerut
        if send_email or send_telegram:
            print(f"DEBUG: Processing notifications...")
            cart_result = await db.execute(
                select(Cart).where(Cart.id == cart_id).options(selectinload(Cart.client))
            )
            cart = cart_result.scalar_one()

            if send_email and invoice.client_email:
                try:
                    print(f"DEBUG: Sending email to {invoice.client_email}")
                    success = await EmailService.send_invoice_email(
                        invoice,
                        invoice.document_path,
                        invoice.client_email,
                        invoice.client_name
                    )
                    if success:
                        invoice.sent_at = datetime.utcnow()
                        invoice.sent_via = "email"
                        print(f"DEBUG: Email sent successfully")
                except Exception as email_error:
                    print(f"ERROR sending email: {str(email_error)}")

            if send_telegram and cart.client.telegram_id:
                try:
                    print(f"DEBUG: Sending telegram to {cart.client.telegram_id}")
                    # Inițializează Telegram service cu bot-ul existent
                    from cfg import bot  # Presupunem că ai bot instance în cfg
                    telegram_service = TelegramInvoiceService(bot)

                    success = await telegram_service.send_quote_with_actions(
                        invoice,
                        invoice.document_path,
                        cart.client.telegram_id,
                        invoice.client_name
                    )
                    if success:
                        invoice.sent_at = datetime.utcnow()
                        invoice.sent_via = "telegram" if not send_email else "email,telegram"
                        print(f"DEBUG: Telegram sent successfully")
                except Exception as tg_error:
                    print(f"ERROR sending telegram: {str(tg_error)}")

            await db.commit()

        print(f"DEBUG: Quote generation completed successfully")
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice.id}?success=quote_created",
            status_code=303
        )

    except Exception as e:
        print(f"ERROR in generate_quote: {str(e)}")
        print(f"ERROR type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")

        await db.rollback()

        return RedirectResponse(
            url=f"/dashboard/staff/cart/{cart_id}?error=quote_failed",
            status_code=303
        )


@invoice_router.post("/invoice/generate")
async def generate_invoice(
        order_id: int = Form(...),
        notes: Optional[str] = Form(None),
        send_email: bool = Form(False),
        send_telegram: bool = Form(False),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Generează factură din comandă."""

    print(f"DEBUG: Starting invoice generation for order {order_id}")
    print(f"DEBUG: Notes: {notes}")
    print(f"DEBUG: Send email: {send_email}, Send telegram: {send_telegram}")

    try:
        # Import OrderService aici pentru a evita circular imports
        from services.models.order_service import OrderService

        invoice = await OrderService.generate_invoice(
            db=db,
            order_id=order_id,
            notes=notes
        )

        print(f"DEBUG: Invoice created with ID {invoice.id}, number {invoice.invoice_number}")

        # Generează PDF
        try:
            print(f"DEBUG: Generating PDF...")
            pdf_path = await PDFService.generate_invoice_pdf(invoice, db)
            invoice.document_path = pdf_path
            await db.commit()
            print(f"DEBUG: PDF generated at {pdf_path}")
        except Exception as pdf_error:
            print(f"ERROR generating PDF: {str(pdf_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            # Continuă fără PDF

        # Trimite notificări dacă e cerut
        if send_email or send_telegram:
            print(f"DEBUG: Processing notifications...")
            # Obține order cu client pentru notificări
            order_result = await db.execute(
                select(Order).where(Order.id == order_id).options(selectinload(Order.client))
            )
            order = order_result.scalar_one()

            if send_email and invoice.client_email:
                try:
                    print(f"DEBUG: Sending email to {invoice.client_email}")
                    success = await EmailService.send_invoice_email(
                        invoice,
                        invoice.document_path,
                        invoice.client_email,
                        invoice.client_name
                    )
                    if success:
                        invoice.sent_at = datetime.utcnow()
                        invoice.sent_via = "email"
                        print(f"DEBUG: Email sent successfully")
                except Exception as email_error:
                    print(f"ERROR sending email: {str(email_error)}")

            if send_telegram and order.client.telegram_id:
                try:
                    print(f"DEBUG: Sending telegram to {order.client.telegram_id}")
                    from cfg import bot
                    telegram_service = TelegramInvoiceService(bot)

                    success = await telegram_service.send_invoice_document(
                        invoice,
                        invoice.document_path,
                        order.client.telegram_id,
                        invoice.client_name
                    )
                    if success:
                        invoice.sent_at = datetime.utcnow()
                        invoice.sent_via = "telegram" if not send_email else "email,telegram"
                        print(f"DEBUG: Telegram sent successfully")
                except Exception as tg_error:
                    print(f"ERROR sending telegram: {str(tg_error)}")

            await db.commit()

        print(f"DEBUG: Invoice generation completed successfully")
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice.id}?success=invoice_created",
            status_code=303
        )

    except ValueError as e:
        print(f"ERROR ValueError: {str(e)}")
        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error={str(e)}",
            status_code=303
        )
    except Exception as e:
        print(f"ERROR in generate_invoice: {str(e)}")
        print(f"ERROR type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")

        await db.rollback()

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order_id}?error=invoice_failed",
            status_code=303
        )


@invoice_router.post("/quote/{invoice_id}/convert")
async def convert_quote_to_order(
        invoice_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "order")),
        db: AsyncSession = Depends(get_db)
):
    """Convertește ofertă în comandă."""

    try:
        order = await InvoiceService.convert_quote_to_order(db, invoice_id)

        return RedirectResponse(
            url=f"/dashboard/staff/order/{order.id}?success=converted_from_quote",
            status_code=303
        )

    except ValueError as e:
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error={str(e)}",
            status_code=303
        )
    except Exception:
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error=conversion_failed",
            status_code=303
        )


@invoice_router.post("/{invoice_id}/send")
async def send_invoice(
        invoice_id: int,
        method: str = Form(...),  # email, telegram, both
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Trimite invoice prin email/telegram."""

    try:
        result = await db.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.cart).selectinload(Cart.client),
                selectinload(Invoice.order).selectinload(Order.client)
            )
            .where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404)

        # Asigură-te că PDF există
        if not invoice.document_path or not Path(invoice.document_path).exists():
            invoice.document_path = await PDFService.generate_invoice_pdf(invoice, db)
            await db.commit()

        success = False
        errors = []

        # Email
        if method in ["email", "both"] and invoice.client_email:
            try:
                email_success = await EmailService.send_invoice_email(
                    invoice,
                    invoice.document_path,
                    invoice.client_email,
                    invoice.client_name
                )
                if email_success:
                    success = True
                else:
                    errors.append("email")
            except Exception as e:
                print(f"Email error: {e}")
                errors.append("email")

        # Telegram
        if method in ["telegram", "both"]:
            # Obține telegram_id
            client = None
            if invoice.cart_id:
                cart_result = await db.execute(
                    select(Cart).where(Cart.id == invoice.cart_id).options(selectinload(Cart.client))
                )
                cart = cart_result.scalar_one()
                client = cart.client
            elif invoice.order_id:
                order_result = await db.execute(
                    select(Order).where(Order.id == invoice.order_id).options(selectinload(Order.client))
                )
                order = order_result.scalar_one()
                client = order.client

            if client and client.telegram_id:
                try:
                    from cfg import bot
                    telegram_service = TelegramInvoiceService(bot)

                    if invoice.is_quote:
                        tg_success = await telegram_service.send_quote_with_actions(
                            invoice,
                            invoice.document_path,
                            client.telegram_id,
                            invoice.client_name
                        )
                    else:
                        tg_success = await telegram_service.send_invoice_document(
                            invoice,
                            invoice.document_path,
                            client.telegram_id,
                            invoice.client_name
                        )

                    if tg_success:
                        success = True
                    else:
                        errors.append("telegram")
                except Exception as e:
                    print(f"Telegram error: {e}")
                    errors.append("telegram")

        if success:
            invoice.sent_at = datetime.utcnow()
            invoice.sent_via = method
            await db.commit()

            return RedirectResponse(
                url=f"/dashboard/staff/invoice/{invoice_id}?success=sent",
                status_code=303
            )
        else:
            error_msg = "send_failed"
            if errors:
                error_msg = f"send_failed_{'_'.join(errors)}"
            return RedirectResponse(
                url=f"/dashboard/staff/invoice/{invoice_id}?error={error_msg}",
                status_code=303
            )

    except Exception as e:
        print(f"Send error: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error=send_failed",
            status_code=303
        )


@invoice_router.get("/{invoice_id}/download")
async def download_invoice(
        invoice_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Descarcă PDF invoice."""
    from fastapi.responses import FileResponse
    from pathlib import Path

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404)

    # Generează PDF dacă nu există
    if not invoice.document_path:
        try:
            invoice.document_path = await PDFService.generate_invoice_pdf(invoice, db)
            await db.commit()
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise HTTPException(
                status_code=500,
                detail="Eroare la generarea PDF"
            )

    # Construiește path-ul corect
    # Dacă path-ul este relativ, îl face absolut relativ la directorul curent
    pdf_path = Path(invoice.document_path)
    if not pdf_path.is_absolute():
        pdf_path = Path.cwd() / pdf_path

    # Verifică că fișierul există
    if not pdf_path.exists():
        # Încearcă să regenereze PDF-ul
        try:
            invoice.document_path = await PDFService.generate_invoice_pdf(invoice, db, force_regenerate=True)
            await db.commit()

            pdf_path = Path(invoice.document_path)
            if not pdf_path.is_absolute():
                pdf_path = Path.cwd() / pdf_path

        except Exception as e:
            print(f"Error regenerating PDF: {e}")
            raise HTTPException(
                status_code=404,
                detail="Fișierul PDF nu a fost găsit și nu a putut fi regenerat"
            )

    # Returnează fișierul
    return FileResponse(
        path=str(pdf_path),
        media_type='application/pdf',
        filename=f"{invoice.invoice_number}.pdf"
    )


@invoice_router.post("/{invoice_id}/delete")
async def delete_invoice(
        invoice_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "invoice")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge invoice (doar draft-uri sau expirate) și PDF-ul asociat."""

    try:
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=404)

        # Verifică dacă poate fi șters
        if invoice.is_invoice:
            # Nu șterge facturi niciodată
            return RedirectResponse(
                url=f"/dashboard/staff/invoice/{invoice_id}?error=cannot_delete_invoice",
                status_code=303
            )

        if invoice.converted_to_order:
            # Nu șterge oferte convertite
            return RedirectResponse(
                url=f"/dashboard/staff/invoice/{invoice_id}?error=cannot_delete_converted",
                status_code=303
            )

        # Salvează informații pentru logging
        invoice_number = invoice.invoice_number
        pdf_path = invoice.document_path

        # Șterge din baza de date
        await db.delete(invoice)
        await db.commit()

        logger.info(f"Invoice {invoice_number} deleted from database")

        # Șterge PDF-ul fizic folosind PDFService
        if pdf_path:
            pdf_deleted = PDFService.delete_invoice_pdf(pdf_path, cleanup_empty_dirs=True)
            if pdf_deleted:
                logger.info(f"PDF file deleted for invoice {invoice_number}")
            else:
                logger.warning(f"Could not delete PDF for invoice {invoice_number}")

        return RedirectResponse(
            url="/dashboard/staff/invoice?success=deleted",
            status_code=303
        )

    except Exception as e:
        logger.error(f"Error deleting invoice {invoice_id}: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/invoice/{invoice_id}?error=delete_failed",
            status_code=303
        )


# API Endpoints pentru AJAX
@invoice_router.get("/api/quote-preview/{cart_id}")
async def preview_quote(
        cart_id: int,
        valid_days: int = Query(30),
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Preview ofertă înainte de generare (AJAX)."""

    # Get cart with details
    cart = await CartService.get_cart_with_details(db, cart_id)

    if not cart:
        return JSONResponse(
            status_code=404,
            content={"error": "Cart not found"}
        )

    # Calculate totals
    subtotal = sum(
        float(item.price_snapshot) * item.quantity
        for item in cart.items
    )

    valid_until = datetime.utcnow() + timedelta(days=valid_days)

    return JSONResponse({
        "client_name": f"{cart.client.first_name or ''} {cart.client.last_name or ''}".strip() or "Client",
        "client_email": cart.client.email or "",
        "items_count": len(cart.items),
        "subtotal": subtotal,
        "valid_until": valid_until.strftime("%d.%m.%Y"),
        "valid_days": valid_days
    })


@invoice_router.get("/api/stats")
async def get_invoice_stats(
        period: str = Query("month"),  # today, week, month, year
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Statistici invoice pentru dashboard (AJAX)."""

    now = datetime.utcnow()

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    # Quotes stats
    quotes_created = await db.scalar(
        select(func.count(Invoice.id))
        .where(
            and_(
                Invoice.invoice_type == InvoiceType.QUOTE,
                Invoice.created_at >= start_date
            )
        )
    )

    quotes_converted = await db.scalar(
        select(func.count(Invoice.id))
        .where(
            and_(
                Invoice.invoice_type == InvoiceType.QUOTE,
                Invoice.created_at >= start_date,
                Invoice.converted_to_order == True
            )
        )
    )

    # Invoices stats
    invoices_created = await db.scalar(
        select(func.count(Invoice.id))
        .where(
            and_(
                Invoice.invoice_type == InvoiceType.INVOICE,
                Invoice.created_at >= start_date
            )
        )
    )

    # Total value
    total_value = await db.scalar(
        select(func.sum(Invoice.total_amount))
        .where(Invoice.created_at >= start_date)
    ) or 0

    return JSONResponse({
        "period": period,
        "quotes_created": quotes_created,
        "quotes_converted": quotes_converted,
        "conversion_rate": (quotes_converted / quotes_created * 100) if quotes_created > 0 else 0,
        "invoices_created": invoices_created,
        "total_value": float(total_value)
    })


