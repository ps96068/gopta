# server/dashboard/routers/products.py
"""
Router pentru gestionarea produselor.
"""

from __future__ import annotations
import pprint
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from slugify import slugify

from cfg import get_db
from models import Product, Category, Vendor, ProductImage, ProductPrice, PriceType, VendorCompany
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.product_service import ProductService
from services.dashboard.file_service import FileService

products_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@products_router.get("/", response_class=HTMLResponse)
async def product_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        vendor_company_id: Optional[int] = None,
        is_active: Optional[str] = None,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă produse cu filtre și prețuri."""

    # Query de bază
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.vendor_company),
        selectinload(Product.images),
        selectinload(Product.prices)
    )

    # Filtre
    filters = []

    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    if category_id:
        filters.append(Product.category_id == category_id)

    if vendor_company_id:
        filters.append(Product.vendor_company_id == vendor_company_id)

    if is_active is not None:
        if is_active == "true":
            filters.append(Product.is_active == True)
        elif is_active == "false":
            filters.append(Product.is_active == False)

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count()).select_from(Product)
    if filters:
        total_query = total_query.where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare și paginare
    offset = (page - 1) * per_page
    query = query.order_by(Product.sort_order, Product.name).offset(offset).limit(per_page)

    result = await db.execute(query)
    products = result.scalars().all()

    # Get categories and vendors for filters
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    vendors_result = await db.execute(
        select(VendorCompany).where(VendorCompany.is_active == True).order_by(VendorCompany.name)
    )
    vendors = vendors_result.scalars().all()

    # Stats
    total_products = await db.execute(
        select(func.count(Product.id))
    )
    total_count = total_products.scalar() or 0

    active_products = await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True)
    )
    active_count = active_products.scalar() or 0

    # Prepare prices for display
    product_prices = {}
    for product in products:
        prices_dict = {}
        for price in product.prices:
            prices_dict[price.price_type.value] = float(price.amount)
        product_prices[product.id] = prices_dict

    # Get primary images
    product_images = {}
    for product in products:
        primary_image = next((img for img in product.images if img.is_primary), None)
        if primary_image:
            product_images[product.id] = primary_image.image_path
        else:
            product_images[product.id] = FileService.get_default_product_image()

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff)



    context.update({
        "page_title": "Produse",
        "products": products,
        "product_prices": product_prices,
        "product_images": product_images,
        "categories": categories,
        "vendors": vendors,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "total_products": total_count,
        "active_products": active_count,
        "inactive_products": total_count - active_count,
        "search_query": search,
        "category_filter": category_id,
        "vendor_filter": vendor_company_id,
        "is_active_filter": is_active
    })

    return templates.TemplateResponse("product/list.html", context)


@products_router.get("/create", response_class=HTMLResponse)
async def product_create_form(
        request: Request,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare produs nou."""

    # Get categories and vendors
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    vendors_result = await db.execute(
        select(VendorCompany).where(VendorCompany.is_active == True).order_by(VendorCompany.name)
    )
    vendors = vendors_result.scalars().all()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Produs Nou",
        "categories": categories,
        "vendors": vendors,
        "price_types": list(PriceType)
    })

    return templates.TemplateResponse("product/form.html", context)


