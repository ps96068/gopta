# server/dashboard/routers/user_request.py
from __future__ import annotations
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Query, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import UserRequest, RequestType, Client, Product, Staff, RequestResponse
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.request_services import RequestService

user_request_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

# Registrăm filtrele pentru templates
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@user_request_router.get("/", response_class=HTMLResponse)
async def user_request_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        request_type: Optional[str] = None,
        is_processed: Optional[str] = None,
        search: Optional[str] = None,
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă cereri utilizatori cu filtre."""

    # Query de bază
    query = select(UserRequest).options(
        selectinload(UserRequest.client),
        selectinload(UserRequest.product),
        selectinload(UserRequest.responses)
    )

    # Filtre
    filters = []

    if request_type and request_type != "all":
        filters.append(UserRequest.request_type == RequestType(request_type))

    if is_processed is not None:
        if is_processed == "true":
            filters.append(UserRequest.is_processed == True)
        elif is_processed == "false":
            filters.append(UserRequest.is_processed == False)

    if search:
        filters.append(
            or_(
                UserRequest.message.ilike(f"%{search}%"),
                Client.first_name.ilike(f"%{search}%"),
                Client.last_name.ilike(f"%{search}%")
            )
        )

    if filters:
        query = query.join(Client).where(and_(*filters))
    else:
        query = query.join(Client)

    # Total pentru paginare
    total_query = select(func.count()).select_from(UserRequest)
    if filters:
        total_query = total_query.join(Client).where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(UserRequest.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    requests = result.scalars().all()

    # Calculăm total pages
    total_pages = (total + per_page - 1) // per_page

    # Context pentru template
    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Cereri Utilizatori",
        "requests": requests,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "request_type_filter": request_type,
        "is_processed_filter": is_processed,
        "search_query": search,
        "request_types": [(rt.value, rt.value.title()) for rt in RequestType]
    })

    return templates.TemplateResponse("user_request/list.html", context)


@user_request_router.get("/{request_id}", response_class=HTMLResponse)
async def user_request_detail(
        request: Request,
        request_id: int,
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii cerere cu posibilitate de răspuns."""

    # Obține cererea cu toate relațiile
    result = await db.execute(
        select(UserRequest)
        .where(UserRequest.id == request_id)
        .options(
            selectinload(UserRequest.client),
            selectinload(UserRequest.product).selectinload(Product.category),
            selectinload(UserRequest.cart),
            selectinload(UserRequest.responses).selectinload(RequestResponse.staff)
        )
    )
    user_request = result.scalar_one_or_none()

    if not user_request:
        raise HTTPException(status_code=404, detail="Cerere negăsită")

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Cerere #{user_request.id}",
        "user_request": user_request
    })

    return templates.TemplateResponse("user_request/detail.html", context)


@user_request_router.post("/{request_id}/respond")
async def respond_to_request(
        request_id: int,
        message: str = Form(...),
        sent_via: str = Form("telegram"),
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Adaugă răspuns la cerere."""

    try:
        # Adaugă răspunsul
        response = await RequestService.add_response(
            db=db,
            request_id=request_id,
            staff_id=staff.id,
            message=message,
            sent_via=sent_via
        )

        # TODO: Trimite notificare la client prin Telegram

        return RedirectResponse(
            url=f"/dashboard/staff/user_request/{request_id}?success=response_sent",
            status_code=303
        )

    except Exception as e:
        return RedirectResponse(
            url=f"/dashboard/staff/user_request/{request_id}?error=response_failed",
            status_code=303
        )


@user_request_router.post("/{request_id}/toggle-processed")
async def toggle_processed(
        request_id: int,
        staff: Staff = Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Toggle status procesare."""

    result = await db.execute(
        select(UserRequest).where(UserRequest.id == request_id)
    )
    user_request = result.scalar_one_or_none()

    if not user_request:
        raise HTTPException(status_code=404)

    user_request.is_processed = not user_request.is_processed
    if user_request.is_processed:
        user_request.processed_at = datetime.utcnow()
    else:
        user_request.processed_at = None

    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/user_request?success=status_updated",
        status_code=303
    )