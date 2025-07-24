# server/dashboard/routers/staff/vendor_company.py

from __future__ import annotations
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import selectinload

from sqlalchemy import func

from cfg.depends import get_db
from server.dashboard.dependencies import get_current_staff, check_permission, get_template_context, require_role
from models import Staff, VendorCompany, StaffRole, VendorStaff
from services.models.vendor_company_service import VendorCompanyService
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.vendor_staff_service import VendorStaffService

vendor_company_router = APIRouter()

templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@vendor_company_router.get("/", response_class=HTMLResponse)
async def list_companies(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        page: int = 1,
        search: Optional[str] = None,
        is_verified: Optional[bool] = None
):
    """Listează toate companiile vendor."""
    per_page = 20
    skip = (page - 1) * per_page

    # Query pentru companii
    from sqlalchemy import select, func
    query = select(VendorCompany)
    count_query = select(func.count(VendorCompany.id))

    # Filtre
    if search:
        query = query.where(
            VendorCompany.name.ilike(f"%{search}%") |
            VendorCompany.legal_name.ilike(f"%{search}%") |
            VendorCompany.tax_id.ilike(f"%{search}%")
        )
        count_query = count_query.where(
            VendorCompany.name.ilike(f"%{search}%") |
            VendorCompany.legal_name.ilike(f"%{search}%") |
            VendorCompany.tax_id.ilike(f"%{search}%")
        )

    if is_verified is not None:
        query = query.where(VendorCompany.is_verified == is_verified)
        count_query = count_query.where(VendorCompany.is_verified == is_verified)

    # Execută query-uri
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query
        .order_by(VendorCompany.created_at.desc())
        .offset(skip)
        .limit(per_page)
    )
    companies = result.scalars().all()

    # Statistici pentru fiecare companie
    companies_with_stats = []
    for company in companies:
        stats = await VendorCompanyService.get_statistics(db, company.id)

        # Număr angajați
        from sqlalchemy import select, func
        from models import VendorStaff
        staff_count_result = await db.execute(
            select(func.count()).select_from(select(VendorStaff).where(
                VendorStaff.company_id == company.id,
                VendorStaff.is_active == True
            ).subquery())
        )
        staff_count = staff_count_result.scalar() or 0

        companies_with_stats.append({
            'company': company,
            'stats': stats,
            'staff_count': staff_count
        })

    # Calcul paginare
    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, current_staff, db)
    # current_staff = context.get('staff', current_staff)
    context.update({
        "companies": companies_with_stats,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search,
        "is_verified": is_verified,
        "page_title": "Companii Vendor",
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_company/list.html", context)


@vendor_company_router.get("/create", response_class=HTMLResponse)
async def create_company_form(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"]))
):
    """Formular creare companie nouă."""
    context = await get_template_context(request, current_staff, db)
    context.update({
        "page_title": "Adaugă Companie Vendor"
    })

    return templates.TemplateResponse("vendor_company/create.html", context)


@vendor_company_router.post("/create")
async def create_company(
        request: Request,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        name: str = Form(...),
        legal_name: str = Form(...),
        tax_id: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        address: str = Form(...),
        bank_account: Optional[str] = Form(None),
        bank_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        website: Optional[str] = Form(None),
        commission_rate: float = Form(15.0),
        payment_terms_days: int = Form(30)
):
    """Creează companie nouă."""
    try:

        # LOGICA SPECIALĂ: Manager creează compania ca INACTIVĂ
        is_active = True
        if current_staff.role == StaffRole.MANAGER:
            is_active = False
            print(f"🔶 Manager {current_staff.email} a creat compania {name} ca INACTIVĂ")

        company = await VendorCompanyService.create(
            db=db,
            name=name,
            legal_name=legal_name,
            tax_id=tax_id,
            email=email,
            phone=phone,
            address=address,
            bank_account=bank_account,
            bank_name=bank_name,
            description=description,
            website=website,
            commission_rate=Decimal(str(commission_rate)),
            payment_terms_days=payment_terms_days,
            is_active=is_active
        )

        return RedirectResponse(
            url=f"/dashboard/staff/vendor_company/{company.id}",
            status_code=303
        )
    except Exception as e:
        context = await get_template_context(request, current_staff, db)
        context.update({
            "page_title": "Adaugă Companie Vendor",
            "error": str(e),
            "form_data": {
                "name": name,
                "legal_name": legal_name,
                "tax_id": tax_id,
                "email": email,
                "phone": phone,
                "address": address,
                "bank_account": bank_account,
                "bank_name": bank_name,
                "description": description,
                "website": website,
                "commission_rate": commission_rate,
                "payment_terms_days": payment_terms_days
            }
        })

        return templates.TemplateResponse("vendor_company/create.html", context)



@vendor_company_router.get("/{company_id}", response_class=HTMLResponse)
async def view_company(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff)
):
    """Vizualizează detalii companie."""
    company = await VendorCompanyService.get_by_id(db, company_id, include_staff=True)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Statistici
    stats = await VendorCompanyService.get_statistics(db, company_id)

    # Produse recente
    from sqlalchemy import select
    from models import Product
    from sqlalchemy.orm import selectinload
    recent_products_result = await db.execute(
        select(Product)
        .options(selectinload(Product.category))  # EAGER LOAD pentru category
        .where(Product.vendor_company_id == company_id)
        .order_by(Product.created_at.desc())
        .limit(5)
    )
    recent_products = recent_products_result.scalars().all()

    # Comenzi recente
    from models import Order, OrderItem
    from sqlalchemy.orm import selectinload
    recent_orders_result = await db.execute(
        select(Order)
        .join(OrderItem)
        .where(OrderItem.vendor_company_id == company_id)
        .distinct()
        .options(selectinload(Order.client))
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent_orders = recent_orders_result.scalars().all()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "stats": stats,
        "recent_products": recent_products,
        "recent_orders": recent_orders,
        "page_title": company.name,
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_company/view.html", context)


@vendor_company_router.get("/{company_id}/products", response_class=HTMLResponse)
async def company_products(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        page: int = 1
):
    """Listează produsele companiei."""
    from sqlalchemy import select, func
    from models import Product

    per_page = 20
    skip = (page - 1) * per_page

    # Verifică compania
    company = await VendorCompanyService.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Query produse
    total_result = await db.execute(
        select(func.count(Product.id))
        .where(Product.vendor_company_id == company_id)
    )
    total = total_result.scalar()

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),  # EAGER LOAD pentru category
            selectinload(Product.prices)     # EAGER LOAD pentru prices
        )
        .where(Product.vendor_company_id == company_id)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(per_page)
    )
    products = result.scalars().all()

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "products": products,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "page_title": f"Produse {company.name}",
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_company/products.html", context)



