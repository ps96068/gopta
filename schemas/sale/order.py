# schemas/sale/order.py
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import OrderStatus


class OrderBase(BaseModel):
    """Schema de bază pentru Order."""
    client_note: Optional[str] = Field(None, max_length=1000)


class OrderCreate(OrderBase):
    """Schema pentru creare comandă din cart."""
    cart_id: int = Field(..., gt=0)

    @field_validator('client_note')
    def sanitize_note(cls, v):
        """Curăță nota de caractere nedorite."""
        if v:
            return v.strip()[:1000]
        return v


class OrderStatusUpdate(BaseModel):
    """Schema pentru actualizare status comandă."""
    status: OrderStatus
    staff_note: Optional[str] = Field(None, max_length=1000)
    notify_client: bool = Field(default=True)


class OrderResponse(OrderBase):
    """Schema pentru răspuns comandă."""
    id: int
    client_id: int
    order_number: str
    status: OrderStatus
    total_amount: Decimal
    currency: str

    # Staff info
    processed_by_id: Optional[int]
    processed_at: Optional[datetime]
    staff_note: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Client info (joined)
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_telegram_id: Optional[int] = None

    # Status calculat
    is_completed: bool = False
    is_cancelled: bool = False
    days_since_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Calculează status flags
        self.is_completed = self.status == OrderStatus.COMPLETED
        self.is_cancelled = self.status == OrderStatus.CANCELLED
        # Calculează zile de la comandă
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            self.days_since_order = delta.days


class OrderListResponse(BaseModel):
    """Schema pentru listă comenzi cu paginare."""
    items: List[OrderResponse]
    total: int
    page: int
    per_page: int

    # Statistici
    total_amount: Decimal = Decimal("0.00")
    by_status: dict = Field(default_factory=dict)


class OrderFilter(BaseModel):
    """Schema pentru filtrare comenzi."""
    status: Optional[OrderStatus] = None
    client_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    order_number: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern="^(created_at|total_amount|order_number)$")
    sort_desc: bool = True


class OrderDashboardStats(BaseModel):
    """Schema pentru statistici dashboard."""
    period: str  # "today", "week", "month"
    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal

    # Pe status
    new_orders: int
    processing_orders: int
    completed_orders: int
    cancelled_orders: int

    # Trend
    orders_change_percent: float  # vs perioada anterioară
    revenue_change_percent: float

    # Top metrics
    top_client_id: Optional[int]
    top_vendor_id: Optional[int]
    busiest_hour: Optional[int]  # 0-23