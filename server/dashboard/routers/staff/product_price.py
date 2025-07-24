# server/dashboard/routers/product_price.py
"""
Router pentru gestionarea prețurilor produselor.
Permite vizualizare și actualizare în masă a prețurilor.
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Product, ProductPrice, PriceType, Category, Vendor, VendorCompany
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.product_service import ProductService

product_price_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only



@product_price_router.get("/", response_class=HTMLResponse)
async def price_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă produse cu toate prețurile pentru vizualizare și editare în masă."""

    # Obține parametrii manual din query string pentru a gestiona string-uri goale
    category_id_str = request.query_params.get('category_id', '')
    vendor_company_id_str = request.query_params.get('vendor_company_id', '')
    search = request.query_params.get('search', '')

    # Convertește în int doar dacă nu e string gol
    category_id = int(category_id_str) if category_id_str and category_id_str.isdigit() else None
    vendor_company_id = int(
        vendor_company_id_str) if vendor_company_id_str and vendor_company_id_str.isdigit() else None

    # Query pentru produse - FĂRĂ să filtrezi prețurile în eager loading
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.vendor_company),
        selectinload(Product.prices)  # Include TOATE prețurile
    )
    # ).where(Product.is_active == True)

    # Filtre
    if category_id:
        query = query.where(Product.category_id == category_id)

    if vendor_company_id:
        query = query.where(Product.vendor_company_id == vendor_company_id)

    if search:
        query = query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    # Total pentru paginare
    # total_query = select(func.count(Product.id)).select_from(Product).where(Product.is_active == True)
    total_query = select(func.count(Product.id)).select_from(Product)
    if category_id:
        total_query = total_query.where(Product.category_id == category_id)
    if vendor_company_id:
        total_query = total_query.where(Product.vendor_company_id == vendor_company_id)
    if search:
        total_query = total_query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(Product.name).offset(offset).limit(per_page)

    result = await db.execute(query)

    products = result.scalars().all()


    # Organizare prețuri pentru afișare - TOATE prețurile (active și inactive)
    product_prices = {}
    for product in products:
        prices_dict = {}

        # Pentru FIECARE tip de preț, caută în toate prețurile produsului
        for price_type in PriceType:
            # Găsește prețul pentru acest tip
            price_obj = None
            for price in product.prices:
                if price.price_type == price_type:
                    price_obj = price
                    break

            # Adaugă în dicționar (chiar dacă e None)
            if price_obj:
                prices_dict[price_type.value] = {
                    'price': price_obj,
                    'amount': price_obj.amount,
                    'is_active': price_obj.is_active,
                    'updated_at': price_obj.updated_at
                }
            else:
                # Nu există preț pentru acest tip
                prices_dict[price_type.value] = None

        product_prices[product.id] = prices_dict

    # Debug pentru a verifica prețurile
    # print(f"🔍 DEBUG: Produse găsite: {len(products)}")
    # for product in products:
    #     print(f"   - {product.name}: {len(product.prices)} prețuri")
    #     for price in product.prices:
    #         print(f"     * {price.price_type.value}: {price.amount} MDL (active: {price.is_active})")


    # Get categories and vendors for filters
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    vendors_result = await db.execute(
        # select(VendorCompany).where(VendorCompany.is_active == True).order_by(VendorCompany.name)
        select(VendorCompany).order_by(VendorCompany.name)
    )
    vendors = vendors_result.scalars().all()

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff, db)
    context.update({
        "page_title": "Prețuri Produse",
        "products": products,
        "product_prices": product_prices,
        "categories": categories,
        "vendors": vendors,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "category_filter": category_id,
        "vendor_filter": vendor_company_id,
        "search_query": search,
        "price_types": list(PriceType)
    })

    return templates.TemplateResponse("product_price/list.html", context)

