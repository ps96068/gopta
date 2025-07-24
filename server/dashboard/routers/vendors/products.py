# server/dashboard/routers/vendor/products.py
"""
Router pentru gestionarea produselor de către vendor.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from slugify import slugify

from cfg import get_db
from models import Product, Category, VendorStaff, ProductImage, ProductPrice, PriceType
from server.dashboard.dependencies import get_current_vendor_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.product_service import ProductService
from services.dashboard.file_service import FileService

vendor_products_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/vend")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@vendor_products_router.get("/", response_class=HTMLResponse)
async def vendor_product_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        is_active: Optional[str] = None,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă produse ale vendor-ului curent."""

    # Query doar pentru produsele companiei curente
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.images),
        selectinload(Product.prices)
    ).where(Product.vendor_company_id == vendor_staff.company_id)

    # Filtre
    filters = []

    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    if category_id:
        filters.append(Product.category_id == category_id)

    if is_active is not None:
        if is_active == "true":
            filters.append(Product.is_active == True)
        elif is_active == "false":
            filters.append(Product.is_active == False)

    if filters:
        query = query.where(and_(*filters))

    # Total pentru paginare
    total_query = select(func.count()).select_from(Product).where(
        Product.vendor_company_id == vendor_staff.company_id
    )
    if filters:
        total_query = total_query.where(and_(*filters))

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Paginare
    offset = (page - 1) * per_page
    query = query.order_by(Product.sort_order, Product.name).offset(offset).limit(per_page)

    result = await db.execute(query)
    products = result.scalars().all()

    # Get categories for filter
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    # Prepare prices and images
    product_prices = {}
    product_images = {}
    for product in products:
        # Prices
        prices_dict = {}
        for price in product.prices:
            prices_dict[price.price_type.value] = float(price.amount)
        product_prices[product.id] = prices_dict

        # Primary image
        primary_image = next((img for img in product.images if img.is_primary), None)
        if primary_image:
            product_images[product.id] = primary_image.image_path
        else:
            product_images[product.id] = FileService.get_default_product_image()

    # Stats
    active_count = await db.execute(
        select(func.count(Product.id))
        .where(
            and_(
                Product.vendor_company_id == vendor_staff.company_id,
                Product.is_active == True
            )
        )
    )
    active_products = active_count.scalar() or 0

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, vendor_staff)
    context.update({
        "page_title": "Produsele Mele",
        "products": products,
        "product_prices": product_prices,
        "product_images": product_images,
        "categories": categories,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "total_products": total,
        "active_products": active_products,
        "inactive_products": total - active_products,
        "search_query": search,
        "category_filter": category_id,
        "is_active_filter": is_active
    })

    return templates.TemplateResponse("/product/list.html", context)


@vendor_products_router.get("/create", response_class=HTMLResponse)
async def vendor_product_create_form(
        request: Request,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare produs nou pentru vendor."""

    # Get categories
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    context = await get_template_context(request, vendor_staff)
    context.update({
        "page_title": "Produs Nou",
        "categories": categories,
        "price_types": list(PriceType)
    })

    return templates.TemplateResponse("/product/form.html", context)


@vendor_products_router.post("/create")
async def vendor_product_create(
        name: str = Form(...),
        sku: str = Form(...),
        slug: Optional[str] = Form(None),
        category_id: int = Form(...),
        description: Optional[str] = Form(None),
        short_description: Optional[str] = Form(None),
        sort_order: int = Form(0),
        is_active: bool = Form(True),
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Creează produs nou pentru vendor."""

    try:
        # Generate slug if not provided
        if not slug:
            slug = slugify(name)

        # Check SKU uniqueness within company
        existing_sku = await db.execute(
            select(Product).where(
                and_(
                    Product.sku == sku,
                    Product.vendor_company_id == vendor_staff.company_id
                )
            )
        )
        if existing_sku.scalar_one_or_none():
            return RedirectResponse(
                url="/dashboard/vendor/product/create?error=sku_exists",
                status_code=303
            )

        # Create product
        product = Product(
            name=name,
            sku=sku,
            slug=slug,
            category_id=category_id,
            vendor_company_id=vendor_staff.company_id,
            description=description,
            short_description=short_description,
            sort_order=sort_order,
            is_active=is_active,
            in_stock=True
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
            url=f"/dashboard/vendor/product?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating product: {e}")
        return RedirectResponse(
            url="/dashboard/vendor/product/create?error=create_failed",
            status_code=303
        )


@vendor_products_router.get("/{product_id}", response_class=HTMLResponse)
async def vendor_product_detail(
        request: Request,
        product_id: int,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii produs vendor."""

    result = await db.execute(
        select(Product)
        .where(
            and_(
                Product.id == product_id,
                Product.vendor_company_id == vendor_staff.company_id
            )
        )
        .options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.prices),
            selectinload(Product.order_items)
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Organize prices
    prices_dict = {}
    for price in product.prices:
        prices_dict[price.price_type.value] = price

    # Get primary image
    primary_image = next((img for img in product.images if img.is_primary), None)

    # Sales stats
    total_orders = len(set(item.order_id for item in product.order_items))
    total_quantity_sold = sum(item.quantity for item in product.order_items)
    total_revenue = sum(float(item.subtotal) for item in product.order_items)

    context = await get_template_context(request, vendor_staff)
    context.update({
        "page_title": product.name,
        "product": product,
        "prices_dict": prices_dict,
        "primary_image": primary_image,
        "total_orders": total_orders,
        "total_quantity_sold": total_quantity_sold,
        "total_revenue": total_revenue,
        "price_types": list(PriceType)
    })

    return templates.TemplateResponse("/product/detail.html", context)


@vendor_products_router.get("/{product_id}/edit", response_class=HTMLResponse)
async def vendor_product_edit_form(
        request: Request,
        product_id: int,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare produs vendor."""

    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.vendor_company_id == vendor_staff.company_id
            )
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Get categories
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    context = await get_template_context(request, vendor_staff)
    context.update({
        "page_title": f"Editare: {product.name}",
        "product": product,
        "categories": categories
    })

    return templates.TemplateResponse("vend/product/form.html", context)


@vendor_products_router.post("/{product_id}/toggle-stock")
async def toggle_product_stock(
        product_id: int,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Toggle stoc produs."""

    result = await db.execute(
        select(Product).where(
            and_(
                Product.id == product_id,
                Product.vendor_company_id == vendor_staff.company_id
            )
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404)

    product.in_stock = not product.in_stock
    await db.commit()

    return RedirectResponse(
        url="/dashboard/vendor/product?success=stock_toggled",
        status_code=303
    )