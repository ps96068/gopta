from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Enum, Integer, String, ForeignKey, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base

from .product_price import PriceType

class ProductPriceHistory(Base):
    __tablename__ = "product_price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product_price_id: Mapped[int] = mapped_column(
        ForeignKey("product_prices.id", ondelete="CASCADE"), nullable=False
    )
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    modified_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_by: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    product: Mapped["Product"] = relationship("Product")
    modified_by_author: Mapped["Staff"] = relationship("Staff")
    price: Mapped["ProductPrice"] = relationship("ProductPrice", back_populates="histories")