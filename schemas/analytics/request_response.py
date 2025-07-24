# schemas/analytics/request_response.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RequestResponseBase(BaseModel):
    """Schema de bază pentru RequestResponse."""
    message: str = Field(..., min_length=5, max_length=3000)


class RequestResponseCreate(RequestResponseBase):
    """Schema pentru creare răspuns la cerere."""
    request_id: int = Field(..., gt=0)
    sent_via: Optional[str] = Field(default="telegram", pattern=r'^(telegram|email|phone|internal)$')

    # Opțiuni notificare
    notify_client: bool = Field(default=True)
    mark_as_processed: bool = Field(default=True)

    # Template răspuns
    use_template: Optional[str] = None
    template_variables: Optional[dict] = None

    @field_validator('message')
    def clean_message(cls, v):
        """Curăță mesajul."""
        return v.strip()


class RequestResponseQuickCreate(BaseModel):
    """Schema pentru răspuns rapid cu template."""
    request_id: int = Field(..., gt=0)
    template: str = Field(..., pattern=r'^(price_info|bulk_discount|out_of_stock|custom_order|need_info)$')

    # Variabile pentru template
    price: Optional[float] = None
    discount_percent: Optional[int] = None
    availability_date: Optional[datetime] = None
    additional_info: Optional[str] = None

    # Override template
    custom_message: Optional[str] = None

    def generate_message(self) -> str:
        """Generează mesaj din template."""
        templates = {
            'price_info': f"Prețul solicitat este {self.price} MDL. {self.additional_info or ''}",
            'bulk_discount': f"Pentru cantități mari oferim discount de {self.discount_percent}%. Contactați-ne pentru detalii.",
            'out_of_stock': f"Produsul nu este în stoc momentan. Disponibil din {self.availability_date.strftime('%d.%m.%Y') if self.availability_date else 'data necunoscută'}.",
            'custom_order': "Putem realiza comanda personalizată. Vă rugăm să ne oferiți mai multe detalii.",
            'need_info': f"Pentru a vă oferi o ofertă, avem nevoie de informații suplimentare: {self.additional_info or 'cantitate exactă, termen livrare'}"
        }

        if self.custom_message:
            return self.custom_message

        return templates.get(self.template, "Vă mulțumim pentru cerere. Vă vom contacta în curând.")


class RequestResponseUpdate(BaseModel):
    """Schema pentru actualizare răspuns."""
    message: Optional[str] = Field(None, min_length=5, max_length=3000)
    sent_via: Optional[str] = Field(None, pattern=r'^(telegram|email|phone|internal)$')


class RequestResponseResponse(RequestResponseBase):
    """Schema pentru răspuns response (meta!)."""
    id: int
    request_id: int
    staff_id: int
    sent_via: Optional[str]
    created_at: datetime

    # Staff info
    staff_name: Optional[str] = None
    staff_role: Optional[str] = None

    # Status
    client_notified: bool = True
    notification_sent_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RequestWithResponses(BaseModel):
    """Schema pentru cerere cu toate răspunsurile."""
    request_id: int
    request_type: str
    message: str
    created_at: datetime
    is_processed: bool

    # Client info
    client_name: str
    client_email: Optional[str]
    client_phone: Optional[str]

    # Responses
    responses: List[RequestResponseResponse] = []
    response_count: int = 0
    last_response_at: Optional[datetime] = None

    # Thread view
    conversation_thread: List[dict] = []
    # [{"type": "request/response", "message": "...", "author": "...", "timestamp": "..."}]


class ResponseTemplate(BaseModel):
    """Schema pentru template-uri răspuns."""
    id: Optional[int] = None
    name: str = Field(..., min_length=3, max_length=100)
    template_key: str = Field(..., pattern=r'^[a-z_]+$')
    content: str = Field(..., min_length=10, max_length=1000)
    variables: List[str] = Field(default_factory=list)
    category: str = Field(..., pattern=r'^(price|stock|order|general)$')
    is_active: bool = True

    # Usage stats
    usage_count: int = 0
    last_used_at: Optional[datetime] = None


class StaffResponseStats(BaseModel):
    """Schema pentru statistici răspunsuri per staff."""
    staff_id: int
    staff_name: str
    period: str

    # Volume
    total_responses: int
    avg_responses_per_day: float

    # Speed
    avg_response_time_hours: float
    fastest_response_minutes: int

    # Quality
    templates_used: int
    custom_responses: int

    # By channel
    by_channel: dict  # {"telegram": 10, "email": 5}