@products_router.post("/create")
async def product_create(
        name: str = Form(...),
        sku: str = Form(...),
        slug: Optional[str] = Form(None),
        category_id: int = Form(...),
        vendor_company_id: int = Form(...),
        description: Optional[str] = Form(None),
        short_description: Optional[str] = Form(None),
        sort_order: int = Form(0),
        is_active: bool = Form(True),
        meta_title: Optional[str] = Form(None),
        meta_description: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Creează produs nou cu imagine default."""

    try:
        # Generate slug if not provided
        if not slug:
            slug = slugify(name)

        # Check SKU uniqueness
        existing_sku = await db.execute(
            select(Product).where(Product.sku == sku)
        )
        if existing_sku.scalar_one_or_none():
            return RedirectResponse(
                url="/dashboard/staff/product/create?error=sku_exists",
                status_code=303
            )

        # Check slug uniqueness
        existing_slug = await db.execute(
            select(Product).where(Product.slug == slug)
        )
        if existing_slug.scalar_one_or_none():
            return RedirectResponse(
                url="/dashboard/staff/product/create?error=slug_exists",
                status_code=303
            )

        # Create product
        product = Product(
            name=name,
            sku=sku,
            slug=slug,
            category_id=category_id,
            vendor_company_id=vendor_company_id,
            description=description,
            short_description=short_description,
            sort_order=sort_order,
            is_active=is_active,
            meta_title=meta_title,
            meta_description=meta_description,
            in_stock=True  # Default to in stock
        )

        db.add(product)
        await db.commit()
        await db.refresh(product)

        # Add default image
        default_image = ProductImage(
            product_id=product.id,
            image_path=FileService.get_default_product_image(),
            file_name="prod_default.png",
            file_size=0,
            is_primary=True,
            sort_order=0
        )
        db.add(default_image)

        # Add default prices (all 0)
        for price_type in PriceType:
            price = ProductPrice(
                product_id=product.id,
                price_type=price_type,
                amount=0,
                currency="MDL"
            )
            db.add(price)

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/product?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating product: {e}")
        return RedirectResponse(
            url="/dashboard/staff/product/create?error=create_failed",
            status_code=303
        )


@products_router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(
        request: Request,
        product_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii produs cu imagini și prețuri."""

    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.category),
            selectinload(Product.vendor_company),
            selectinload(Product.images),
            selectinload(Product.prices),
            selectinload(Product.cart_items),
            selectinload(Product.order_items)
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Organize prices by type
    prices_dict = {}
    for price in product.prices:
        prices_dict[price.price_type.value] = price

    # Get primary image
    primary_image = next((img for img in product.images if img.is_primary), None)

    # Basic stats
    total_orders = len(set(item.order_id for item in product.order_items))
    total_quantity_sold = sum(item.quantity for item in product.order_items)

    context = await get_template_context(request, staff)
    context.update({
        "page_title": product.name,
        "product": product,
        "prices_dict": prices_dict,
        "primary_image": primary_image,
        "total_orders": total_orders,
        "total_quantity_sold": total_quantity_sold,
        "price_types": list(PriceType)
    })

    return templates.TemplateResponse("product/detail.html", context)


@products_router.get("/{product_id}/edit", response_class=HTMLResponse)
async def product_edit_form(
        request: Request,
        product_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare produs."""

    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Get categories and vendors
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    vendors_result = await db.execute(
        select(VendorCompany).where(VendorCompany.is_active == True).order_by(VendorCompany.name)
    )
    vendors = vendors_result.scalars().all()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Editare: {product.name}",
        "product": product,
        "categories": categories,
        "vendors": vendors
    })

    return templates.TemplateResponse("product/form.html", context)


@products_router.post("/{product_id}/edit")
async def product_edit(
        product_id: int,
        name: str = Form(...),
        sku: str = Form(...),
        slug: str = Form(...),
        category_id: int = Form(...),
        vendor_company_id: int = Form(...),
        description: Optional[str] = Form(None),
        short_description: Optional[str] = Form(None),
        sort_order: int = Form(0),
        is_active: bool = Form(False),  # Checkbox trick
        meta_title: Optional[str] = Form(None),
        meta_description: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează produs."""

    try:
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404)

        # Check SKU uniqueness
        if product.sku != sku:
            existing_sku = await db.execute(
                select(Product).where(
                    and_(
                        Product.sku == sku,
                        Product.id != product_id
                    )
                )
            )
            if existing_sku.scalar_one_or_none():
                return RedirectResponse(
                    url=f"/dashboard/staff/product/{product_id}/edit?error=sku_exists",
                    status_code=303
                )

        # Check slug uniqueness
        if product.slug != slug:
            existing_slug = await db.execute(
                select(Product).where(
                    and_(
                        Product.slug == slug,
                        Product.id != product_id
                    )
                )
            )
            if existing_slug.scalar_one_or_none():
                return RedirectResponse(
                    url=f"/dashboard/staff/product/{product_id}/edit?error=slug_exists",
                    status_code=303
                )

        # Update product
        product.name = name
        product.sku = sku
        product.slug = slug
        product.category_id = category_id
        product.vendor_company_id = vendor_company_id
        product.description = description
        product.short_description = short_description
        product.sort_order = sort_order
        product.is_active = is_active
        product.meta_title = meta_title
        product.meta_description = meta_description

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/product/{product_id}?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating product: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/product/{product_id}/edit?error=update_failed",
            status_code=303
        )


@products_router.post("/{product_id}/toggle-active")
async def toggle_product_active(
        product_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Toggle active status produs."""

    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404)

    product.is_active = not product.is_active
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/product?success=status_toggled",
        status_code=303
    )


@products_router.post("/{product_id}/delete")
async def product_delete(
        product_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge produs (soft delete)."""

    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404)

    # Soft delete
    product.is_active = False
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/product?success=deleted",
        status_code=303
    )