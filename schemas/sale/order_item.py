# schemas/sale/order_item.py
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, computed_field


class OrderItemBase(BaseModel):
    """Schema de bază pentru OrderItem."""
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    price_type: str = Field(..., max_length=20)


class OrderItemCreate(OrderItemBase):
    """Schema pentru creare order item (intern, din cart)."""
    order_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    product_name: str = Field(..., min_length=1, max_length=255)
    product_sku: str = Field(..., min_length=1, max_length=100)
    vendor_id: int = Field(..., gt=0)

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        """Calculează subtotal automat."""
        return self.unit_price * self.quantity


class OrderItemResponse(OrderItemBase):
    """Schema pentru răspuns order item."""
    id: int
    order_id: int
    product_id: int
    product_name: str
    product_sku: str
    subtotal: Decimal
    vendor_id: int
    created_at: datetime

    # Joined data
    vendor_name: Optional[str] = None
    product_image: Optional[str] = None

    # Calculat
    is_available: bool = True  # Pentru re-order
    current_price: Optional[Decimal] = None  # Prețul actual al produsului
    price_difference: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class OrderItemsByVendor(BaseModel):
    """Schema pentru grupare items pe vendor."""
    vendor_id: int
    vendor_name: str
    vendor_email: str
    items: List[OrderItemResponse]
    items_count: int
    total_amount: Decimal

    # Pentru procesare
    notification_sent: bool = False
    processed: bool = False


class OrderItemsExport(BaseModel):
    """Schema pentru export items (CSV/Excel)."""
    order_number: str
    order_date: datetime
    client_name: str
    product_sku: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    vendor_name: str
    status: str


class VendorOrderSummary(BaseModel):
    """Schema pentru sumar comenzi per vendor."""
    vendor_id: int
    vendor_name: str
    period: str  # "today", "week", "month"

    # Metrici
    total_orders: int
    total_items: int
    total_revenue: Decimal
    unique_products: int
    unique_clients: int

    # Top products
    top_products: List[dict] = Field(default_factory=list)
    # [{"product_id": 1, "name": "...", "quantity": 10, "revenue": 1000}]


class OrderItemReorder(BaseModel):
    """Schema pentru re-comandă produse."""
    order_id: int = Field(..., gt=0)
    item_ids: Optional[List[int]] = None  # None = toate, altfel doar selectate

    # Rezultat validare
    can_reorder: bool = True
    unavailable_items: List[int] = Field(default_factory=list)
    price_changed_items: List[dict] = Field(default_factory=list)