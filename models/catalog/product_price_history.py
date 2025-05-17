from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Enum, Integer, String, ForeignKey, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import CreatedAtMixin, UpdatedAtMixin



# models/catalog/product_price_history.py


from models.catalog.product_price import PriceType


class ProductPriceHistory(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "product_price_history"
    __table_args__ = (
        Index("ix_price_history_prod_type_time", "product_id", "price_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price_id: Mapped[int] = mapped_column(
        ForeignKey("product_prices.id", ondelete="CASCADE"), nullable=False
    )
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)

    old_usd: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    new_usd: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    old_mdl: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    new_mdl: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    rate_used: Mapped[Decimal] = mapped_column(Numeric(10,4), nullable=False)
    stale_days: Mapped[int | None] = mapped_column(Integer)

    changed_by: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)



    price: Mapped["ProductPrice"] = relationship("ProductPrice", back_populates="histories")
    product: Mapped["Product"] = relationship("Product", foreign_keys=[product_id])
    staff: Mapped["Staff"] = relationship("Staff")

    @validates("old_usd","new_usd","old_mdl","new_mdl","rate_used")
    def ensure_positive(self, key, value: Decimal):
        if value < 0:
            raise ValueError(f"{key} trebuie să fie pozitiv")
        return value
