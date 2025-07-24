# schemas/notification/notification.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models import NotificationType, NotificationChannel, NotificationStatus


class NotificationBase(BaseModel):
    """Schema de bază pentru Notification."""
    notification_type: NotificationType
    channel: NotificationChannel
    message: str = Field(..., min_length=10, max_length=2000)
    subject: Optional[str] = Field(None, max_length=255)  # Pentru email


class NotificationCreate(NotificationBase):
    """Schema pentru creare notificare."""
    client_id: int = Field(..., gt=0)
    metadata: Optional[Dict] = None
    scheduled_for: Optional[datetime] = None

    # Retry settings
    max_retries: int = Field(default=3, ge=0, le=5)

    @field_validator('scheduled_for')
    def validate_schedule(cls, v):
        """Validează că e programată în viitor."""
        if v and v <= datetime.utcnow():
            raise ValueError('Notificarea trebuie programată în viitor')
        return v

    @model_validator(mode='after')
    def validate_email_subject(self):
        """Email necesită subject."""
        if self.channel in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
            if not self.subject:
                raise ValueError('Email notifications require subject')
        return self


class NotificationBulkCreate(BaseModel):
    """Schema pentru creare notificări bulk."""
    client_ids: List[int] = Field(..., min_items=1, max_items=1000)
    notification_type: NotificationType
    channel: NotificationChannel

    # Template
    message_template: str = Field(..., min_length=10)
    subject_template: Optional[str] = None

    # Variables per client
    personalization: Optional[Dict[int, Dict]] = None
    # Ex: {1: {"name": "Ion", "amount": 100}, 2: {"name": "Maria", "amount": 200}}

    # Schedule
    scheduled_for: Optional[datetime] = None
    stagger_minutes: int = Field(default=0, ge=0, le=60)  # Delay între notificări

    @field_validator('client_ids')
    def validate_unique_clients(cls, v):
        """Verifică clienți unici."""
        if len(v) != len(set(v)):
            raise ValueError('Client IDs must be unique')
        return v


class NotificationUpdate(BaseModel):
    """Schema pentru actualizare notificare (doar pending)."""
    message: Optional[str] = Field(None, min_length=10, max_length=2000)
    subject: Optional[str] = Field(None, max_length=255)
    scheduled_for: Optional[datetime] = None

    # Cancel
    cancel: bool = Field(default=False)


class NotificationResponse(NotificationBase):
    """Schema pentru răspuns notificare."""
    id: int
    client_id: int
    status: NotificationStatus
    created_at: datetime
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    max_retries: int

    # Client info
    client_name: Optional[str] = None
    client_telegram_id: Optional[int] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None

    # Calculat
    is_scheduled: bool = False
    can_retry: bool = False
    time_until_send: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)

        # Flags
        self.is_scheduled = bool(self.scheduled_for and not self.sent_at)
        self.can_retry = (
                self.status == NotificationStatus.FAILED and
                self.retry_count < self.max_retries
        )

        # Time until send
        if self.scheduled_for and self.status == NotificationStatus.PENDING:
            delta = self.scheduled_for - datetime.utcnow()
            if delta.total_seconds() > 0:
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                if hours > 0:
                    self.time_until_send = f"{hours}h {minutes}m"
                else:
                    self.time_until_send = f"{minutes}m"


class NotificationListResponse(BaseModel):
    """Schema pentru listă notificări."""
    items: List[NotificationResponse]
    total: int
    page: int
    per_page: int

    # Stats
    by_status: Dict[str, int]
    by_channel: Dict[str, int]
    scheduled_count: int
    failed_count: int


class NotificationFilter(BaseModel):
    """Schema pentru filtrare notificări."""
    client_id: Optional[int] = None
    notification_type: Optional[NotificationType] = None
    channel: Optional[NotificationChannel] = None
    status: Optional[NotificationStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern=r'^(created_at|scheduled_for|sent_at)$')
    sort_desc: bool = True


class NotificationStats(BaseModel):
    """Schema pentru statistici notificări."""
    period: str  # "today", "week", "month"

    # Volume
    total_sent: int
    total_pending: int
    total_failed: int

    # Success rates
    delivery_rate: float  # sent / (sent + failed)
    retry_success_rate: float

    # By type
    by_type: Dict[str, int]
    by_channel: Dict[str, int]

    # Performance
    avg_send_time_seconds: float
    peak_hour: int  # 0-23

    # Engagement (if tracked)
    telegram_read_rate: Optional[float] = None
    email_open_rate: Optional[float] = None


class NotificationTemplate(BaseModel):
    """Schema pentru template notificare."""
    name: str = Field(..., min_length=3, max_length=100)
    notification_type: NotificationType
    channel: NotificationChannel

    # Content
    subject_template: Optional[str] = None
    message_template: str = Field(..., min_length=10)

    # Variables
    required_vars: List[str] = Field(default_factory=list)
    optional_vars: List[str] = Field(default_factory=list)

    # Example
    example_data: Optional[Dict] = None
    preview: Optional[str] = None


class NotificationQueueStatus(BaseModel):
    """Schema pentru status coadă notificări."""
    pending_count: int
    processing_count: int
    scheduled_count: int

    # Next batch
    next_batch_at: Optional[datetime]
    next_batch_size: int

    # Health
    is_healthy: bool
    last_processed_at: Optional[datetime]
    avg_processing_time: float

    # Errors
    recent_errors: List[Dict]  # Last 5 errors


class NotificationRetry(BaseModel):
    """Schema pentru retry notificare."""
    notification_id: int = Field(..., gt=0)

    # Options
    force: bool = Field(default=False)  # Ignore retry limit
    delay_minutes: int = Field(default=5, ge=0, le=60)