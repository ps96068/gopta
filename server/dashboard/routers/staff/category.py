# server/dashboard/routers/category.py
"""
Router pentru gestionarea categoriilor cu upload imagini.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from slugify import slugify

from cfg import get_db
from models import Category, Product
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.category_services import CategoryService
from services.dashboard.file_service import FileService

category_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@category_router.get("/", response_class=HTMLResponse)
async def category_list(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        search: Optional[str] = None,
        parent_id: Optional[int] = None,
        is_active: Optional[str] = None,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Listă categorii cu structură arborescentă."""

    # Query de bază - TOATE categoriile
    query = select(Category)

    # Filtre
    filters = []

    if search:
        filters.append(
            or_(
                Category.name.ilike(f"%{search}%"),
                Category.slug.ilike(f"%{search}%")
            )
        )

    # Filtru pentru status
    if is_active is not None:
        if is_active == "true":
            filters.append(Category.is_active == True)
        elif is_active == "false":
            filters.append(Category.is_active == False)

    if parent_id is not None:
        filters.append(Category.parent_id == parent_id)
    else:
        # Doar categoriile root pentru afișare inițială
        filters.append(Category.parent_id == None)

    if filters:
        query = query.where(and_(*filters))

    # Include children (toate, nu doar active)
    query = query.options(selectinload(Category.children))

    # Total pentru paginare
    total_query = select(func.count()).select_from(Category)
    if parent_id is not None:
        total_query = total_query.where(Category.parent_id == parent_id)
    else:
        total_query = total_query.where(Category.parent_id == None)

    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    # Sortare și paginare
    offset = (page - 1) * per_page
    query = query.order_by(Category.sort_order, Category.name).offset(offset).limit(per_page)

    result = await db.execute(query)
    categories = result.scalars().all()

    # Stats - actualizat pentru toate și active
    all_categories = await db.execute(
        select(func.count(Category.id))
    )
    total_categories = all_categories.scalar() or 0

    active_categories = await db.execute(
        select(func.count(Category.id)).where(Category.is_active == True)
    )
    total_active = active_categories.scalar() or 0

    # Count products per category
    category_products = {}
    for cat in categories:
        products_count = await db.execute(
            select(func.count(Product.id))
            .where(Product.category_id == cat.id)
        )
        category_products[cat.id] = products_count.scalar() or 0

        # Count pentru subcategorii
        for child in cat.children:
            child_products = await db.execute(
                select(func.count(Product.id))
                .where(Product.category_id == child.id)
            )
            category_products[child.id] = child_products.scalar() or 0

    total_pages = (total + per_page - 1) // per_page

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Categorii",
        "categories": categories,
        "category_products": category_products,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "total_categories": total_categories,
        "total_active": total_active,
        "total_inactive": total_categories - total_active,
        "search_query": search,
        "parent_id": parent_id,
        "is_active_filter": is_active
    })

    return templates.TemplateResponse("category/list.html", context)