@vendor_company_router.get("/{company_id}/edit", response_class=HTMLResponse)
async def edit_company_form(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"]))
):
    """Formular editare companie."""
    company = await VendorCompanyService.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "page_title": f"Editează {company.name}"
    })

    return templates.TemplateResponse("vendor_company/edit.html", context)


@vendor_company_router.post("/{company_id}/edit")
async def edit_company(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"])),
        name: str = Form(...),
        legal_name: str = Form(...),
        tax_id: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        address: str = Form(...),
        bank_account: Optional[str] = Form(None),
        bank_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        website: Optional[str] = Form(None),
        commission_rate: float = Form(...),
        payment_terms_days: int = Form(...)
):
    """Actualizează date companie."""
    from sqlalchemy import select

    result = await db.execute(
        select(VendorCompany).where(VendorCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Actualizează datele
    company.name = name
    company.legal_name = legal_name
    company.tax_id = tax_id
    company.email = email
    company.phone = phone
    company.address = address
    company.bank_account = bank_account
    company.bank_name = bank_name
    company.description = description
    company.website = website
    company.commission_rate = Decimal(str(commission_rate))
    company.payment_terms_days = payment_terms_days

    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_company/{company_id}",
        status_code=303
    )


@vendor_company_router.post("/{company_id}/delete")
async def delete_company(
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["super_admin"]))
):
    """Șterge permanent o companie vendor și toate datele asociate."""
    from sqlalchemy import select

    # Verifică dacă compania există
    result = await db.execute(
        select(VendorCompany).where(VendorCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Verifică dacă are produse sau comenzi active
    from models import Product, OrderItem

    # Verifică produse
    products_result = await db.execute(
        select(func.count(Product.id))
        .where(Product.vendor_company_id == company_id)
    )
    products_count = products_result.scalar()

    if products_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Nu se poate șterge! Compania are {products_count} produse. Ștergeți sau transferați produsele mai întâi."
        )

    # Verifică comenzi
    orders_result = await db.execute(
        select(func.count(OrderItem.id))
        .where(OrderItem.vendor_company_id == company_id)
    )
    orders_count = orders_result.scalar()

    if orders_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Nu se poate șterge! Compania are {orders_count} articole în comenzi active."
        )

    # Șterge compania (staff-ul se șterge automat prin cascade)
    await db.delete(company)
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/vendor_company/",
        status_code=303
    )


