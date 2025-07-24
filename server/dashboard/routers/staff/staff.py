# server/dashboard/routers/staff.py (nou)
"""
Router pentru gestionarea staff-ului.
"""

from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from cfg import get_db
from models import Staff, StaffRole
from server.dashboard.dependencies import get_current_staff, get_template_context, require_role, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models import StaffService

staff_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@staff_router.get("/", response_class=HTMLResponse)
async def staff_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        role: Optional[str] = None,
        is_active: Optional[str] = None,
        search: Optional[str] = None,
        current_staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă membri staff."""

    # Query de bază
    query = select(Staff)

    # Filtre
    filters = []

    if role and role != "all":
        filters.append(Staff.role == StaffRole(role))

    if is_active is not None:
        if is_active == "true":
            filters.append(Staff.is_active == True)
        elif is_active == "false":
            filters.append(Staff.is_active == False)

    if search:
        search_filter = or_(
            Staff.first_name.ilike(f"%{search}%"),
            Staff.last_name.ilike(f"%{search}%"),
            Staff.email.ilike(f"%{search}%")
        )
        filters.append(search_filter)

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count()).select_from(Staff)
    if filters:
        total_query = total_query.where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(Staff.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    staff_members = result.scalars().all()

    # Statistici pe roluri
    role_stats = await StaffService.count_by_role(db)

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, current_staff)
    context.update({
        "page_title": "Staff",
        "staff_members": staff_members,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "role_filter": role,
        "is_active_filter": is_active,
        "search_query": search,
        "staff_roles": [(r.value, r.value.replace('_', ' ').title()) for r in StaffRole],
        "role_stats": role_stats,
        "current_staff": current_staff
    })

    return templates.TemplateResponse("staff/list.html", context)


@staff_router.get("/create", response_class=HTMLResponse)
async def staff_create_form(
        request: Request,
        current_staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "staff")),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare staff nou."""
    context = await get_template_context(request, current_staff)
    context.update({
        "page_title": "Client Nou",
        "staff_roles": [(r.value, r.value.replace('_', ' ').title()) for r in StaffRole],
        "staff": None
    })

    return templates.TemplateResponse("staff/form.html", context)

@staff_router.post("/create")
async def staff_create(
        email: str = Form(...),
        password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: Optional[str] = Form(None),
        role: str = Form(...),
        can_manage_clients: bool = Form(False),
        can_manage_products: bool = Form(False),
        can_manage_orders: bool = Form(False),
        current_staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "staff")),
        db: AsyncSession = Depends(get_db)
):
    """Creează staff nou."""

    try:
        # Verifică dacă email există
        existing = await StaffService.get_by_email(db, email)
        if existing:
            return RedirectResponse(
                url="/dashboard/staff/staff/create?error=email_exists",
                status_code=303
            )

        # Creează staff
        new_staff = await StaffService.create(
            db=db,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=StaffRole(role)
        )

        # Setează permisiuni pentru Manager
        if new_staff.role == StaffRole.MANAGER:
            new_staff.can_manage_clients = can_manage_clients
            new_staff.can_manage_products = can_manage_products
            new_staff.can_manage_orders = can_manage_orders
            await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/staff?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating staff: {e}")
        return RedirectResponse(
            url="/dashboard/staff/staff/create?error=create_failed",
            status_code=303
        )

@staff_router.get("/{staff_id}", response_class=HTMLResponse)
async def staff_detail(
        request: Request,
        staff_id: int,
        current_staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii membru staff."""

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id)
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    context = await get_template_context(request, current_staff)
    context.update({
        "page_title": f"{staff.first_name} {staff.last_name}",
        "staff": staff,
        "current_staff": current_staff
    })

    return templates.TemplateResponse("staff/detail.html", context)


@staff_router.get("/{staff_id}/edit", response_class=HTMLResponse)
async def staff_edit_form(
        request: Request,
        staff_id: int,
        current_staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "staff")),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare staff."""

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id)
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    context = await get_template_context(request, current_staff)
    context.update({
        "page_title": f"Editare: {staff.first_name} {staff.last_name}",
        "staff": staff,
        "staff_roles": [(r.value, r.value.replace('_', ' ').title()) for r in StaffRole]
    })

    return templates.TemplateResponse("staff/form.html", context)


