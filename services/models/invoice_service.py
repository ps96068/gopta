# services/models/invoice_service.py

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Invoice, InvoiceType, Cart, Order, CartItem
from services.models.cart_service import CartService


class InvoiceService:
    """Service pentru gestionarea invoice-urilor și ofertelor."""

    @staticmethod
    async def _generate_invoice_number(db: AsyncSession, invoice_type: InvoiceType) -> str:
        """
        Generează număr unic pentru invoice.
        Format: O_YYYYMMDD_XXXX pentru oferte, C_YYYYMMDD_XXXX pentru conturi
        """
        prefix = "O" if invoice_type == InvoiceType.QUOTE else "C"
        today = datetime.now().strftime("%Y%m%d")

        # Numără invoice-urile de același tip din ziua curentă
        result = await db.execute(
            select(func.count(Invoice.id))
            .where(
                Invoice.invoice_type == invoice_type,
                Invoice.invoice_number.like(f"{prefix}_{today}_%")
            )
        )
        count = result.scalar() or 0

        return f"{prefix}_{today}_{count + 1:04d}"

    @staticmethod
    async def create_quote_from_cart(
            db: AsyncSession,
            cart_id: int,
            valid_days: int = 30,
            notes: Optional[str] = None
    ) -> Invoice:
        """
        Creează ofertă din coș.
        """
        print(f"[InvoiceService] Creating quote from cart {cart_id}")

        # Obține coșul cu toate datele
        result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product),
                selectinload(Cart.client)
            )
        )
        cart = result.scalar_one_or_none()

        if not cart:
            raise ValueError(f"Cart {cart_id} not found")

        print(f"[InvoiceService] Cart found with {len(cart.items)} items")

        if not cart.items:
            raise ValueError("Cannot create quote from empty cart")

        print(f"[InvoiceService] Cart found with {len(cart.items)} items")

        # Verifică că clientul are date minime
        if not cart.client:
            raise ValueError("Cart has no client associated")

        # Calculează total
        total = await CartService.calculate_total(db, cart_id)
        print(f"[InvoiceService] Calculated total: {total}")

        # Generează număr ofertă
        invoice_number = await InvoiceService._generate_invoice_number(db, InvoiceType.QUOTE)
        print(f"[InvoiceService] Generated invoice number: {invoice_number}")

        # Construiește numele clientului
        client_name = f"{cart.client.first_name or ''} {cart.client.last_name or ''}".strip()
        if not client_name:
            client_name = f"Client {cart.client.id}"

        # Creează oferta
        invoice = Invoice(
            cart_id=cart_id,
            invoice_type=InvoiceType.QUOTE,
            invoice_number=invoice_number,

            client_name=client_name,
            client_email=cart.client.email or "",
            client_phone=cart.client.phone,
            total_amount=total,
            currency="MDL",
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
            notes=notes
        )

        print(f"[InvoiceService] Creating invoice object...")
        db.add(invoice)

        try:
            await db.commit()
            await db.refresh(invoice)
            print(f"[InvoiceService] Invoice created successfully with ID {invoice.id}")
        except Exception as e:
            print(f"[InvoiceService] ERROR committing invoice: {str(e)}")
            await db.rollback()
            raise

        return invoice

    @staticmethod
    async def convert_quote_to_order(
            db: AsyncSession,
            invoice_id: int
    ) -> Order:
        """
        Convertește o ofertă în comandă.
        """
        # Obține oferta
        result = await db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(selectinload(Invoice.cart))
        )
        invoice = result.scalar_one()

        if invoice.invoice_type != InvoiceType.QUOTE:
            raise ValueError("Only quotes can be converted to orders")

        if invoice.converted_to_order:
            raise ValueError("Quote already converted to order")

        if not invoice.cart_id:
            raise ValueError("Quote has no associated cart")

        # Creează comanda din coș
        from services.models.order_service import OrderService
        order = await OrderService.create_from_cart(
            db,
            invoice.cart_id,
            from_quote_id=invoice_id
        )

        # Marchează oferta ca convertită
        invoice.converted_to_order = True
        invoice.converted_at = datetime.utcnow()

        await db.commit()

        return order

    @staticmethod
    async def get_quotes_for_client(
            db: AsyncSession,
            client_id: int,
            include_expired: bool = False
    ) -> List[Invoice]:
        """Obține toate ofertele unui client."""
        query = select(Invoice).join(Cart).where(
            Cart.client_id == client_id,
            Invoice.invoice_type == InvoiceType.QUOTE
        )

        if not include_expired:
            query = query.where(Invoice.valid_until > datetime.utcnow())

        query = query.order_by(Invoice.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_invoice_from_order(
            db: AsyncSession,
            order_id: int,
            notes: Optional[str] = None
    ) -> Invoice:
        """
        Creează factură (cont) pentru comandă.
        """
        # Obține comanda cu client
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.client))
        )
        order = result.scalar_one()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Verifică dacă există deja invoice pentru această comandă
        existing = await db.execute(
            select(Invoice).where(Invoice.order_id == order_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Order {order.order_number} already has an invoice")

        # Generează număr factură
        invoice_number = await InvoiceService._generate_invoice_number(db, InvoiceType.INVOICE)
        print(f"[InvoiceService] Generated invoice number: {invoice_number}")

        # Construiește numele clientului
        client_name = f"{order.client.first_name or ''} {order.client.last_name or ''}".strip()
        if not client_name:
            client_name = f"Client {order.client.id}"

        # Creează factura
        invoice = Invoice(
            order_id=order_id,
            invoice_type=InvoiceType.INVOICE,
            invoice_number=invoice_number,
            client_name=client_name,
            client_email=order.client.email or "",
            client_phone=order.client.phone,
            total_amount=order.total_amount,
            currency=order.currency,
            notes=notes
        )

        db.add(invoice)

        try:
            await db.commit()
            await db.refresh(invoice)
            print(f"[InvoiceService] Invoice saved successfully with ID {invoice.id}")
        except Exception as e:
            print(f"[InvoiceService] ERROR saving invoice: {str(e)}")
            await db.rollback()
            raise
        return invoice

    @staticmethod
    async def cancel_invoice(
            db: AsyncSession,
            invoice_id: int,
            reason: str,
            staff_id: int
    ) -> Invoice:
        """Anulează o factură (nu o șterge!)."""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.is_quote:
            raise ValueError("Use delete for quotes, not cancel")

        if invoice.is_cancelled:
            raise ValueError("Invoice already cancelled")

        # Marchează ca anulată
        invoice.is_cancelled = True
        invoice.cancelled_at = datetime.utcnow()
        invoice.cancellation_reason = reason
        invoice.cancelled_by_id = staff_id

        await db.commit()
        await db.refresh(invoice)

        # TODO: Creează notă de credit automată dacă e necesar

        return invoice


