from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field



class ProductBase(BaseModel):
    cod_produs: int | None = None
    name: str
    description: str | None = None
    datasheet_url: str | None = None
    category_id: int | None = None
    is_active: bool = True
    publish_date: datetime | None = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    cod_produs: int | None = None
    name: str | None = None
    description: str | None = None
    datasheet_url: str | None = None
    category_id: int | None = None
    is_active: bool | None = None
    publish_date: datetime | None = None

class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True