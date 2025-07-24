# server/dashboard/routers/staff/vendor_staff.py

from __future__ import annotations
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from cfg.depends import get_db
from server.dashboard.dependencies import get_current_staff, check_permission, get_template_context, require_role
from models import Staff, VendorStaff, VendorCompany, VendorRole
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.vendor_staff_service import VendorStaffService
from services.models.vendor_company_service import VendorCompanyService

vendor_staff_router = APIRouter()

templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only



@vendor_staff_router.get("/", response_class=HTMLResponse)
async def list_vendor_staff(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        page: int = 1,
        search: Optional[str] = None,
        company_id: Optional[int] = None,
        vendor_role: Optional[str] = None
):
    """Listează toți angajații vendor."""

    # ADAUGĂ DEBUG PENTRU CONTEXT
    print(f"DEBUG: current_staff = {current_staff}")
    print(f"DEBUG: current_staff.role = {current_staff.role}")



    from sqlalchemy import select, func
    from sqlalchemy.orm import selectinload

    per_page = 20
    skip = (page - 1) * per_page

    # Query pentru staff
    query = select(VendorStaff).options(selectinload(VendorStaff.company))
    count_query = select(func.count(VendorStaff.id))

    # Filtre
    if search:
        query = query.where(
            VendorStaff.first_name.ilike(f"%{search}%") |
            VendorStaff.last_name.ilike(f"%{search}%") |
            VendorStaff.email.ilike(f"%{search}%")
        )
        count_query = count_query.where(
            VendorStaff.first_name.ilike(f"%{search}%") |
            VendorStaff.last_name.ilike(f"%{search}%") |
            VendorStaff.email.ilike(f"%{search}%")
        )

    if company_id:
        query = query.where(VendorStaff.company_id == company_id)
        count_query = count_query.where(VendorStaff.company_id == company_id)

    if vendor_role:
        try:
            role_enum = VendorRole(vendor_role)
            query = query.where(VendorStaff.role == role_enum)
            count_query = count_query.where(VendorStaff.role == role_enum)
        except ValueError:
            pass

    # Execută query-uri
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query
        .order_by(VendorStaff.created_at.desc())
        .offset(skip)
        .limit(per_page)
    )
    staff_list = result.scalars().all()

    # Lista companiilor pentru filtru
    companies_result = await db.execute(
        select(VendorCompany)
        .where(VendorCompany.is_active == True)
        .order_by(VendorCompany.name)
    )
    companies = companies_result.scalars().all()

    # Calcul paginare
    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, current_staff, db)

    # ADAUGĂ DEBUG PENTRU CONTEXT
    print(f"DEBUG: context keys = {list(context.keys())}")
    print(f"DEBUG: dashboard_prefix = {context.get('dashboard_prefix')}")
    print(f"DEBUG: menu_structure = {context.get('menu_structure')}")



    context.update({
        "staff_list": staff_list,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "company_id": company_id,
        "vendor_role": vendor_role,
        "companies": companies,
        "vendor_roles": VendorRole,
        "page_title": "Angajați Vendor",
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_staff/list.html", context)


@vendor_staff_router.get("/create", response_class=HTMLResponse)
async def create_vendor_staff_form(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        company_id: Optional[int] = None
):
    """Formular creare angajat vendor nou."""
    # Lista companiilor active
    from sqlalchemy import select
    companies_result = await db.execute(
        select(VendorCompany)
        .where(VendorCompany.is_active == True)
        .order_by(VendorCompany.name)
    )
    companies = companies_result.scalars().all()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "companies": companies,
        "preselected_company_id": company_id,
        "vendor_roles": VendorRole,
        "page_title": "Adaugă Angajat Vendor"
    })

    return templates.TemplateResponse("vendor_staff/create.html", context)


@vendor_staff_router.post("/create")
async def create_vendor_staff(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        company_id: int = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: Optional[str] = Form(None),
        role: str = Form(...),
        return_to: Optional[str] = Form(None)
):
    """Creează angajat vendor nou."""
    try:
        # Verifică dacă email-ul există deja
        existing = await VendorStaffService.get_by_email(db, email)
        if existing:
            raise ValueError("Email-ul este deja înregistrat")

        # Verifică compania
        company = await VendorCompanyService.get_by_id(db, company_id)
        if not company:
            raise ValueError("Compania selectată nu există")

        # Creează angajatul
        vendor_staff = await VendorStaffService.create(
            db=db,
            company_id=company_id,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=VendorRole(role)
        )

        # LOGICĂ NAVIGARE: Determină unde să ne întoarcem
        if return_to == "company_staff":
            redirect_url = f"/dashboard/staff/vendor_company/{company_id}/staff"
        else:
            redirect_url = f"/dashboard/staff/vendor_staff/{vendor_staff.id}"

        return RedirectResponse(url=redirect_url, status_code=303)

    except Exception as e:
        # Re-încarcă datele pentru formular
        from sqlalchemy import select
        companies_result = await db.execute(
            select(VendorCompany)
            .where(VendorCompany.is_active == True)
            .order_by(VendorCompany.name)
        )
        companies = companies_result.scalars().all()

        context = await get_template_context(request, current_staff, db)
        context.update({
            "error": str(e),
            "companies": companies,
            "vendor_roles": VendorRole,
            "page_title": "Adaugă Angajat Vendor",
            "form_data": {
                "company_id": company_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "role": role
            }
        })

        return templates.TemplateResponse("vendor_staff/create.html", context)


