# models/catalog/category.py
"""
Category model pentru organizarea produselor.

Categoriile sunt globale (nu aparțin unui vendor specific) și reprezintă
modalitatea principală de organizare a produselor pe platformă.

În MVP avem doar categorii de nivel 1 (fără ierarhie).
Post-MVP se poate extinde cu categorii parent-child.

Business Rules:
- Categoriile pot fi create doar de super_admin și manager
- Fiecare categorie are o imagine (default dacă nu se specifică)
- Slug unic generat automat pentru URL-uri
- Un produs poate aparține unei singure categorii
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING


from sqlalchemy import String, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Category, Product


class Category(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru categorii de produse."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Imagine categorie
    image_path: Mapped[str] = mapped_column(String(500), default="static/webapp/img/category/cat_default.png")

    # Pentru ierarhie (categorie părinte)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    # Ordine afișare
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(back_populates="children", remote_side="Category.id")
    children: Mapped[List["Category"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship(back_populates="category", cascade="all, delete-orphan")