@vendor_company_router.post("/{company_id}/verify")
async def verify_company(
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["super_admin"]))
):
    """Verifică și aprobă companie."""
    await VendorCompanyService.verify_company(db, company_id, current_staff.id)

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_company/{company_id}",
        status_code=303
    )


@vendor_company_router.post("/{company_id}/toggle-status")
async def toggle_company_status(
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["super_admin"]))
):
    """
    Activează/Dezactivează companie cu toate efectele cascade.

    Când o companie se dezactivează:
    1. Toți VendorStaff nu se mai pot autentifica
    2. Toate produsele devin is_active=False
    3. Toate prețurile produselor devin is_active=False
    """
    from sqlalchemy import select, update
    from models import VendorCompany, Product, ProductPrice

    result = await db.execute(
        select(VendorCompany).where(VendorCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    old_status = company.is_active
    new_status = not company.is_active

    # company.is_active = new_status
    company.is_active = not company.is_active

    if not new_status:  # Dacă se dezactivează compania
        print(f"🔴 Dezactivez compania {company.name} și toate resursele asociate...")

        # 1. Dezactivează toate produsele companiei
        products_update_result = await db.execute(
            update(Product)
            .where(Product.vendor_company_id == company_id)
            .values(is_active=False)
        )
        affected_products = products_update_result.rowcount

        # 2. Obține ID-urile produselor pentru a dezactiva prețurile
        products_result = await db.execute(
            select(Product.id).where(Product.vendor_company_id == company_id)
        )
        product_ids = [row[0] for row in products_result.fetchall()]

        # 3. Dezactivează toate prețurile pentru produsele companiei
        affected_prices = 0
        if product_ids:
            prices_update_result = await db.execute(
                update(ProductPrice)
                .where(ProductPrice.product_id.in_(product_ids))
                .values(is_active=False)
            )
            affected_prices = prices_update_result.rowcount

        print(f"✅ Dezactivat: {affected_products} produse, {affected_prices} prețuri")

        # Log pentru audit
        print(f"🔍 AUDIT: Staff {current_staff.email} a dezactivat compania {company.name}")
        print(f"    - Produse afectate: {affected_products}")
        print(f"    - Prețuri afectate: {affected_prices}")

    else:  # Dacă se reactivează compania
        print(f"🟢 Reactivez compania {company.name}...")

        # La reactivare, NU reactivăm automat produsele și prețurile
        # Acestea trebuie reactivate manual pentru control granular
        print("ℹ️  Produsele și prețurile rămân dezactivate - reactivează manual dacă necesar")

        # Log pentru audit
        print(f"🔍 AUDIT: Staff {current_staff.email} a reactivat compania {company.name}")
        print(f"    - Produsele și prețurile rămân dezactivate pentru verificare manuală")



    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_company/{company_id}",
        status_code=303
    )


@vendor_company_router.post("/{company_id}/reactivate-products")
async def reactivate_company_products(
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["super_admin"]))
):
    """
    Reactivează toate produsele și prețurile unei companii.
    Disponibil doar când compania este activă.
    """
    from sqlalchemy import select
    from services.models.product_service import ProductService

    # Verifică dacă compania există și este activă
    result = await db.execute(
        select(VendorCompany).where(VendorCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    if not company.is_active:
        raise HTTPException(
            status_code=400,
            detail="Nu se pot reactiva produsele unei companii dezactivate"
        )

    # Reactivează produsele și prețurile
    try:
        stats = await ProductService.reactivate_company_products(
            db=db,
            company_id=company_id,
            staff_id=current_staff.id
        )

        # Adaugă un mesaj de succes (dacă folosești flash messages)
        # flash(f"Reactivat cu succes: {stats['products_reactivated']} produse și {stats['prices_reactivated']} prețuri")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la reactivare: {str(e)}")

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_company/{company_id}",
        status_code=303
    )


@vendor_company_router.get("/{company_id}/products-status", response_class=HTMLResponse)
async def company_products_status(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        show_inactive: bool = False
):
    """
    Afișează statusul produselor companiei cu opțiune de a vedea și cele inactive.
    """
    from sqlalchemy import select, func, case, and_
    from models import Product, ProductPrice

    # Verifică compania
    company = await VendorCompanyService.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Statistici produse
    query_base = select(Product).where(Product.vendor_company_id == company_id)

    if not show_inactive:
        query_base = query_base.where(Product.is_active == True)

    # Obține produsele cu statusuri
    result = await db.execute(
        query_base
        .options(
            selectinload(Product.category),
            selectinload(Product.prices)
        )
        .order_by(Product.is_active.desc(), Product.name)
    )
    products = result.scalars().all()

    # Statistici
    stats_result = await db.execute(
        select(
            func.count(Product.id).label('total'),
            func.sum(case((Product.is_active == True, 1), else_=0)).label('active'),
            func.sum(case((Product.is_active == False, 1), else_=0)).label('inactive')
        ).where(Product.vendor_company_id == company_id)
    )
    stats = stats_result.first()

    # Statistici prețuri
    prices_stats_result = await db.execute(
        select(
            func.count(ProductPrice.id).label('total_prices'),
            func.sum(case((ProductPrice.is_active == True, 1), else_=0)).label('active_prices'),
            func.sum(case((ProductPrice.is_active == False, 1), else_=0)).label('inactive_prices')
        )
        .select_from(Product)
        .join(ProductPrice)
        .where(Product.vendor_company_id == company_id)
    )
    prices_stats = prices_stats_result.first()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "products": products,
        "show_inactive": show_inactive,
        "stats": {
            "total_products": stats.total or 0,
            "active_products": stats.active or 0,
            "inactive_products": stats.inactive or 0,
            "total_prices": prices_stats.total_prices or 0,
            "active_prices": prices_stats.active_prices or 0,
            "inactive_prices": prices_stats.inactive_prices or 0
        },
        "page_title": f"Status Produse {company.name}"
    })

    return templates.TemplateResponse("vendor_company/products_status.html", context)


