from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field
from models.catalog.product_price import PriceType


# ---------- Base ----------
class OrderItemBase(BaseModel):
    order_id: int
    product_id: int
    quantity: int = Field(..., gt=0)

    price_usd_snapshot: Decimal = Field(..., gt=0)
    price_mdl_snapshot: Decimal = Field(..., gt=0)
    rate_used: Decimal = Field(..., gt=0)
    price_type_snapshot: PriceType


# ---------- Create ----------
class OrderItemCreate(OrderItemBase):
    """
    DTO folosit la adăugarea item-ului într-o comandă.
    """


# ---------- Read ----------
class OrderItemRead(OrderItemBase):
    id: int
    created_at: datetime

    # totaluri calculate pentru afișare
    total_price_usd: Decimal
    total_price_mdl: Decimal

    class Config:
        from_attributes = True