from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field
from models.sale.order import OrderStatus          # Enum
# from schemas.sale.order_item import OrderItemRead  # dacă vrei nested read


# ---------- Base ----------
class OrderBase(BaseModel):
    client_id: int
    status: OrderStatus = OrderStatus.pending

    # snapshot totals
    total_usd: Decimal = Field(..., gt=0)
    total_mdl: Decimal = Field(..., gt=0)
    currency_rate_used: Decimal = Field(..., gt=0)

    # snapshot contact
    client_username: str
    client_phone: str
    client_email: str

    # optional
    cancel_reason: str | None = None
    invoice_qr_path: str | None = None


# ---------- Create ----------
class OrderCreate(OrderBase):
    """
    DTO folosit la crearea comenzii din frontend / bot.
    items va conține DTO-urile OrderItemCreate.
    """
    items: List[int]  # listă de (product_id, quantity) sau un DTO propriu


# ---------- Update ----------
class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    cancel_reason: str | None = None
    invoice_qr_path: str | None = None


# ---------- Read ----------
class OrderRead(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    created_by: int | None = None
    modified_by: int | None = None

    # items: List[OrderItemRead]  # de-comentează dacă vrei nested

    class Config:
        from_attributes = True
