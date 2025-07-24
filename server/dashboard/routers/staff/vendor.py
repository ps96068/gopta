# server/dashboard/routers/vendor.py
"""
Router pentru gestionarea vendorilor în dashboard.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Vendor, Product
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.vendor_services import VendorService

vendor_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf/vendor")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@vendor_router.get("/", response_class=HTMLResponse)
async def vendor_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        is_active: Optional[str] = None,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă vendori cu filtre și paginare."""

    # Query de bază
    query = select(Vendor)

    # Filtre
    filters = []

    if search:
        filters.append(
            or_(
                Vendor.name.ilike(f"%{search}%"),
                Vendor.email.ilike(f"%{search}%"),
                Vendor.phone.ilike(f"%{search}%")
            )
        )

    if is_active is not None:
        if is_active == "true":
            filters.append(Vendor.is_active == True)
        elif is_active == "false":
            filters.append(Vendor.is_active == False)

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count()).select_from(Vendor)
    if filters:
        total_query = total_query.where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare și paginare
    offset = (page - 1) * per_page
    query = query.order_by(Vendor.name).offset(offset).limit(per_page)

    result = await db.execute(query)
    vendors = result.scalars().all()

    # Count products pentru fiecare vendor
    vendor_products = {}
    for vendor in vendors:
        products_count = await db.execute(
            select(func.count(Product.id)).where(Product.vendor_id == vendor.id)
        )
        vendor_products[vendor.id] = products_count.scalar() or 0

    # Stats
    total_vendors = await db.execute(
        select(func.count(Vendor.id))
    )
    total_count = total_vendors.scalar() or 0

    active_vendors = await db.execute(
        select(func.count(Vendor.id)).where(Vendor.is_active == True)
    )
    active_count = active_vendors.scalar() or 0

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Furnizori",
        "vendors": vendors,
        "vendor_products": vendor_products,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "total_vendors": total_count,
        "active_vendors": active_count,
        "inactive_vendors": total_count - active_count,
        "search_query": search,
        "is_active_filter": is_active
    })

    return templates.TemplateResponse("vendor/list.html", context)


@vendor_router.get("/create", response_class=HTMLResponse)
async def vendor_create_form(
        request: Request,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "vendor")),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare vendor nou."""

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Furnizor Nou"
    })

    return templates.TemplateResponse("vendor/form.html", context)


@vendor_router.post("/create")
async def vendor_create(
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        contact_person: Optional[str] = Form(None),
        address: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "vendor")),
        db: AsyncSession = Depends(get_db)
):
    """Creează vendor nou."""

    try:
        # Verifică email unic
        existing = await VendorService.get_by_email(db, email)
        if existing:
            return RedirectResponse(
                url="/dashboard/vendor/create?error=email_exists",
                status_code=303
            )

        # Creează vendor
        vendor = await VendorService.create(
            db=db,
            name=name,
            email=email,
            phone=phone,
            contact_person=contact_person,
            address=address,
            description=description
        )

        return RedirectResponse(
            url=f"/dashboard/vendor?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating vendor: {e}")
        return RedirectResponse(
            url="/dashboard/vendor/create?error=create_failed",
            status_code=303
        )


@vendor_router.get("/{vendor_id}", response_class=HTMLResponse)
async def vendor_detail(
        request: Request,
        vendor_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii vendor cu produse."""

    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")

    # Get products count
    products_count = await db.execute(
        select(func.count(Product.id)).where(Product.vendor_id == vendor_id)
    )
    total_products = products_count.scalar() or 0

    # Get recent products
    products_result = await db.execute(
        select(Product)
        .where(Product.vendor_id == vendor_id)
        .options(selectinload(Product.category))
        .order_by(Product.created_at.desc())
        .limit(10)
    )
    recent_products = products_result.scalars().all()

    # Stats
    active_products = await db.execute(
        select(func.count(Product.id))
        .where(
            and_(
                Product.vendor_id == vendor_id,
                Product.is_active == True
            )
        )
    )
    active_count = active_products.scalar() or 0

    context = await get_template_context(request, staff)
    context.update({
        "page_title": vendor.name,
        "vendor": vendor,
        "total_products": total_products,
        "active_products": active_count,
        "recent_products": recent_products
    })

    return templates.TemplateResponse("vendor/detail.html", context)


@vendor_router.get("/{vendor_id}/edit", response_class=HTMLResponse)
async def vendor_edit_form(
        request: Request,
        vendor_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "vendor")),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare vendor."""

    vendor = await VendorService.get_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Furnizor negăsit")

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Editare: {vendor.name}",
        "vendor": vendor
    })

    return templates.TemplateResponse("vendor/form.html", context)


@vendor_router.post("/{vendor_id}/edit")
async def vendor_edit(
        vendor_id: int,
        name: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        contact_person: Optional[str] = Form(None),
        address: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "vendor")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează vendor."""

    try:
        vendor = await VendorService.get_by_id(db, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404)

        # Verifică email unic
        if vendor.email != email:
            existing = await VendorService.get_by_email(db, email)
            if existing:
                return RedirectResponse(
                    url=f"/dashboard/vendor/{vendor_id}/edit?error=email_exists",
                    status_code=303
                )

        # Actualizează
        vendor.name = name
        vendor.email = email
        vendor.phone = phone
        vendor.contact_person = contact_person
        vendor.address = address
        vendor.description = description

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/vendor/{vendor_id}?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating vendor: {e}")
        return RedirectResponse(
            url=f"/dashboard/vendor/{vendor_id}/edit?error=update_failed",
            status_code=303
        )


@vendor_router.post("/{vendor_id}/toggle-active")
async def toggle_vendor_active(
        vendor_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "vendor")),
        db: AsyncSession = Depends(get_db)
):
    """Toggle active status vendor."""

    vendor = await VendorService.get_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404)

    vendor.is_active = not vendor.is_active
    await db.commit()

    return RedirectResponse(
        url="/dashboard/vendor?success=status_toggled",
        status_code=303
    )