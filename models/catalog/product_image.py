# models/catalog/product_image.py
"""
ProductImage model pentru imaginile produselor.

Fiecare produs poate avea maxim 4 imagini, dintre care una este principală.
Imaginile sunt stocate local în directorul static și sunt șterse fizic
când înregistrarea este ștearsă din baza de date.

Business Rules:
- Maxim 4 imagini per produs
- O singură imagine poate fi marcată ca principală
- Formaturi acceptate: jpg, jpeg, png
- Dimensiune maximă: 2MB
- Ștergerea din BD implică ștergerea fizică a fișierului
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import os
import re
from pathlib import Path

from sqlalchemy import String, Integer, Boolean, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from .product import Product


class ProductImage(Base, CreatedAtMixin):
    """Model pentru imaginile produselor."""
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    # Path către imagine
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # în bytes

    alt_text: Mapped[Optional[str]] = mapped_column(String(255))

    # Pentru ordonare
    is_primary: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="images")