@vendor_staff_router.get("/{staff_id}", response_class=HTMLResponse)
async def view_vendor_staff(
        request: Request,
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        from_company: Optional[int] = None  # parametru de navigare
):
    """Vizualizează detalii angajat vendor."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(VendorStaff)
        .where(VendorStaff.id == staff_id)
        .options(selectinload(VendorStaff.company))
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    # Activitate recentă (produse adăugate/modificate)
    from models import Product
    recent_products_result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))  # EAGER LOAD pentru category
        .where(Product.vendor_company_id == vendor_staff.company_id)
        .order_by(Product.updated_at.desc())
        .limit(10)
    )
    recent_products = recent_products_result.scalars().all()

    # LOGICĂ NAVIGARE: Determină URL-ul de întoarcere
    if from_company:
        back_url = f"/dashboard/staff/vendor_company/{from_company}/staff"
        back_text = f"Înapoi la {vendor_staff.company.name}"
    else:
        # Detectăm automat dacă vine din company staff sau din lista generală
        referer = request.headers.get('referer', '')
        if f"/vendor_company/{vendor_staff.company_id}/staff" in referer:
            back_url = f"/dashboard/staff/vendor_company/{vendor_staff.company_id}/staff"
            back_text = f"Înapoi la {vendor_staff.company.name}"
        else:
            back_url = "/dashboard/staff/vendor_staff/"
            back_text = "Înapoi la Lista Generală"

    context = await get_template_context(request, current_staff, db)
    context.update({
        "vendor_staff": vendor_staff,
        "recent_products": recent_products,
        "page_title": vendor_staff.full_name,
        "current_staff": current_staff,
        "back_url": back_url,  # ADĂUGAT
        "back_text": back_text  # ADĂUGAT
    })

    return templates.TemplateResponse("vendor_staff/view.html", context)


@vendor_staff_router.get("/{staff_id}/edit", response_class=HTMLResponse)
async def edit_vendor_staff_form(
        request: Request,
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"]))
):
    """Formular editare angajat vendor."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(VendorStaff)
        .where(VendorStaff.id == staff_id)
        .options(selectinload(VendorStaff.company))
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    # Lista companiilor pentru schimbare
    companies_result = await db.execute(
        select(VendorCompany)
        .where(VendorCompany.is_active == True)
        .order_by(VendorCompany.name)
    )
    companies = companies_result.scalars().all()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "vendor_staff": vendor_staff,
        "companies": companies,
        "vendor_roles": VendorRole,
        "page_title": f"Editează {vendor_staff.full_name}"
    })

    return templates.TemplateResponse("vendor_staff/edit.html", context)


@vendor_staff_router.post("/{staff_id}/edit")
async def edit_vendor_staff(
        request: Request,
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        company_id: int = Form(...),
        email: str = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: Optional[str] = Form(None),
        role: str = Form(...)
):
    """Actualizează date angajat vendor."""
    from sqlalchemy import select

    result = await db.execute(
        select(VendorStaff).where(VendorStaff.id == staff_id)
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    # Verifică dacă email-ul nou există la alt utilizator
    if vendor_staff.email != email:
        existing = await VendorStaffService.get_by_email(db, email)
        if existing and existing.id != staff_id:
            raise HTTPException(status_code=400, detail="Email-ul este deja folosit")

    # Actualizează datele
    vendor_staff.company_id = company_id
    vendor_staff.email = email
    vendor_staff.first_name = first_name
    vendor_staff.last_name = last_name
    vendor_staff.phone = phone
    vendor_staff.role = VendorRole(role)

    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_staff/{staff_id}",
        status_code=303
    )


@vendor_staff_router.post("/{staff_id}/reset-password")
async def reset_vendor_staff_password(
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        new_password: str = Form(...)
):
    """Resetează parola angajatului vendor."""
    from sqlalchemy import select
    import bcrypt

    result = await db.execute(
        select(VendorStaff).where(VendorStaff.id == staff_id)
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    # Hash new password
    vendor_staff.password_hash = bcrypt.hashpw(
        new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_staff/{staff_id}",
        status_code=303
    )


@vendor_staff_router.post("/{staff_id}/toggle-status")
async def toggle_vendor_staff_status(
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"]))
):
    """Activează/Dezactivează angajat vendor."""
    from sqlalchemy import select

    result = await db.execute(
        select(VendorStaff).where(VendorStaff.id == staff_id)
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    vendor_staff.is_active = not vendor_staff.is_active
    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_staff/{staff_id}",
        status_code=303
    )


@vendor_staff_router.post("/{staff_id}/delete")
async def delete_vendor_staff(
        staff_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["super_admin"]))
):
    """Șterge permanent angajat vendor."""
    from sqlalchemy import select

    result = await db.execute(
        select(VendorStaff).where(VendorStaff.id == staff_id)
    )
    vendor_staff = result.scalar_one_or_none()

    if not vendor_staff:
        raise HTTPException(status_code=404, detail="Angajatul nu a fost găsit")

    await db.delete(vendor_staff)
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/vendor_staff/",
        status_code=303
    )