@vendor_company_router.get("/{company_id}/staff", response_class=HTMLResponse)
async def company_staff(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff)
):
    """Listează angajații companiei."""
    from sqlalchemy import select
    from models import VendorStaff

    # Verifică compania
    company = await VendorCompanyService.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Query staff
    result = await db.execute(
        select(VendorStaff)
        .where(VendorStaff.company_id == company_id)
        .order_by(VendorStaff.created_at.desc())
    )
    staff_members = result.scalars().all()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "staff_members": staff_members,
        "page_title": f"Angajați {company.name}",
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_company/staff.html", context)


@vendor_company_router.post("/{company_id}/reactivate-products")
async def reactivate_company_products(
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(require_role(["manager", "super_admin"]))
):
    """
    Reactivează toate produsele și prețurile unei companii.
    Disponibil doar când compania este activă.
    """
    from sqlalchemy import select
    from services.models.product_service import ProductService

    # Verifică dacă compania există și este activă
    result = await db.execute(
        select(VendorCompany).where(VendorCompany.id == company_id)
    )
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    if not company.is_active:
        raise HTTPException(
            status_code=400,
            detail="Nu se pot reactiva produsele unei companii dezactivate"
        )

    # Reactivează produsele și prețurile
    try:
        stats = await ProductService.reactivate_company_products(
            db=db,
            company_id=company_id,
            staff_id=current_staff.id
        )

        print(
            f"✅ REACTIVARE MANUALĂ: {stats['products_reactivated']} produse și {stats['prices_reactivated']} prețuri pentru compania {company.name}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la reactivare: {str(e)}")

    return RedirectResponse(
        url=f"/dashboard/staff/vendor_company/{company_id}/products-status",
        status_code=303
    )


