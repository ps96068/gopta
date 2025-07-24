# services/models/blog_service.py

from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.blog import Post, PostImage


class BlogService:
    """Service pentru gestionarea blog-ului."""

    @staticmethod
    async def create_post(
            db: AsyncSession,
            title: str,
            slug: str,
            content: str,
            author_id: int,
            excerpt: Optional[str] = None,
            is_featured: bool = False,
            **kwargs
    ) -> Post:
        """Creează articol nou."""
        post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            excerpt=excerpt,
            is_featured=is_featured,
            **kwargs
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post


    @staticmethod
    async def get_published(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 10,
            featured_only: bool = False
    ) -> List[Post]:
        """Obține articole publicate."""
        query = select(Post).where(Post.is_active == True)

        if featured_only:
            query = query.where(Post.is_featured == True)

        result = await db.execute(
            query
            .options(selectinload(Post.images))
            .order_by(Post.sort_order, Post.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


    @staticmethod
    async def get_by_slug(
            db: AsyncSession,
            slug: str,
            increment_views: bool = True
    ) -> Optional[Post]:
        """Găsește articol după slug."""
        result = await db.execute(
            select(Post)
            .where(Post.slug == slug)
            .where(Post.is_active == True)
            .options(selectinload(Post.images), selectinload(Post.author))
        )
        post = result.scalar_one_or_none()

        if post and increment_views:
            post.view_count += 1
            await db.commit()

        return post

    @staticmethod
    async def add_image(
            db: AsyncSession,
            post_id: int,
            image_path: str,
            file_name: str,
            file_size: int,
            alt_text: Optional[str] = None,
            caption: Optional[str] = None,
            is_featured: bool = False,
            sort_order: Optional[int] = None
    ) -> PostImage:
        """Adaugă imagine la articol."""
        # Dacă e featured, dezactivează alte featured
        if is_featured:
            result = await db.execute(
                select(PostImage)
                .where(PostImage.post_id == post_id)
                .where(PostImage.is_featured == True)
            )
            existing_featured = result.scalars().all()
            for img in existing_featured:
                img.is_featured = False

        image = PostImage(
            post_id=post_id,
            image_path=image_path,
            file_name=file_name,
            file_size=file_size,
            alt_text=alt_text,
            caption=caption,
            is_featured=is_featured,
            sort_order=sort_order or 0
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    @staticmethod
    async def delete_image(
            db: AsyncSession,
            image_id: int
    ) -> bool:
        """Șterge imagine articol (din DB și de pe disk)."""
        from services.file_service import FileService

        result = await db.execute(
            select(PostImage).where(PostImage.id == image_id)
        )
        image = result.scalar_one_or_none()

        if image:
            # Șterge fișierul fizic
            FileService.delete_image(image.image_path)

            # Șterge din DB
            await db.delete(image)
            await db.commit()
            return True

        return False


