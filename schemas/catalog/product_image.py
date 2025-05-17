from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field



class ProductImageBase(BaseModel):
    product_id: int
    image_path: str | None = None
    is_primary: bool = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageUpdate(BaseModel):
    image_path: str | None = None
    is_primary: bool | None = None

class ProductImageRead(ProductImageBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True