from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Enum, Integer, String, ForeignKey, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base


class PriceType(enum.Enum):
    anonim = "anonim"
    user = "user"
    instal = "instal"
    pro = "pro"


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id: Mapped[int] = mapped_column(primary_key=True)

    # new
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relații

    # new
    product_price_author: Mapped["Staff"] = relationship("Staff", foreign_keys=[author_id],
                                                         back_populates="product_prices")

    product: Mapped["Product"] = relationship("Product", back_populates="prices")


    __table_args__ = (
        UniqueConstraint('product_id', 'price_type', name='uix_product_price_type'),
        Index('idx_product_price_type', 'product_id', 'price_type')
    )

    @validates('price')
    def validate_price(self, key, value):
        if value < 0:
            raise ValueError("Prețul trebuie să fie un număr pozitiv")
        return value
