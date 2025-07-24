# models/catalog/product.py
"""
Product model pentru produsele din catalog.

Produsele aparțin unui vendor (în MVP - System Vendor cu id=1).
Fiecare produs aparține unei singure categorii și poate avea până la 4 imagini.

Business Rules:
- SKU unic global (nu poate exista același SKU la vendori diferiți)
- Fiecare produs are exact un set de prețuri (4 nivele)
- Dacă nu are imagini, se folosește imaginea default
- URL-uri externe pentru informații suplimentare
- SEO optimizat cu meta tags
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
import re
from slugify import slugify

from sqlalchemy import String, Integer, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Category, Vendor, ProductImage, ProductPrice, CartItem, OrderItem



class Product(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru produse."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_company_id: Mapped[int] = mapped_column(
        ForeignKey("vendor_companies.id"),
        nullable=False,
        index=True
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    description: Mapped[Optional[str]] = mapped_column(Text)
    short_description: Mapped[Optional[str]] = mapped_column(String(500))

    # Stoc și disponibilitate
    in_stock: Mapped[bool] = mapped_column(default=True)
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # SEO și meta
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))

    # Ordine afișare
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    vendor_company: Mapped["VendorCompany"] = relationship(back_populates="products")
    category: Mapped["Category"] = relationship(back_populates="products")
    images: Mapped[List["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    prices: Mapped[List["ProductPrice"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product", cascade="all, delete-orphan")


