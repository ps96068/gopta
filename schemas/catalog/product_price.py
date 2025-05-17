from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from models.catalog.product_price import PriceType


class ProductPriceBase(BaseModel):
    product_id: int
    price_type: PriceType
    price_usd: Decimal
    price_mdl: Decimal
    rate_used: Decimal

class ProductPriceCreate(ProductPriceBase):
    pass

class ProductPriceUpdate(BaseModel):
    price_usd: Decimal | None = None
    price_mdl: Decimal | None = None
    rate_used: Decimal | None = None

class ProductPriceRead(ProductPriceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True