@vendor_company_router.get("/{company_id}/products-status", response_class=HTMLResponse)
async def company_products_status(
        request: Request,
        company_id: int,
        db=Depends(get_db),
        current_staff: Staff = Depends(get_current_staff),
        show_inactive: bool = False
):
    """
    Afișează statusul produselor companiei cu opțiune de a vedea și cele inactive.
    """
    from sqlalchemy import select, func, case, and_
    from models import Product, ProductPrice

    # Verifică compania
    company = await VendorCompanyService.get_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Compania nu a fost găsită")

    # Query pentru produse
    query_base = select(Product).where(Product.vendor_company_id == company_id)

    if not show_inactive:
        query_base = query_base.where(Product.is_active == True)

    # Obține produsele cu statusuri
    result = await db.execute(
        query_base
        .options(
            selectinload(Product.category),
            selectinload(Product.prices)  # Toate prețurile, nu doar active
        )
        .order_by(Product.is_active.desc(), Product.name)
    )
    products = result.scalars().all()

    # Statistici produse
    stats_result = await db.execute(
        select(
            func.count(Product.id).label('total'),
            func.sum(case((Product.is_active == True, 1), else_=0)).label('active'),
            func.sum(case((Product.is_active == False, 1), else_=0)).label('inactive')
        ).where(Product.vendor_company_id == company_id)
    )
    stats = stats_result.first()

    # Statistici prețuri
    prices_stats_result = await db.execute(
        select(
            func.count(ProductPrice.id).label('total_prices'),
            func.sum(case((ProductPrice.is_active == True, 1), else_=0)).label('active_prices'),
            func.sum(case((ProductPrice.is_active == False, 1), else_=0)).label('inactive_prices')
        )
        .select_from(Product)
        .join(ProductPrice)
        .where(Product.vendor_company_id == company_id)
    )
    prices_stats = prices_stats_result.first()

    context = await get_template_context(request, current_staff, db)
    context.update({
        "company": company,
        "products": products,
        "show_inactive": show_inactive,
        "stats": {
            "total_products": stats.total or 0,
            "active_products": stats.active or 0,
            "inactive_products": stats.inactive or 0,
            "total_prices": prices_stats.total_prices or 0,
            "active_prices": prices_stats.active_prices or 0,
            "inactive_prices": prices_stats.inactive_prices or 0
        },
        "page_title": f"Status Produse {company.name}",
        "current_staff": current_staff
    })

    return templates.TemplateResponse("vendor_company/products_status.html", context)



