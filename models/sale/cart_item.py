# models/sale/cart_item.py


from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from models import Cart, Product


class CartItem(Base, CreatedAtMixin, UpdatedAtMixin):
    """Model pentru produse în coș."""
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(Integer, ForeignKey("carts.id", ondelete='CASCADE'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Snapshot preț la momentul adăugării
    price_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)  # tip preț aplicat

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")

