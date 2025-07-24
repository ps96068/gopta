# schemas/analytics/user_activity.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ipaddress import ip_address


class UserActivityBase(BaseModel):
    """Schema de bază pentru UserActivity."""
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)

    @field_validator('ip_address')
    def validate_ip(cls, v):
        """Validează format IP."""
        if v:
            try:
                ip_address(v)
            except ValueError:
                raise ValueError('Format IP invalid')
        return v


class UserActivityStart(UserActivityBase):
    """Schema pentru start sesiune."""
    client_id: int = Field(..., gt=0)

    # Metadata suplimentară
    device_type: Optional[str] = Field(None, pattern=r'^(mobile|tablet|desktop|unknown)$')
    platform: Optional[str] = Field(None, pattern=r'^(ios|android|web|unknown)$')
    app_version: Optional[str] = Field(None, max_length=20)


class UserActivityEnd(BaseModel):
    """Schema pentru închidere sesiune."""
    activity_id: int = Field(..., gt=0)

    # Reason pentru închidere
    end_reason: Optional[str] = Field(default="user_action", pattern=r'^(user_action|timeout|app_close|error)$')


class UserActivityResponse(UserActivityBase):
    """Schema pentru răspuns activitate."""
    id: int
    client_id: int
    session_start: datetime
    session_end: Optional[datetime]

    # Metrici
    page_views: int
    interactions: int

    # Client info
    client_telegram_id: Optional[int] = None
    client_status: Optional[str] = None

    # Calculat
    session_duration_seconds: Optional[int] = None
    session_duration_formatted: Optional[str] = None
    is_active: bool = False
    device_info: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)

        # Calculează durata
        if self.session_start and self.session_end:
            duration = self.session_end - self.session_start
            self.session_duration_seconds = int(duration.total_seconds())

            # Format human-readable
            hours = self.session_duration_seconds // 3600
            minutes = (self.session_duration_seconds % 3600) // 60
            seconds = self.session_duration_seconds % 60

            if hours > 0:
                self.session_duration_formatted = f"{hours}h {minutes}m"
            elif minutes > 0:
                self.session_duration_formatted = f"{minutes}m {seconds}s"
            else:
                self.session_duration_formatted = f"{seconds}s"

        # Verifică dacă e activă
        self.is_active = self.session_end is None

        # Parse user agent pentru device info
        if self.user_agent:
            self.device_info = self._parse_user_agent()

    def _parse_user_agent(self) -> Dict:
        """Extrage info din user agent."""
        ua = self.user_agent.lower()
        return {
            "is_mobile": "mobile" in ua or "android" in ua or "iphone" in ua,
            "is_telegram": "telegram" in ua,
            "platform": "android" if "android" in ua else "ios" if "iphone" in ua else "unknown"
        }


class UserActivityListResponse(BaseModel):
    """Schema pentru listă activități."""
    items: List[UserActivityResponse]
    total: int
    page: int
    per_page: int

    # Stats
    active_sessions: int = 0
    avg_session_duration: Optional[int] = None
    total_page_views: int = 0


class UserActivityFilter(BaseModel):
    """Schema pentru filtrare activități."""
    client_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_active: Optional[bool] = None
    min_duration_seconds: Optional[int] = Field(None, ge=0)
    max_duration_seconds: Optional[int] = Field(None, ge=0)
    has_interactions: Optional[bool] = None

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="session_start", pattern=r'^(session_start|duration|page_views)$')
    sort_desc: bool = True


class ActiveSessionsResponse(BaseModel):
    """Schema pentru sesiuni active în timp real."""
    total_active: int
    sessions: List[Dict]

    # Breakdown
    by_platform: Dict[str, int]
    by_status: Dict[str, int]

    # Recent activity
    last_5_minutes: int
    last_hour: int


class UserActivityStats(BaseModel):
    """Schema pentru statistici activitate."""
    period: str  # "today", "week", "month"

    # Sessions
    total_sessions: int
    unique_users: int
    avg_sessions_per_user: float

    # Duration
    total_time_seconds: int
    avg_session_duration_seconds: int
    longest_session_seconds: int

    # Engagement
    total_page_views: int
    total_interactions: int
    avg_pages_per_session: float
    bounce_rate: float  # Sessions with 1 page view

    # Peak times
    peak_hour: int  # 0-23
    peak_day: str  # "monday", etc.

    # Devices
    mobile_percentage: float
    desktop_percentage: float


class UserJourneySession(BaseModel):
    """Schema pentru o sesiune în user journey."""
    session_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_formatted: str
    page_views: int
    key_actions: List[str]  # ["viewed_category_phones", "added_to_cart", etc.]
    resulted_in_order: bool = False
    order_id: Optional[int] = None