@category_router.get("/create", response_class=HTMLResponse)
async def category_create_form(
        request: Request,
        parent_id: Optional[int] = None,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Formular creare categorie nouă."""

    # Get all categories for parent selection
    all_cats = await db.execute(
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.name)
    )
    categories = all_cats.scalars().all()

    # If parent_id provided, get parent
    parent = None
    if parent_id:
        parent_result = await db.execute(
            select(Category).where(Category.id == parent_id)
        )
        parent = parent_result.scalar_one_or_none()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": "Categorie Nouă",
        "categories": categories,
        "parent": parent
    })

    return templates.TemplateResponse("category/form.html", context)


@category_router.post("/create")
async def category_create(
        name: str = Form(...),
        slug: Optional[str] = Form(None),
        parent_id: Optional[str] = Form(None),  # Schimbat în str
        description: Optional[str] = Form(None),
        sort_order: int = Form(0),
        image: Optional[UploadFile] = File(None),
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("create", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Creează categorie nouă cu imagine opțională."""

    try:
        # Generate slug if not provided
        if not slug:
            slug = slugify(name)

        # Check if slug exists
        existing = await db.execute(
            select(Category).where(Category.slug == slug)
        )
        if existing.scalar_one_or_none():
            return RedirectResponse(
                url="/dashboard/staff/category/create?error=slug_exists",
                status_code=303
            )

        # Handle image upload
        image_path = FileService.get_default_category_image()  # "static/webapp/img/category/cat_default.png"
        if image and image.filename:
            try:
                image_path = await FileService.save_category_image(image, slug)
            except HTTPException as e:
                return RedirectResponse(
                    url=f"/dashboard/staff/category/create?error=image_error",
                    status_code=303
                )

        # Create category
        parent_id_int = None
        if parent_id and parent_id.strip():
            try:
                parent_id_int = int(parent_id)
            except ValueError:
                parent_id_int = None

        category = Category(
            name=name,
            slug=slug,
            parent_id=parent_id_int,
            description=description,
            sort_order=sort_order,
            image_path=image_path
        )

        db.add(category)
        await db.commit()

        return RedirectResponse(
            url="/dashboard/staff/category?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating category: {e}")
        return RedirectResponse(
            url="/dashboard/staff/category/create?error=create_failed",
            status_code=303
        )



@category_router.get("/{category_id}/edit", response_class=HTMLResponse)
async def category_edit_form(
        request: Request,
        category_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Formular editare categorie."""

    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categorie negăsită")

    # Get all categories for parent selection (except self)
    all_cats = await db.execute(
        select(Category)
        .where(
            and_(
                Category.is_active == True,
                Category.id != category_id
            )
        )
        .order_by(Category.name)
    )
    categories = all_cats.scalars().all()

    context = await get_template_context(request, staff)
    context.update({
        "page_title": f"Editare: {category.name}",
        "category": category,
        "categories": categories
    })

    return templates.TemplateResponse("category/form.html", context)



@category_router.post("/{category_id}/edit")
async def category_edit(
        category_id: int,
        name: str = Form(...),
        slug: str = Form(...),
        parent_id: Optional[str] = Form(None),  # Schimbat în str pentru a gestiona ""
        description: Optional[str] = Form(None),
        sort_order: int = Form(0),
        image: Optional[UploadFile] = File(None),
        remove_image: Optional[str] = Form(None),  # Schimbat pentru checkbox
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Actualizează categorie cu gestionare imagine."""

    try:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404)

        # Check if slug exists (for other categories)
        existing = await db.execute(
            select(Category).where(
                and_(
                    Category.slug == slug,
                    Category.id != category_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return RedirectResponse(
                url=f"/dashboard/staff/category/{category_id}/edit?error=slug_exists",
                status_code=303
            )

        # Update basic fields
        category.name = name
        category.slug = slug
        # Convert parent_id from string to int or None
        if parent_id and parent_id.strip():
            try:
                category.parent_id = int(parent_id)
            except ValueError:
                category.parent_id = None
        else:
            category.parent_id = None
        category.description = description
        category.sort_order = sort_order

        # Handle image
        default_image = FileService.get_default_category_image()
        if remove_image and category.image_path != default_image:
            # Delete old image
            FileService.delete_image(category.image_path)
            category.image_path = default_image
            print(f"Image removed for category {category.id}")
        elif image and image.filename:
            print(f"Uploading new image: {image.filename}")
            # Delete old image if not default
            if category.image_path != default_image:
                FileService.delete_image(category.image_path)

            # Save new image
            try:
                new_image_path = await FileService.save_category_image(image, category.slug)
                category.image_path = new_image_path
                print(f"New image saved at: {new_image_path}")
            except HTTPException as e:
                print(f"Image upload error: {e.detail}")
                return RedirectResponse(
                    url=f"/dashboard/staff/category/{category_id}/edit?error=image_error",
                    status_code=303
                )

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/category/{category_id}?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating category: {e}")
        return RedirectResponse(
            url=f"/dashboard/staff/category/{category_id}/edit?error=update_failed",
            status_code=303
        )




@category_router.get("/{category_id}", response_class=HTMLResponse)
async def category_detail(
        request: Request,
        category_id: int,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Detalii categorie cu produse și subcategorii."""

    # Get category with relations
    result = await db.execute(
        select(Category)
        .where(Category.id == category_id)
        .options(
            selectinload(Category.parent),
            selectinload(Category.children)
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Categorie negăsită")

    # Count total products
    products_count_result = await db.execute(
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
    )
    products_count = products_count_result.scalar() or 0

    # Count active products
    active_products_result = await db.execute(
        select(func.count(Product.id))
        .where(
            and_(
                Product.category_id == category_id,
                Product.is_active == True,
                Product.in_stock == True
            )
        )
    )
    active_products_count = active_products_result.scalar() or 0

    # Get first 10 products
    products_result = await db.execute(
        select(Product)
        .where(Product.category_id == category_id)
        .order_by(Product.sort_order, Product.name)
        .limit(10)
    )
    products = products_result.scalars().all()

    # Check if there are more products
    has_more_products = products_count > 10

    # Count products for each subcategory
    child_products_count = {}
    for child in category.children:
        child_count = await db.execute(
            select(func.count(Product.id))
            .where(Product.category_id == child.id)
        )
        child_products_count[child.id] = child_count.scalar() or 0

    context = await get_template_context(request, staff)
    context.update({
        "page_title": category.name,
        "category": category,
        "products": products,
        "products_count": products_count,
        "active_products_count": active_products_count,
        "has_more_products": has_more_products,
        "child_products_count": child_products_count
    })

    return templates.TemplateResponse("category/detail.html", context)




@category_router.post("/{category_id}/toggle-active")
async def toggle_category_active(
        category_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("update", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Toggle active status categorie."""

    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404)

    category.is_active = not category.is_active
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/category?success=status_toggled",
        status_code=303
    )


@category_router.post("/{category_id}/delete")
async def category_delete(
        category_id: int,
        staff=Depends(get_current_staff),
        _=Depends(PermissionChecker("delete", "category")),
        db: AsyncSession = Depends(get_db)
):
    """Șterge categorie (soft delete)."""

    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404)

    # Check if has products
    products_count = await db.execute(
        select(func.count(Product.id))
        .where(Product.category_id == category_id)
    )

    if products_count.scalar() > 0:
        return RedirectResponse(
            url=f"/dashboard/staff/category/{category_id}?error=has_products",
            status_code=303
        )

    # Soft delete
    category.is_active = False
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/category?success=deleted",
        status_code=303
    )




