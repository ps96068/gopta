# services/models/category_services.py


from __future__ import annotations
from typing import Optional, List, Dict
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from models import Category, Product


class CategoryService:
    """Service pentru gestionarea categoriilor."""

    @staticmethod
    async def get_tree(db: AsyncSession) -> List[Category]:
        """Returnează arborele de categorii."""
        result = await db.execute(
            select(Category)
            .where(Category.parent_id == None)
            .where(Category.is_active == True)
            .options(selectinload(Category.children))
            .order_by(Category.sort_order)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Category]:
        """Găsește categorie după slug."""
        result = await db.execute(
            select(Category)
            .where(Category.slug == slug)
            .where(Category.is_active == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_categories_with_counts(db: AsyncSession):
        subq = (
            select(Product.category_id, func.count(Product.id).label('product_count'))
            .group_by(Product.category_id)
            .subquery()
        )

        query = (
            select(Category, subq.c.product_count)
            .outerjoin(subq, Category.id == subq.c.category_id)
            .where(Category.is_active == True)
        )

