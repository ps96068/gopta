# schemas/sale/cart.py
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CartBase(BaseModel):
    """Schema de bază pentru Cart."""
    session_id: Optional[str] = Field(None, max_length=255)


class CartCreate(BaseModel):
    """Schema pentru creare cart (se creează automat la primul add)."""
    client_id: int = Field(..., gt=0)
    session_id: Optional[str] = Field(None, max_length=255)


class CartResponse(CartBase):
    """Schema pentru răspuns cart."""
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    # Calculat
    items_count: Optional[int] = 0
    total_amount: Optional[Decimal] = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class CartSummary(BaseModel):
    """Schema pentru sumar cart."""
    cart_id: int
    items_count: int
    unique_products: int
    total_amount: Decimal
    currency: str = "MDL"
    last_updated: datetime

    # Grupat pe status preț
    price_breakdown: dict = Field(default_factory=dict)
    # Ex: {"anonim": 2, "user": 1} - 2 produse cu preț anonim, 1 cu preț user


class CartClearResponse(BaseModel):
    """Schema pentru răspuns golire cart."""
    success: bool
    message: str
    cleared_items: int


class AbandonedCartFilter(BaseModel):
    """Schema pentru filtrare abandoned carts."""
    hours_since_update: int = Field(default=24, ge=1)
    has_items: bool = True
    client_status: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)