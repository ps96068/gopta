# models/catalog/product_price.py
"""
ProductPrice model pentru prețurile produselor.

Fiecare produs are exact un set de prețuri active cu 4 nivele:
- anonim: pentru vizitatori neînregistrați
- user: pentru clienți înregistrați
- instalator: pentru instalatori (setat manual de staff)
- pro: pentru profesioniști (setat manual de staff)

Business Rules:
- Un produs are un singur set de prețuri activ
- Toate cele 4 prețuri sunt obligatorii
- TVA este inclus în preț (doar informativ)
- Prețurile sunt afișate condiționat pe front bazat pe price_type al clientului
- În MVP nu păstrăm istoric prețuri
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Enum as SQLAlchemyEnum

from sqlalchemy import Numeric, String, Boolean, ForeignKey, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models.enum import PriceType

if TYPE_CHECKING:
    from models import Product


class ProductPrice(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru prețurile produselor pe grile."""
    __tablename__ = "product_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    price_type: Mapped[PriceType] = mapped_column(SQLAlchemyEnum(PriceType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Valută (pentru extindere viitoare)
    currency: Mapped[str] = mapped_column(String(3), default="MDL", nullable=False)


    # Relationships
    product: Mapped["Product"] = relationship(back_populates="prices")


