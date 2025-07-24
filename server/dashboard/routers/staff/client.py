# server/dashboard/routers/client.py
"""
Router pentru gestionarea clienților în dashboard.
"""
from __future__ import annotations

import pprint
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Client, UserStatus, Order, UserRequest, OrderStatus
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.client_services import ClientService

client_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

# Registrăm filtrele
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@client_router.get("/", response_class=HTMLResponse)
async def client_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        status: Optional[str] = None,
        search: Optional[str] = None,
        show_inactive: bool = Query(False),
        sort_by: str = "created_at",
        sort_desc: bool = True,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă clienți cu filtre și paginare."""

    # Query de bază
    # query = select(Client).where(Client.is_active == True)
    query = select(Client)

    # Query de bază - INCLUDE clienți inactivi dacă se cere
    # if show_inactive:
    #     query = select(Client)  # TOȚI clienții
    #     print("🔍 Afișez TOȚI clienții (inclusiv inactivi)")
    # else:
    #     query = select(Client).where(Client.is_active == True)  # Doar activi
    #     print("🔍 Afișez doar clienții activi")



    # Filtre
    if status and status != "all":
        query = query.where(Client.status == UserStatus(status))

    if search:
        search_filter = or_(
            Client.first_name.ilike(f"%{search}%"),
            Client.last_name.ilike(f"%{search}%"),
            Client.email.ilike(f"%{search}%"),
            Client.phone.ilike(f"%{search}%"),
            Client.username.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    # Total pentru paginare
    if show_inactive:
        total_query = select(func.count()).select_from(Client)
    else:
        total_query = select(func.count()).select_from(Client).where(Client.is_active == True)

    if status and status != "all":
        total_query = total_query.where(Client.status == UserStatus(status))
    if search:
        total_query = total_query.where(search_filter)

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare
    if sort_by == "name":
        order_by = Client.first_name
    elif sort_by == "status":
        order_by = Client.status
    elif sort_by == "created_at":
        order_by = Client.created_at
    else:
        order_by = Client.created_at

    if sort_desc:
        order_by = order_by.desc()

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(order_by).offset(offset).limit(per_page)

    result = await db.execute(query)
    clients = result.scalars().all()

    # Statistici pentru fiecare client
    client_stats = {}
    for client in clients:
        # Count orders
        orders_count = await db.execute(
            select(func.count(Order.id)).where(Order.client_id == client.id)
        )
        # Count requests
        requests_count = await db.execute(
            select(func.count(UserRequest.id)).where(UserRequest.client_id == client.id)
        )

        client_stats[client.id] = {
            "orders": orders_count.scalar() or 0,
            "requests": requests_count.scalar() or 0
        }

    # Stats pentru cards
    stats = {
        "total": total,
        "anonim": 0,
        "user": 0,
        "instalator": 0,
        "pro": 0
    }

    # Count by status
    status_counts = await db.execute(
        select(Client.status, func.count(Client.id))
        .where(Client.is_active == True)
        .group_by(Client.status)
    )

    for status_row, count in status_counts:
        stats[status_row.value] = count

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Clienți",
        "clients": clients,
        "client_stats": client_stats,
        "stats": stats,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "status_filter": status,
        "search_query": search,
        "show_inactive": show_inactive,
        "sort_by": sort_by,
        "sort_desc": sort_desc,
        "user_statuses": [(s.value, s.value.title()) for s in UserStatus]
    })

    return templates.TemplateResponse("client/list.html", context)



@client_router.get("/create", response_class=HTMLResponse)
async def client_create_form(
        request: Request,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare client nou."""

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Client Nou",
        "user_statuses": [(s.value, s.value.title()) for s in UserStatus]
    })

    return templates.TemplateResponse("client/form.html", context)


@client_router.post("/create")
async def client_create(
        telegram_id: int = Form(...),
        first_name: Optional[str] = Form(None),
        last_name: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        username: Optional[str] = Form(None),
        status: str = Form(...),
        language_code: str = Form("ro"),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Creează client nou."""

    try:
        # Verifică dacă telegram_id există deja
        existing = await db.execute(
            select(Client).where(Client.telegram_id == telegram_id)
        )
        if existing.scalar_one_or_none():
            return RedirectResponse(
                url="/dashboard/staff/client/create?error=telegram_id_exists",
                status_code=303
            )

        # Creează client
        client = Client(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            username=username,
            status=UserStatus(status),
            language_code=language_code
        )

        db.add(client)
        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/client?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating client: {e}")
        return RedirectResponse(
            url="/dashboard/staff/client/create?error=create_failed",
            status_code=303
        )




@client_router.get("/{client_id}", response_class=HTMLResponse)
async def client_detail(
        request: Request,
        client_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii client cu istoric complet."""

    # Get client
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client negăsit")

    # Get recent orders
    orders_result = await db.execute(
        select(Order)
        .where(Order.client_id == client_id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent_orders = orders_result.scalars().all()

    # Get recent requests
    requests_result = await db.execute(
        select(UserRequest)
        .where(UserRequest.client_id == client_id)
        .options(selectinload(UserRequest.product))
        .order_by(UserRequest.created_at.desc())
        .limit(5)
    )
    recent_requests = requests_result.scalars().all()

    # Statistics
    total_orders = await db.execute(
        select(func.count(Order.id)).where(Order.client_id == client_id)
    )

    total_spent = await db.execute(
        select(func.sum(Order.total_amount))
        .where(
            and_(
                Order.client_id == client_id,
                # Order.status.in_(["processing", "completed"])
                Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED])
            )
        )
    )

    total_requests = await db.execute(
        select(func.count(UserRequest.id)).where(UserRequest.client_id == client_id)
    )

    stats = {
        "orders": total_orders.scalar() or 0,
        "spent": float(total_spent.scalar() or 0),
        "requests": total_requests.scalar() or 0
    }

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Client: {client.first_name or 'Anonim'} {client.last_name or ''}",
        "client": client,
        "recent_orders": recent_orders,
        "recent_requests": recent_requests,
        "stats": stats,
        "current_staff": staff
    })

    return templates.TemplateResponse("client/detail.html", context)




