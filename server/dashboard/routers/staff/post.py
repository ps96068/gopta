# server/dashboard/routers/staff/post.py
"""
Router pentru gestionarea articolelor blog.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from slugify import slugify

from cfg import get_db
from models import Post, PostImage, Staff, StaffRole
from server.dashboard.dependencies import get_current_staff, get_template_context, PermissionChecker
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models.blog_service import BlogService
from services.dashboard.file_service import FileService

post_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

# Filters pentru templates
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@post_router.get("/", response_class=HTMLResponse)
async def post_list(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        page: int = Query(1, ge=1),
        search: Optional[str] = Query(None),
        author_id: Optional[int] = Query(None),
        is_featured: Optional[bool] = Query(None),
        is_active: Optional[bool] = Query(None)
):
    """Lista articolelor cu filtrare și paginare."""
    # Build query
    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.images)
    )

    # Filters
    filters = []
    if search:
        filters.append(
            or_(
                Post.title.ilike(f"%{search}%"),
                Post.content.ilike(f"%{search}%"),
                Post.excerpt.ilike(f"%{search}%")
            )
        )

    if author_id:
        filters.append(Post.author_id == author_id)

    if is_featured is not None:
        filters.append(Post.is_featured == is_featured)

    if is_active is not None:
        filters.append(Post.is_active == is_active)

    if filters:
        query = query.where(and_(*filters))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    per_page = 20
    offset = (page - 1) * per_page
    query = query.order_by(desc(Post.created_at)).offset(offset).limit(per_page)

    # Execute
    result = await db.execute(query)
    posts = result.scalars().all()

    # Get featured image for each post
    for post in posts:
        post.featured_image = next(
            (img for img in post.images if img.is_featured),
            None
        )

    # Get authors for filter
    authors_result = await db.execute(
        select(Staff).where(
            Staff.role.in_([StaffRole.SUPER_ADMIN, StaffRole.MANAGER])
        )
    )
    authors = authors_result.scalars().all()

    context = await get_template_context(request, staff, db)
    context.update({
        "posts": posts,
        "page": page,
        "total": total,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "search": search,
        "author_id": author_id,
        "is_featured": is_featured,
        "is_active": is_active,
        "authors": authors
    })

    return templates.TemplateResponse(
        "post/list.html",
        context
    )


@post_router.get("/create", response_class=HTMLResponse)
async def post_create_form(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Formular creare articol nou."""
    # Check permission
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Nu aveți permisiune")

    context = await get_template_context(request, staff, db)
    context.update({
        "post": None,
        "action": "create"
    })

    return templates.TemplateResponse(
        "post/form.html",
        context
    )


@post_router.post("/create")
async def post_create(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        title: str = Form(...),
        content: str = Form(...),
        excerpt: Optional[str] = Form(None),
        meta_title: str = Form(...),
        meta_description: str = Form(...),
        is_featured: bool = Form(False),
        is_active: bool = Form(False),
        featured_image: Optional[UploadFile] = File(None)
):
    """Creează articol nou."""
    # Check permission
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Nu aveți permisiune")

    try:
        # Generate slug
        slug = slugify(title)

        # Check if slug exists
        existing = await db.execute(
            select(Post).where(Post.slug == slug)
        )
        if existing.scalar_one_or_none():
            # Add timestamp to make unique
            slug = f"{slug}-{int(datetime.now().timestamp())}"

        # Create post
        post = await BlogService.create_post(
            db=db,
            title=title,
            slug=slug,
            content=content,
            author_id=staff.id,
            excerpt=excerpt,
            meta_title=meta_title,
            meta_description=meta_description,
            is_featured=is_featured,
            is_active=is_active if staff.role == StaffRole.SUPER_ADMIN else False
        )

        # Handle featured image
        if featured_image and featured_image.filename:
            try:
                image_path, file_name, file_size = await FileService.save_blog_image(
                    featured_image,
                    post.slug
                )

                # Add as featured image
                await BlogService.add_image(
                    db=db,
                    post_id=post.id,
                    image_path=image_path,
                    file_name=file_name,
                    file_size=file_size,
                    alt_text=title,
                    is_featured=True
                )
            except Exception as e:
                print(f"Error saving featured image: {e}")
        else:
            # Adaugă imaginea implicită ca featured
            default_image_path = FileService.get_default_blog_image()
            await BlogService.add_image(
                db=db,
                post_id=post.id,
                image_path=default_image_path,
                file_name="blog_default.png",
                file_size=0,  # Poți calcula dimensiunea reală dacă e necesar
                alt_text=title,
                is_featured=True
            )

        return RedirectResponse(
            url=f"/dashboard/staff/post?success=created",
            status_code=303
        )

    except Exception as e:
        print(f"Error creating post: {e}")
        return RedirectResponse(
            url="/dashboard/staff/post/create?error=true",
            status_code=303
        )