@product_price_router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_price_detail(
        request: Request,
        product_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagină detaliu prețuri pentru un produs specific."""

    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.category),
            selectinload(Product.vendor_company),
            selectinload(Product.prices)  # Toate prețurile, nu doar active
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Debug pentru a verifica prețurile
    print(f"🔍 DEBUG DETAIL: Produs {product.name}")
    print(f"   - Total prețuri: {len(product.prices)}")
    for price in product.prices:
        print(f"   - {price.price_type.value}: {price.amount} MDL (active: {price.is_active})")

    # Verifică dacă modelul ProductPrice are câmpul is_active
    from sqlalchemy import inspect
    inspector = inspect(ProductPrice)
    columns = [col.name for col in inspector.columns]
    print(f"🔍 DEBUG: Coloane ProductPrice: {columns}")

    # Verifică dacă există prețuri inactive în baza de date
    inactive_prices_count = await db.execute(
        select(func.count(ProductPrice.id))
        .where(ProductPrice.is_active == False)
    )
    print(f"🔍 DEBUG: Total prețuri inactive în BD: {inactive_prices_count.scalar()}")

    # Verifică dacă produsul curent are prețuri inactive
    current_inactive = await db.execute(
        select(func.count(ProductPrice.id))
        .where(
            and_(
                ProductPrice.product_id == product_id,
                ProductPrice.is_active == False
            )
        )
    )
    print(f"🔍 DEBUG: Prețuri inactive pentru produsul {product_id}: {current_inactive.scalar()}")



    # Organizare prețuri - INCLUDE STATUS
    prices_dict = {}
    has_inactive_prices = False

    for price in product.prices:
        prices_dict[price.price_type] = price
        if not price.is_active:
            has_inactive_prices = True

    # Verifică dacă produsul aparține unei companii inactive
    company_active = product.vendor_company.is_active if product.vendor_company else True

    context = await get_template_context(request, staff, db)
    context.update({
        "page_title": f"Prețuri: {product.name}",
        "product": product,
        "prices_dict": prices_dict,
        "price_types": list(PriceType),
        "has_inactive_prices": has_inactive_prices,
        "company_active": company_active,
        "can_edit": company_active and not has_inactive_prices
        # Poate edita doar dacă compania e activă și nu are prețuri inactive
    })

    return templates.TemplateResponse("product_price/detail.html", context)


@product_price_router.post("/product/{product_id}/update")
async def update_product_prices(
        request: Request,
        product_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează toate prețurile pentru un produs - doar dacă sunt active."""

    # Verifică mai întâi dacă produsul și prețurile sunt active
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.vendor_company),
            selectinload(Product.prices)
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Verifică dacă compania este activă
    if not product.vendor_company.is_active:
        return RedirectResponse(
            url=f"/dashboard/staff/product_price/product/{product_id}?error=company_inactive",
            status_code=303
        )

    # Verifică dacă toate prețurile sunt active
    inactive_prices = [p for p in product.prices if not p.is_active]
    if inactive_prices:
        return RedirectResponse(
            url=f"/dashboard/staff/product_price/product/{product_id}?error=prices_inactive",
            status_code=303
        )

    # Get form data
    form = await request.form()

    try:
        # Pentru fiecare tip de preț
        for price_type in PriceType:
            amount_str = form.get(f"price_{price_type.value}")
            if amount_str:
                amount = float(amount_str)

                # Actualizează sau creează prețul
                await ProductService.set_price(
                    db=db,
                    product_id=product_id,
                    price_type=price_type,
                    amount=amount
                )

        return RedirectResponse(
            url=f"/dashboard/staff/product_price/product/{product_id}?success=updated",
            status_code=303
        )

    except ValueError:
        return RedirectResponse(
            url=f"/dashboard/staff/product_price/product/{product_id}?error=invalid_amount",
            status_code=303
        )
    except Exception as e:
        print(f"Error updating prices: {e}")  # Pentru debug
        return RedirectResponse(
            url=f"/dashboard/staff/product_price/product/{product_id}?error=update_failed",
            status_code=303
        )


@product_price_router.post("/bulk-update")
async def bulk_update_prices(
        request: Request,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizare în masă a prețurilor (AJAX) - doar pentru prețuri active."""

    try:
        data = await request.json()
        updates = data.get('updates', [])

        results = []
        errors = []

        for update in updates:
            product_id = update.get('product_id')
            price_type = PriceType(update.get('price_type'))
            amount = float(update.get('amount'))

            # Verifică dacă prețul este activ
            price_result = await db.execute(
                select(ProductPrice)
                .where(
                    and_(
                        ProductPrice.product_id == product_id,
                        ProductPrice.price_type == price_type
                    )
                )
            )
            existing_price = price_result.scalar_one_or_none()

            if existing_price and not existing_price.is_active:
                errors.append({
                    'product_id': product_id,
                    'price_type': price_type.value,
                    'error': 'Prețul este inactiv'
                })
                continue

            # Actualizează prețul
            await ProductService.set_price(
                db=db,
                product_id=product_id,
                price_type=price_type,
                amount=amount
            )

            results.append({
                'product_id': product_id,
                'price_type': price_type.value,
                'success': True
            })

        return JSONResponse({
            'success': len(errors) == 0,
            'updated': len(results),
            'results': results,
            'errors': errors
        })

    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        }, status_code=400)

