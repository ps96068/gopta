# schemas/sale/invoice.py
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

from models.sale import Order, OrderItem


class InvoiceBase(BaseModel):
    """Schema de bază pentru Invoice."""
    client_name: str = Field(..., min_length=2, max_length=255)
    client_email: EmailStr
    client_phone: Optional[str] = Field(None, max_length=20)
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="MDL", pattern=r'^[A-Z]{3}$')


class InvoiceCreate(BaseModel):
    """Schema pentru generare invoice din order."""
    order_id: int = Field(..., gt=0)

    # Override date client dacă e necesar
    override_client_name: Optional[str] = None
    override_client_email: Optional[EmailStr] = None
    override_client_phone: Optional[str] = None

    # Opțiuni generare
    send_immediately: bool = Field(default=True)
    send_via: str = Field(default="both", pattern=r'^(telegram|email|both)$')


class InvoiceManualCreate(InvoiceBase):
    """Schema pentru creare invoice manuală (fără order)."""
    invoice_items: List[dict] = Field(..., min_items=1)
    # Format: [{"description": "...", "quantity": 1, "unit_price": 100, "subtotal": 100}]

    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('invoice_items')
    def validate_items(cls, v):
        """Validează structura items."""
        total = Decimal("0")
        for item in v:
            required = ['description', 'quantity', 'unit_price', 'subtotal']
            if not all(k in item for k in required):
                raise ValueError(f'Item trebuie să conțină: {", ".join(required)}')

            # Verifică calculul
            expected = Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
            if abs(expected - Decimal(str(item['subtotal']))) > Decimal("0.01"):
                raise ValueError('Subtotal incorect pentru unul din items')

            total += Decimal(str(item['subtotal']))

        return v


class InvoiceResponse(InvoiceBase):
    """Schema pentru răspuns invoice."""
    id: int
    invoice_number: str

    # Trimitere
    sent_at: Optional[datetime]
    sent_via: Optional[str]

    # Document
    document_path: Optional[str]

    # Timestamps
    created_at: datetime

    # Relații
    order_id: Optional[int] = None
    order_number: Optional[str] = None

    # Status calculat
    is_sent: bool = False
    days_since_created: Optional[int] = None
    document_exists: bool = False

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.is_sent = self.sent_at is not None
        self.document_exists = bool(self.document_path)

        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            self.days_since_created = delta.days


class InvoiceSend(BaseModel):
    """Schema pentru trimitere/retrimitere invoice."""
    invoice_id: int = Field(..., gt=0)
    send_via: str = Field(..., pattern=r'^(telegram|email|both)$')

    # Pentru email
    custom_subject: Optional[str] = None
    custom_message: Optional[str] = None

    # Pentru Telegram
    include_preview: bool = Field(default=True)


class InvoiceListResponse(BaseModel):
    """Schema pentru listă facturi."""
    items: List[InvoiceResponse]
    total: int
    page: int
    per_page: int

    # Stats
    total_amount: Decimal = Decimal("0.00")
    sent_count: int = 0
    pending_count: int = 0


class InvoiceFilter(BaseModel):
    """Schema pentru filtrare facturi."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_sent: Optional[bool] = None
    client_email: Optional[str] = None
    invoice_number: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class InvoiceGenerateOptions(BaseModel):
    """Schema pentru opțiuni generare PDF."""
    template: str = Field(default="default", pattern=r'^(default|detailed|simple)$')
    language: str = Field(default="ro", pattern=r'^(ro|ru|en)$')

    # Afișare
    show_product_images: bool = True
    show_payment_details: bool = True
    show_company_details: bool = True

    # Footer
    footer_text: Optional[str] = Field(None, max_length=200)
    terms_text: Optional[str] = Field(None, max_length=500)


class InvoiceBulkAction(BaseModel):
    """Schema pentru acțiuni bulk pe facturi."""
    invoice_ids: List[int] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern=r'^(send|regenerate|download)$')

    # Pentru send
    send_via: Optional[str] = Field(default="email", pattern=r'^(telegram|email|both)$')

    @field_validator('invoice_ids')
    def validate_unique(cls, v):
        """Verifică ID-uri unice."""
        if len(v) != len(set(v)):
            raise ValueError('ID-urile trebuie să fie unice')
        return v