# schemas/aale/cart_item.py
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import UserStatus


class CartItemBase(BaseModel):
    """Schema de bază pentru CartItem."""
    quantity: int = Field(..., gt=0)


class CartItemAdd(CartItemBase):
    """Schema pentru adăugare produs în coș."""
    product_id: int = Field(..., gt=0)

    @field_validator('quantity')
    def validate_quantity(cls, v):
        """Validează cantitate rezonabilă."""
        if v > 999:
            raise ValueError('Cantitate prea mare. Maxim 999')
        return v


class CartItemUpdate(BaseModel):
    """Schema pentru actualizare cantitate."""
    quantity: int = Field(..., gt=0, le=999)


class CartItemResponse(CartItemBase):
    """Schema pentru răspuns cart item."""
    id: int
    cart_id: int
    product_id: int
    price_snapshot: Decimal
    price_type: str
    created_at: datetime
    updated_at: datetime

    # Date produs (joined)
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    product_slug: Optional[str] = None
    product_image: Optional[str] = None  # Prima imagine

    # Calculat
    subtotal: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Calculează subtotal
        if self.price_snapshot and self.quantity:
            self.subtotal = self.price_snapshot * self.quantity


class CartItemBulkAdd(BaseModel):
    """Schema pentru adăugare multiplă produse."""
    items: List[CartItemAdd] = Field(..., min_items=1, max_items=50)

    @field_validator('items')
    def validate_unique_products(cls, v):
        """Verifică duplicate."""
        product_ids = [item.product_id for item in v]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError('Nu se permit produse duplicate în bulk add')
        return v


class CartItemMoveToWishlist(BaseModel):
    """Schema pentru mutare în wishlist (pentru viitor)."""
    cart_item_id: int = Field(..., gt=0)
    create_wishlist_item: bool = True


class CartValidation(BaseModel):
    """Schema pentru validare cart înainte de checkout."""
    cart_id: int
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Detalii validare
    out_of_stock_items: List[int] = Field(default_factory=list)
    price_changed_items: List[dict] = Field(default_factory=list)
    minimum_not_met: bool = False


class CartItemPriceCheck(BaseModel):
    """Schema pentru verificare actualizare prețuri."""
    cart_item_id: int
    product_id: int
    old_price: Decimal
    new_price: Decimal
    price_difference: Decimal
    percentage_change: float

    model_config = ConfigDict(from_attributes=True)