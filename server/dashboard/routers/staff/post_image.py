# server/dashboard/routers/staff/post_image.py
"""
Router pentru gestionarea imaginilor articolelor blog.
"""
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Post, PostImage, Staff, StaffRole, Category
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.blog_service import BlogService
from services.dashboard.file_service import FileService

post_image_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@post_image_router.get("/", response_class=HTMLResponse)
async def post_images_gallery(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        page: int = Query(1, ge=1),
        search: Optional[str] = Query(None),
        author_id: Optional[int] = Query(None)
):
    """Galerie generală pentru toate imaginile articolelor."""
    # Build query for posts with images
    query = select(Post).options(
        selectinload(Post.images),
        selectinload(Post.author)
    )

    # Apply filters
    filters = []
    if search:
        filters.append(
            or_(
                Post.title.ilike(f"%{search}%"),
                Post.slug.ilike(f"%{search}%")
            )
        )

    if author_id:
        filters.append(Post.author_id == author_id)

    if filters:
        query = query.where(and_(*filters))

    # Order by updated date
    query = query.order_by(desc(Post.updated_at))

    # Count total posts
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    per_page = 24
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    # Execute query
    result = await db.execute(query)
    posts = result.scalars().all()

    # Count total images
    total_images_result = await db.execute(
        select(func.count(PostImage.id))
    )
    total_images = total_images_result.scalar() or 0

    # Get authors for filter
    authors_result = await db.execute(
        select(Staff).where(
            Staff.role.in_([StaffRole.SUPER_ADMIN, StaffRole.MANAGER])
        )
    )
    authors = authors_result.scalars().all()

    # Get default image path
    default_image = FileService.get_default_blog_image()

    context = await get_template_context(request, staff, db)
    context.update({
        "posts": posts,
        "page": page,
        "total": total,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "total_images": total_images,
        "search": search,
        "author_id": author_id,
        "authors": authors,
        "default_image": default_image,
        "page_title": "Imagini Articole"
    })

    return templates.TemplateResponse(
        "post_image/gallery.html",
        context
    )


