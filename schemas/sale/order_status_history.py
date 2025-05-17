from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from models.sale.order import OrderStatus

class OrderStatusHistoryRead(BaseModel):
    id: int
    order_id: int
    old_status: OrderStatus
    new_status: OrderStatus
    changed_by: int
    reason: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True