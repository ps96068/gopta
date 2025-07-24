# schemas/analytics/user_request.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models import RequestType
from models import UserStatus


class UserRequestBase(BaseModel):
    """Schema de bază pentru UserRequest."""
    message: str = Field(..., min_length=10, max_length=2000)


class UserRequestCreate(UserRequestBase):
    """Schema pentru creare cerere utilizator."""
    request_type: RequestType

    # Referințe opționale (unul dintre acestea)
    product_id: Optional[int] = Field(None, gt=0)
    cart_id: Optional[int] = Field(None, gt=0)
    order_id: Optional[int] = Field(None, gt=0)

    @model_validator(mode='after')
    def validate_reference(self):
        """Verifică că are cel puțin o referință pentru anumite tipuri."""
        if self.request_type == RequestType.PRICE_REQUEST:
            if not any([self.product_id, self.cart_id]):
                raise ValueError('PRICE_REQUEST necesită product_id sau cart_id')
        elif self.request_type == RequestType.BULK_ORDER:
            if not self.product_id:
                raise ValueError('BULK_ORDER necesită product_id')
        return self

    @field_validator('message')
    def clean_message(cls, v):
        """Curăță și validează mesajul."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError('Mesajul trebuie să aibă minim 10 caractere')
        return v


class UserRequestQuickCreate(BaseModel):
    """Schema pentru creare rapidă din UI."""
    product_id: int = Field(..., gt=0)
    template: str = Field(..., pattern=r'^(price|bulk|info|custom)$')

    # Pentru template bulk
    quantity: Optional[int] = Field(None, gt=0)

    # Pentru custom
    custom_message: Optional[str] = Field(None, min_length=10)

    @model_validator(mode='after')
    def generate_message(self):
        """Generează mesaj bazat pe template."""
        if self.template == 'custom' and not self.custom_message:
            raise ValueError('Template custom necesită custom_message')
        if self.template == 'bulk' and not self.quantity:
            raise ValueError('Template bulk necesită quantity')
        return self


class UserRequestResponse(UserRequestBase):
    """Schema pentru răspuns cerere."""
    id: int
    client_id: int
    request_type: RequestType

    # Referințe
    product_id: Optional[int]
    cart_id: Optional[int]
    order_id: Optional[int]

    # Status
    is_processed: bool
    processed_at: Optional[datetime]

    # Timestamps
    created_at: datetime

    # Date joined
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_status: Optional[UserStatus] = None

    # Produs info (dacă există)
    product_name: Optional[str] = None
    product_sku: Optional[str] = None

    # Calculat
    response_count: int = 0
    days_since_request: Optional[int] = None
    priority: str = "normal"  # "low", "normal", "high", "urgent"

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Calculează zile
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            self.days_since_request = delta.days

            # Setează prioritate bazat pe timp și status
            if not self.is_processed:
                if delta.days >= 3:
                    self.priority = "urgent"
                elif delta.days >= 1:
                    self.priority = "high"
                elif self.client_status in [UserStatus.INSTALATOR, UserStatus.PRO]:
                    self.priority = "high"


class UserRequestListResponse(BaseModel):
    """Schema pentru listă cereri."""
    items: List[UserRequestResponse]
    total: int
    page: int
    per_page: int

    # Stats
    unprocessed_count: int = 0
    urgent_count: int = 0
    by_type: dict = Field(default_factory=dict)


class UserRequestFilter(BaseModel):
    """Schema pentru filtrare cereri."""
    is_processed: Optional[bool] = None
    request_type: Optional[RequestType] = None
    client_id: Optional[int] = None
    product_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern=r'^(low|normal|high|urgent)$')
    has_responses: Optional[bool] = None

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern=r'^(created_at|priority)$')
    sort_desc: bool = True


class UserRequestStats(BaseModel):
    """Schema pentru statistici cereri."""
    period: str  # "today", "week", "month"

    # Volume
    total_requests: int
    processed_requests: int
    pending_requests: int

    # Response time
    avg_response_hours: float
    fastest_response_hours: float
    slowest_response_hours: float

    # By type
    by_type: dict
    by_client_status: dict

    # Top
    top_products: List[dict]  # [{"product_id": 1, "name": "...", "count": 5}]
    most_active_clients: List[dict]