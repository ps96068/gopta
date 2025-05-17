from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Enum, Integer, String, ForeignKey, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import CreatedAtMixin




# models/catalog/product_price.py


class PriceType(enum.Enum):
    anonim = "anonim"
    user = "user"
    instalator = "instalator"
    pro = "pro"


class ProductPrice(Base, CreatedAtMixin):
    __tablename__ = "product_prices"
    __table_args__ = (
        UniqueConstraint('product_id', 'price_type', name='uix_product_price_type'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)

    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_mdl: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rate_used: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Relații
    histories: Mapped[list["ProductPriceHistory"]] = relationship("ProductPriceHistory", back_populates="price")

    product_price_author: Mapped["Staff"] = relationship("Staff", foreign_keys=[author_id],
                                                         back_populates="product_prices")
    product: Mapped["Product"] = relationship("Product", back_populates="prices")




    @validates("price_usd", "price_mdl", "rate_used")
    def validate_price(self, key, value: Decimal):
        if value < 0:
            raise ValueError("Prețul trebuie să fie pozitiv.")
        return value