@post_image_router.get("/{post_id}", response_class=HTMLResponse)
async def post_images_list(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Lista imaginilor pentru un articol specific."""
    # Get post with images
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.images))
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Articol negăsit")

    # Sort images
    featured_image = None
    content_images = []

    for img in post.images:
        if img.is_featured:
            featured_image = img
        else:
            content_images.append(img)

    # Sort content images by sort_order
    content_images.sort(key=lambda x: x.sort_order)

    context = await get_template_context(request, staff, db)
    context.update({
        "post": post,
        "featured_image": featured_image,
        "content_images": content_images,
        "images_count": len(content_images),
        "can_upload": len(content_images) < 5,  # Max 5 content images
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error")
    })

    return templates.TemplateResponse(
        "post_image/list.html",
        context
    )


@post_image_router.post("/{post_id}/upload")
async def upload_image(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        image: UploadFile = File(...),
        alt_text: Optional[str] = Form(None),
        caption: Optional[str] = Form(None),
        is_featured: bool = Form(False)
):
    """Upload imagine pentru articol."""
    # Check permission
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403, detail="Nu aveți permisiune")

    # Get post
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404)

    try:
        # Check content images limit (5 max, not counting featured)
        if not is_featured:
            count_result = await db.execute(
                select(func.count(PostImage.id))
                .where(
                    and_(
                        PostImage.post_id == post_id,
                        PostImage.is_featured == False
                    )
                )
            )
            content_count = count_result.scalar() or 0

            if content_count >= 5:
                # Check if request is from AJAX (modal)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Limita de 5 imagini pentru conținut a fost atinsă!"}
                    )
                else:
                    return RedirectResponse(
                        url=f"/dashboard/staff/post_image/{post_id}?error=limit",
                        status_code=303
                    )

        # Save image
        image_path, file_name, file_size = await FileService.save_blog_image(
            image,
            post.slug
        )

        # Get next sort order
        max_order_result = await db.execute(
            select(func.max(PostImage.sort_order))
            .where(PostImage.post_id == post_id)
        )
        max_order = max_order_result.scalar() or 0

        # Add to database
        new_image = await BlogService.add_image(
            db=db,
            post_id=post_id,
            image_path=image_path,
            file_name=file_name,
            file_size=file_size,
            alt_text=alt_text or post.title,
            caption=caption,
            is_featured=is_featured,
            sort_order=max_order + 1 if not is_featured else 0
        )

        # Get the referer to determine where to redirect
        referer = request.headers.get('referer', '')

        # Check if upload is from edit page modal
        if f'/post/{post_id}/edit' in referer:
            # Redirect back to edit page with success message
            return RedirectResponse(
                url=f"/dashboard/staff/post/{post_id}/edit?success=image_uploaded",
                status_code=303
            )
        else:
            # Regular form submission - redirect to image list
            return RedirectResponse(
                url=f"/dashboard/staff/post_image/{post_id}?success=uploaded",
                status_code=303
            )

    except Exception as e:
        print(f"Error uploading image: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JSONResponse(
                status_code=500,
                content={"error": f"Eroare la încărcare: {str(e)}"}
            )
        else:
            return RedirectResponse(
                url=f"/dashboard/staff/post_image/{post_id}?error=upload",
                status_code=303
            )


@post_image_router.post("/{post_id}/image/{image_id}/update")
async def update_image(
        post_id: int,
        image_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        alt_text: str = Form(...),
        caption: Optional[str] = Form(None)
):
    """Actualizează detalii imagine."""
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403)

    # Get image
    result = await db.execute(
        select(PostImage).where(
            and_(
                PostImage.id == image_id,
                PostImage.post_id == post_id
            )
        )
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404)

    # Update
    image.alt_text = alt_text
    image.caption = caption
    await db.commit()

    return JSONResponse({"success": True})


@post_image_router.post("/{post_id}/image/{image_id}/set-featured")
async def set_featured_image(
        post_id: int,
        image_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Setează imagine ca featured."""
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403)

    # Remove current featured
    result = await db.execute(
        select(PostImage)
        .where(
            and_(
                PostImage.post_id == post_id,
                PostImage.is_featured == True
            )
        )
    )

    for img in result.scalars().all():
        img.is_featured = False

    # Set new featured
    result = await db.execute(
        select(PostImage).where(
            and_(
                PostImage.id == image_id,
                PostImage.post_id == post_id
            )
        )
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404)

    image.is_featured = True
    image.sort_order = 0
    await db.commit()

    return JSONResponse({"success": True})


@post_image_router.post("/{post_id}/reorder")
async def reorder_images(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Reordonează imaginile."""
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403)

    # Get JSON data
    data = await request.json()
    image_ids = data.get("image_ids", [])

    # Update sort order
    for index, image_id in enumerate(image_ids):
        result = await db.execute(
            select(PostImage).where(
                and_(
                    PostImage.id == image_id,
                    PostImage.post_id == post_id,
                    PostImage.is_featured == False  # Don't reorder featured
                )
            )
        )
        image = result.scalar_one_or_none()

        if image:
            image.sort_order = index + 1

    await db.commit()

    return JSONResponse({"success": True})


@post_image_router.post("/{post_id}/image/{image_id}/delete")
async def delete_image(
        post_id: int,
        image_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Șterge imagine."""
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403)

    # Get image
    result = await db.execute(
        select(PostImage).where(
            and_(
                PostImage.id == image_id,
                PostImage.post_id == post_id
            )
        )
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404)

    # Don't delete the default image file
    if "blog_default.png" not in image.image_path:
        FileService.delete_image(image.image_path)

    # Delete from DB
    await db.delete(image)
    await db.commit()

    return RedirectResponse(
        url=f"/dashboard/staff/post_image/{post_id}?success=deleted",
        status_code=303
    )


@post_image_router.get("/gallery/{post_id}", response_class=HTMLResponse)
async def image_gallery_modal(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Modal pentru selectare imagini în editor."""
    # Get post images
    result = await db.execute(
        select(PostImage)
        .where(
            and_(
                PostImage.post_id == post_id,
                PostImage.is_featured == False
            )
        )
        .order_by(PostImage.sort_order)
    )
    images = result.scalars().all()

    context = {
        "request": request,
        "images": images,
        "post_id": post_id
    }

    return templates.TemplateResponse(
        "post_image/gallery_modal.html",
        context
    )