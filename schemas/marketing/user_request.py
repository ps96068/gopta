from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field

from models import RequestTypeEnum


class UserRequestBase(BaseModel):
    request_type: RequestTypeEnum = Field(..., description="Tipul cererii")
    request_details: str = Field(..., min_length=1, description="Detaliile cererii")
    product_id: int | None = Field(None, description="ID produs (dacă request_type='product')")
    order_id:   int | None = Field(None, description="ID comandă (dacă request_type='order')")


class UserRequestCreate(UserRequestBase):
    """Folosit la POST /user-requests"""


class UserRequestRead(UserRequestBase):
    id: int
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True