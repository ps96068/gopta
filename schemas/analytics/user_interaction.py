# schemas/analytics/user_interaction.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import ActionType, TargetType


class UserInteractionBase(BaseModel):
    """Schema de bază pentru UserInteraction."""
    action_type: ActionType
    target_type: TargetType
    target_id: int = Field(..., gt=0)
    extra_data: Optional[Dict[str, Any]] = None


class UserInteractionCreate(UserInteractionBase):
    """Schema pentru tracking interacțiune."""
    client_id: int = Field(..., gt=0)
    activity_id: Optional[int] = Field(None, gt=0)

    @field_validator('extra_data')
    def validate_extra_data(cls, v):
        """Validează structura metadata."""
        if v and len(str(v)) > 1000:
            raise ValueError('Metadata prea mare (max 1000 caractere)')
        return v


class UserInteractionBulkCreate(BaseModel):
    """Schema pentru tracking multiple interactions."""
    client_id: int = Field(..., gt=0)
    activity_id: Optional[int] = Field(None, gt=0)
    interactions: List[UserInteractionBase] = Field(..., min_items=1, max_items=50)


class UserInteractionResponse(UserInteractionBase):
    """Schema pentru răspuns interacțiune."""
    id: int
    client_id: int
    activity_id: Optional[int]
    view_count: int
    last_viewed_at: datetime
    created_at: datetime

    # Target info (joined)
    target_name: Optional[str] = None
    target_slug: Optional[str] = None

    # Calculat
    interaction_type_display: str
    time_since: str

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)

        # Display friendly
        self.interaction_type_display = f"{self.action_type.value} {self.target_type.value}"

        # Time since
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            if delta.days > 0:
                self.time_since = f"{delta.days} zile"
            elif delta.seconds > 3600:
                self.time_since = f"{delta.seconds // 3600} ore"
            elif delta.seconds > 60:
                self.time_since = f"{delta.seconds // 60} minute"
            else:
                self.time_since = "acum"


class UserInteractionListResponse(BaseModel):
    """Schema pentru listă interacțiuni."""
    items: List[UserInteractionResponse]
    total: int
    page: int
    per_page: int

    # Summary
    by_action: Dict[str, int]
    by_target: Dict[str, int]


class UserInteractionFilter(BaseModel):
    """Schema pentru filtrare interacțiuni."""
    client_id: Optional[int] = None
    action_type: Optional[ActionType] = None
    target_type: Optional[TargetType] = None
    target_id: Optional[int] = None
    activity_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_extra_data: Optional[bool] = None

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)
    sort_by: str = Field(default="created_at", pattern=r'^(created_at|view_count)$')
    sort_desc: bool = True


class InteractionHeatmap(BaseModel):
    """Schema pentru heatmap interacțiuni."""
    period: str  # "day", "week", "month"
    timezone: str = "Europe/Chisinau"

    # Data structure for heatmap
    # Hour x Day grid
    data: List[List[int]]  # 24x7 for week, 24x1 for day

    # Labels
    hour_labels: List[str]
    day_labels: List[str]

    # Stats
    peak_hour: int
    peak_day: Optional[str]
    total_interactions: int


class UserPath(BaseModel):
    """Schema pentru analiza căi utilizator."""
    client_id: int
    session_id: Optional[int]
    path_length: int

    # Secvența de acțiuni
    steps: List[Dict] = Field(default_factory=list)
    # Format: [{"action": "view", "target": "category_1", "timestamp": "...", "name": "Telefoane"}]

    # Rezultat
    ended_with: str  # "purchase", "cart_abandon", "exit"
    conversion: bool = False
    total_duration_seconds: int


class PopularPaths(BaseModel):
    """Schema pentru cele mai populare căi."""
    period: str
    top_paths: List[Dict]
    # Format: [{"path": "home->category->product->cart", "count": 150, "conversion_rate": 0.23}]

    # Insights
    most_common_entry: str
    most_common_exit: str
    avg_path_length: float


class InteractionFunnel(BaseModel):
    """Schema pentru funnel analysis."""
    funnel_name: str
    period: str

    stages: List[Dict]
    # Format: [
    #   {"name": "Viewed Category", "users": 1000, "percentage": 100},
    #   {"name": "Viewed Product", "users": 600, "percentage": 60},
    #   {"name": "Added to Cart", "users": 200, "percentage": 20},
    #   {"name": "Completed Order", "users": 50, "percentage": 5}
    # ]

    # Conversion rates
    overall_conversion: float
    biggest_drop: str  # "Viewed Product -> Added to Cart"

    # Segmentation
    by_user_status: Dict[str, float]  # conversion by status


class ProductInteractionStats(BaseModel):
    """Schema pentru statistici interacțiuni produs."""
    product_id: int
    product_name: str
    period: str

    # Views
    total_views: int
    unique_viewers: int
    avg_views_per_user: float

    # Actions
    add_to_cart_count: int
    request_quote_count: int

    # Conversion
    view_to_cart_rate: float
    cart_to_order_rate: float

    # Engagement
    avg_view_duration: Optional[int]  # seconds, if tracked
    bounce_rate: float  # viewed but no other action

    # Sources
    traffic_sources: Dict[str, int]  # {"category": 50, "search": 30, "direct": 20}