@post_router.get("/{post_id}/edit", response_class=HTMLResponse)
async def post_edit_form(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Formular editare articol."""
    # Get post with images
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.author),
            selectinload(Post.images)
        )
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Articol negăsit")

    # Check permission
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403, detail="Nu aveți permisiune de editare")

    # Get featured image
    post.featured_image = next(
        (img for img in post.images if img.is_featured),
        None
    )

    # Get content images (non-featured)
    post.content_images = [img for img in post.images if not img.is_featured]

    context = await get_template_context(request, staff, db)
    context.update({
        "post": post,
        "action": "edit",
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error")
    })

    return templates.TemplateResponse(
        "post/form.html",
        context
    )


@post_router.post("/{post_id}/edit")
async def post_update(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        title: str = Form(...),
        content: str = Form(...),
        excerpt: Optional[str] = Form(None),
        meta_title: str = Form(...),
        meta_description: str = Form(...),
        is_featured: bool = Form(False),
        is_active: bool = Form(False),
        featured_image: Optional[UploadFile] = File(None),
        regenerate_slug: bool = Form(False)
):
    """Actualizează articol."""
    # Check permission
    if staff.role == StaffRole.SUPERVISOR:
        raise HTTPException(status_code=403, detail="Nu aveți permisiune de editare")

    # Get post
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Articol negăsit")

    try:
        # Update fields
        post.title = title
        post.content = content
        post.excerpt = excerpt
        post.meta_title = meta_title
        post.meta_description = meta_description
        post.is_featured = is_featured

        # Only super_admin can publish
        if staff.role == StaffRole.SUPER_ADMIN:
            post.is_active = is_active

        # Regenerate slug if requested
        if regenerate_slug:
            new_slug = slugify(title)
            if new_slug != post.slug:
                # Check if new slug exists
                existing = await db.execute(
                    select(Post).where(
                        and_(
                            Post.slug == new_slug,
                            Post.id != post_id
                        )
                    )
                )
                if not existing.scalar_one_or_none():
                    post.slug = new_slug

        # Handle featured image upload
        if featured_image and featured_image.filename:
            try:
                # Remove old featured image if exists (but not if it's the default)
                old_featured = await db.execute(
                    select(PostImage).where(
                        and_(
                            PostImage.post_id == post_id,
                            PostImage.is_featured == True
                        )
                    )
                )
                for old_img in old_featured.scalars().all():
                    # Don't delete the default image file
                    if "blog_default.png" not in old_img.image_path:
                        FileService.delete_image(old_img.image_path)
                    await db.delete(old_img)

                # Save new image
                image_path, file_name, file_size = await FileService.save_blog_image(
                    featured_image,
                    post.slug
                )

                # Add as featured
                await BlogService.add_image(
                    db=db,
                    post_id=post.id,
                    image_path=image_path,
                    file_name=file_name,
                    file_size=file_size,
                    alt_text=title,
                    is_featured=True
                )
            except Exception as e:
                print(f"Error updating featured image: {e}")

        await db.commit()

        return RedirectResponse(
            url=f"/dashboard/staff/post/{post_id}/edit?success=updated",
            status_code=303
        )

    except Exception as e:
        print(f"Error updating post: {e}")
        await db.rollback()
        return RedirectResponse(
            url=f"/dashboard/staff/post/{post_id}/edit?error=true",
            status_code=303
        )


@post_router.post("/{post_id}/toggle-featured")
async def post_toggle_featured(
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Toggle featured status."""
    if staff.role not in [StaffRole.SUPER_ADMIN, StaffRole.MANAGER]:
        raise HTTPException(status_code=403)

    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404)

    post.is_featured = not post.is_featured
    await db.commit()

    return JSONResponse({
        "success": True,
        "is_featured": post.is_featured
    })


@post_router.post("/{post_id}/toggle-active")
async def post_toggle_active(
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Toggle active status (publish/unpublish)."""
    # Only super_admin can publish
    if staff.role != StaffRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Doar Super Admin poate publica")

    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404)

    post.is_active = not post.is_active
    await db.commit()

    return JSONResponse({
        "success": True,
        "is_active": post.is_active
    })


@post_router.get("/{post_id}/preview", response_class=HTMLResponse)
async def post_preview(
        request: Request,
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff),
        modal: bool = Query(False)
):
    """Preview articol - poate fi afișat în pagină separată sau modal."""
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.author),
            selectinload(Post.images)
        )
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404)

    # Get featured image
    post.featured_image = next(
        (img for img in post.images if img.is_featured),
        None
    )

    # Dacă e pentru modal, returnăm doar conținutul
    if modal:
        context = {
            "request": request,
            "post": post,
            "date_only": date_only,
            "datetime_local": datetime_local
        }
        return templates.TemplateResponse(
            "post/preview_modal.html",
            context
        )

    # Altfel, returnăm pagina completă
    context = await get_template_context(request, staff, db)
    context.update({
        "post": post
    })

    return templates.TemplateResponse(
        "post/preview.html",
        context
    )

@post_router.post("/{post_id}/delete")
async def post_delete(
        post_id: int,
        db: AsyncSession = Depends(get_db),
        staff: Staff = Depends(get_current_staff)
):
    """Șterge articol (doar super_admin)."""
    if staff.role != StaffRole.SUPER_ADMIN:
        raise HTTPException(status_code=403)

    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.images))
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404)

    # Delete all images (but not the default image file)
    for image in post.images:
        if "blog_default.png" not in image.image_path:
            FileService.delete_image(image.image_path)

    # Delete post (cascade will delete PostImages)
    await db.delete(post)
    await db.commit()

    return RedirectResponse(
        url="/dashboard/staff/post?success=deleted",
        status_code=303
    )