@client_router.get("/{client_id}/edit", response_class=HTMLResponse)
async def client_edit_form(
        request: Request,
        client_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare client."""

    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client negăsit")

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Editare: {client.first_name or 'Client'} {client.last_name or ''}",
        "client": client,
        "user_statuses": [(s.value, s.value.title()) for s in UserStatus]
    })

    return templates.TemplateResponse("client/form.html", context)


@client_router.post("/{client_id}/edit")
async def client_edit(
        request: Request,
        client_id: int,
        telegram_id: int = Form(...),
        first_name: Optional[str] = Form(None),
        last_name: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        username: Optional[str] = Form(None),
        status: str = Form(...),
        language_code: str = Form("ro"),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează date client."""

    try:
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            raise HTTPException(status_code=404)

        # Verifică dacă telegram_id nou există la alt client
        if client.telegram_id != telegram_id:
            existing = await db.execute(
                select(Client).where(
                    and_(
                        Client.telegram_id == telegram_id,
                        Client.id != client_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                return RedirectResponse(
                    url=f"/dashboard/staff/client/{client_id}/edit?error=telegram_id_exists",
                    status_code=303
                )

        # Actualizează date
        client.telegram_id = telegram_id
        client.username = username
        client.first_name = first_name
        client.last_name = last_name
        client.language_code = language_code
        if client.status != UserStatus(status):
            # Dacă statusul s-a schimbat, actualizează și în baza de date
            client.email = email or None
            client.phone = phone or None

        client.status = UserStatus(status)

        # Tratează email și phone - convertește string gol în None
        client.email = email.strip() if email and email.strip() else None
        client.phone = phone.strip() if phone and phone.strip() else None



        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/client/{client_id}?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating client: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/client/{client_id}/edit?error=update_failed",
            status_code=303
        )





@client_router.post("/{client_id}/update-status")
async def update_client_status(
        request: Request,  # Adaugă request pentru a obține referer
        client_id: int,
        new_status: str = Form(...),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează status client (doar manager+)."""

    try:
        status = UserStatus(new_status)

        pprint.pprint(f"+++++++++++ ststaus: {status}")

        # Update status
        await ClientService.update_status(db, client_id, status)

        # Redirect înapoi la pagina de unde a venit (lista sau detalii)
        referer = request.headers.get("referer", f"/dashboard/staff/client")

        # Dacă vine din lista de clienți, rămâne acolo
        if "/dashboard/staff/client" in referer and f"/dashboard/staff/client/{client_id}" not in referer:
            return RedirectResponse(
                url=f"/dashboard/staff/client?success=status_updated",
                status_code=303
            )

        # Altfel, merge la detalii
        return RedirectResponse(
            url=f"/dashboard/staff/client/{client_id}?success=status_updated",
            status_code=303
        )

    except ValueError:
        referer = request.headers.get("referer", f"/dashboard/staff/client")
        return RedirectResponse(
            url=f"{referer}?error=invalid_status",
            status_code=303
        )
    except Exception:
        referer = request.headers.get("referer", f"/dashboard/staff/client")
        return RedirectResponse(
            url=f"{referer}?error=update_failed",
            status_code=303
        )



@client_router.post("/{client_id}/toggle-active")
async def toggle_client_active(
        client_id: int,
        staff=Depends(get_current_staff),
        # _=Depends(PermissionChecker("update", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Toggle active status client - DOAR super_admin."""

    # VERIFICARE CRITICĂ: Doar super_admin poate dezactiva clienți
    if staff.role.value != 'super_admin':
        print(f"🚫 ACCES REFUZAT: {staff.email} ({staff.role.value}) a încercat să dezactiveze clientul {client_id}")
        raise HTTPException(
            status_code=403,
            detail="Doar Super Administrator poate activa/dezactiva clienți"
        )

    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404)

    old_status = "ACTIV" if client.is_active else "INACTIV"
    client.is_active = not client.is_active
    new_status = "ACTIV" if client.is_active else "INACTIV"

    await db.commit()

    # Log pentru audit
    print(f"✅ AUDIT: Super Admin {staff.email} a schimbat statusul clientului {client.first_name} {client.last_name} (ID: {client_id}): {old_status} → {new_status}")

    return RedirectResponse(
        url=f"/dashboard/staff/client?success=status_toggled",
        status_code=303
    )





@client_router.post("/{client_id}/delete")
async def client_delete(
        client_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "client")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge client (soft delete)."""

    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404)

    # Soft delete
    client.is_active = False
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/client?success=deleted",
        status_code=303
    )



