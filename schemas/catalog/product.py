# schemas/catalog/product.py
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


from models import UserStatus


class ProductBase(BaseModel):
    """Schema de bază pentru Product."""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    in_stock: bool = Field(default=True)
    stock_quantity: Optional[int] = Field(default=0, ge=0)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    """Schema pentru creare produs."""
    vendor_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    slug: str = Field(..., pattern=r'^[a-z0-9\-]+$')
    sku: str = Field(..., min_length=3, max_length=100)

    @field_validator('sku')
    def validate_sku(cls, v):
        """Validează SKU format."""
        return v.upper().strip()

    @field_validator('slug')
    def validate_slug(cls, v):
        """Validează slug format."""
        return v.lower().strip()


class ProductUpdate(BaseModel):
    """Schema pentru actualizare produs."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    category_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = Field(None, ge=0)


class ProductImageResponse(BaseModel):
    """Schema pentru răspuns imagine produs."""
    id: int
    image_path: str
    file_name: str
    file_size: int
    alt_text: Optional[str]
    is_primary: bool
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(ProductBase):
    """Schema pentru răspuns produs."""
    id: int
    vendor_id: int
    vendor_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    slug: str
    sku: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    images: List[ProductImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Schema pentru listă produse cu paginare."""
    items: List[ProductResponse]
    total: int
    page: int = 1
    per_page: int = 20


class ProductSearchParams(BaseModel):
    """Schema pentru parametri căutare produse."""
    query: Optional[str] = Field(None, min_length=2)
    category_id: Optional[int] = None
    vendor_id: Optional[int] = None
    in_stock_only: bool = True
    sort_by: str = Field(default="sort_order", pattern=r'^(name|created_at|sort_order)$')
    sort_desc: bool = False
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)