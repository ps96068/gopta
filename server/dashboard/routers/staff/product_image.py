# server/dashboard/routers/product_image.py
"""
Router pentru gestionarea galeriei de imagini produse.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Product, ProductImage, Category
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.product_service import ProductService
from services.dashboard.file_service import FileService

product_image_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@product_image_router.get("/", response_class=HTMLResponse)
async def product_image_gallery(
        request: Request,
        category_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        per_page: int = Query(24, ge=1, le=48),
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Galerie imagini produse - afișare TOATE produsele active."""

    # Get default image path
    default_image = FileService.get_default_product_image()

    # Query pentru TOATE produsele active cu imaginile lor
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.images)
    ).where(Product.is_active == True)

    # Filtre
    if category_id:
        query = query.where(Product.category_id == category_id)

    if search:
        query = query.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
        )

    # Total pentru paginare
    total_query = select(func.count(Product.id)).select_from(Product).where(Product.is_active == True)

    if category_id:
        total_query = total_query.where(Product.category_id == category_id)
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

    # Get categories for filter
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True).order_by(Category.name)
    )
    categories = categories_result.scalars().all()

    # Stats - doar imagini non-default
    total_images = await db.execute(
        select(func.count(ProductImage.id))
        .where(ProductImage.image_path != default_image)
    )
    total_images_count = total_images.scalar() or 0

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Galerie Imagini Produse",
        "products": products,
        "categories": categories,
        "category_filter": category_id,
        "search_query": search,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "total_images": total_images_count,
        "default_image": default_image
    })

    return templates.TemplateResponse("product_image/gallery.html", context)


@product_image_router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_image_detail(
        request: Request,
        product_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagină detaliu imagini pentru un produs specific."""

    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.category),
            selectinload(Product.images)
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Produs negăsit")

    # Filtrează imaginea default pentru afișare
    default_image = FileService.get_default_product_image()
    real_images = [img for img in product.images if img.image_path != default_image]

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Imagini: {product.name}",
        "product": product,
        "images": real_images,
        "images_count": len(real_images),
        "max_images": 4,
        "default_image": default_image
    })

    return templates.TemplateResponse("product_image/detail.html", context)


@product_image_router.post("/{product_id}/upload")
async def upload_product_image(
        product_id: int,
        image: UploadFile = File(...),
        is_primary: Optional[bool] = Form(None),
        alt_text: Optional[str] = Form(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Upload imagine pentru produs."""

    try:
        # Get product with images
        result = await db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.images))
        )
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404)

        # Count real images (exclude default)
        default_image = FileService.get_default_product_image()
        real_images = [img for img in product.images if img.image_path != default_image]

        if len(real_images) >= 4:
            return JSONResponse(
                status_code=400,
                content={"error": "Maxim 4 imagini per produs"}
            )

        # Dacă nu are imagini reale, aceasta va fi primary automat
        if is_primary is None:
            is_primary = len(real_images) == 0

        # Save image
        image_path, file_name, file_size = await FileService.save_product_image(
            image, product.sku
        )

        # Remove default image if exists and this is the first real image
        if len(real_images) == 0:
            default_images = [img for img in product.images if img.image_path == default_image]
            for img in default_images:
                await db.delete(img)

        # Add new image
        await ProductService.add_image(
            db=db,
            product_id=product_id,
            image_path=image_path,
            file_name=file_name,
            file_size=file_size,
            alt_text=alt_text,
            is_primary=is_primary
        )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Imagine încărcată cu succes"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@product_image_router.post("/image/{image_id}/set-primary")
async def set_primary_image(
        image_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Setează imagine ca principală."""

    result = await db.execute(
        select(ProductImage).where(ProductImage.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404)

    # Remove primary from others
    other_images_result = await db.execute(
        select(ProductImage)
        .where(
            and_(
                ProductImage.product_id == image.product_id,
                ProductImage.is_primary == True,
                ProductImage.id != image_id
            )
        )
    )
    other_images = other_images_result.scalars().all()

    for other in other_images:
        other.is_primary = False

    image.is_primary = True
    await db.commit()

    return JSONResponse(
        status_code=200,
        content={"success": True}
    )


@product_image_router.delete("/image/{image_id}")
async def delete_product_image(
        image_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "product")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge imagine produs."""

    # Get image with product
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.id == image_id)
        .options(selectinload(ProductImage.product).selectinload(Product.images))
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404)

    # Check if it's the last real image
    default_image = FileService.get_default_product_image()
    real_images = [img for img in image.product.images if img.image_path != default_image]

    # Delete the image
    deleted = await ProductService.delete_image(db, image_id)

    # If it was the last real image, add default back
    if len(real_images) == 1:  # Was 1, now 0
        default_img = ProductImage(
            product_id=image.product_id,
            image_path=default_image,
            file_name="prod_default.png",
            file_size=0,
            is_primary=True,
            sort_order=0
        )
        db.add(default_img)
        await db.commit()

    return JSONResponse(
        status_code=200,
        content={"success": True}
    )