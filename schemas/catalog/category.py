from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field





class CategoryBase(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    is_unknown: bool = False
    image_path: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None
    is_unknown: bool | None = None
    image_path: str | None = None

class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True