@staff_router.post("/{staff_id}/edit")
async def staff_edit(
        staff_id: int,
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: Optional[str] = Form(None),
        role: str = Form(...),
        can_manage_clients: bool = Form(False),
        can_manage_products: bool = Form(False),
        can_manage_orders: bool = Form(False),
        current_staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "staff")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează date staff."""

    try:
        # Update basic info
        updated = await StaffService.update(
            db=db,
            staff_id=staff_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )

        if not updated:
            raise HTTPException(status_code=404)

        # Update role if changed
        if updated.role.value != role:
            await StaffService.update_role(db, staff_id, StaffRole(role))

        # Update permissions for Manager
        if updated.role == StaffRole.MANAGER:
            updated.can_manage_clients = can_manage_clients
            updated.can_manage_products = can_manage_products
            updated.can_manage_orders = can_manage_orders
            await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/staff/{staff_id}?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating staff: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/staff/{staff_id}/edit?error=update_failed",
            status_code=303
        )


@staff_router.post("/{staff_id}/toggle-active")
async def toggle_staff_active(
        staff_id: int,
        current_staff=Depends(get_current_staff),
        _=Depends(require_role(["super_admin"])),
        db: AsyncSession = Depends(get_db)
):
    """Toggle active status staff."""

    if staff_id == current_staff.id:
        return RedirectResponse(
            url=f"/dashboard/staff/staff/{staff_id}?error=cannot_deactivate_self",
            status_code=303
        )

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id)
    )
    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404)

    if staff.is_active:
        await StaffService.deactivate(db, staff_id)
    else:
        await StaffService.activate(db, staff_id)

    return RedirectResponse(
        url=f"/dashboard/staff/staff?success=status_toggled",
        status_code=303
    )


@staff_router.get("/{staff_id}/permissions", response_class=HTMLResponse)
async def staff_permissions(
        request: Request,
        staff_id: int,
        current_staff=Depends(get_current_staff),
        _=Depends(require_role(["super_admin"])),  # Doar super_admin
        db: AsyncSession = Depends(get_db)
):
    """Pagină gestionare permisiuni pentru un Manager."""

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id)
    )
    staff = result.scalar_one_or_none()

    if not staff or staff.role != StaffRole.MANAGER:
        raise HTTPException(status_code=404, detail="Manager negăsit")

    context = await get_template_context(request, current_staff)
    context.update({
        "page_title": f"Permisiuni: {staff.first_name} {staff.last_name}",
        "staff": staff
    })

    return templates.TemplateResponse("staff/permissions.html", context)


@staff_router.post("/{staff_id}/permissions")
async def update_staff_permissions(
        request: Request,
        staff_id: int,
        can_manage_clients: bool = Form(False),
        can_manage_products: bool = Form(False),
        can_manage_orders: bool = Form(False),
        current_staff=Depends(get_current_staff),
        _=Depends(require_role(["super_admin"])),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează permisiunile unui Manager."""

    result = await db.execute(
        select(Staff).where(Staff.id == staff_id)
    )
    staff = result.scalar_one_or_none()

    if not staff or staff.role != StaffRole.MANAGER:
        raise HTTPException(status_code=404)

    # Actualizează permisiuni
    staff.can_manage_clients = can_manage_clients
    staff.can_manage_products = can_manage_products
    staff.can_manage_orders = can_manage_orders

    await db.commit()

    return RedirectResponse(
        # url=f"/dashboard/staff/{staff_id}/permissions?success=updated",
        url=str(request.url_for("staff_permissions", staff_id=staff_id)) + "?success=updated",
        status_code=303
    )