from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from models.catalog.product_price import PriceType




class ProductPriceHistoryRead(BaseModel):
    id: int
    product_id: int
    price_id: int
    price_type: PriceType

    old_usd: Decimal
    new_usd: Decimal
    old_mdl: Decimal
    new_mdl: Decimal
    rate_used: Decimal
    stale_days: int | None = None

    changed_by: int
    created_at: datetime

    class Config:
        from_attributes = True