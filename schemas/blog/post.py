# schemas/blog/post.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.blog import PostImage


class PostBase(BaseModel):
    """Schema de bază pentru Post."""
    title: str = Field(..., min_length=5, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=50)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_featured: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)


class PostCreate(PostBase):
    """Schema pentru creare articol."""
    slug: str = Field(..., min_length=3, max_length=255, pattern=r'^[a-z0-9\-]+$')
    author_id: int = Field(..., gt=0)

    @field_validator('slug')
    def validate_slug(cls, v):
        """Validează slug format."""
        return v.lower().strip()

    @field_validator('content')
    def validate_content(cls, v):
        """Validează conținut minim."""
        # Remove HTML tags pentru verificare lungime
        import re
        text_only = re.sub('<.*?>', '', v)
        if len(text_only) < 50:
            raise ValueError('Conținutul trebuie să aibă minim 50 caractere (fără HTML)')
        return v


class PostUpdate(BaseModel):
    """Schema pentru actualizare articol."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=50)
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PostImageResponse(BaseModel):
    """Schema pentru imagine articol."""
    id: int
    image_path: str
    file_name: str
    file_size: int
    alt_text: Optional[str]
    caption: Optional[str]
    is_featured: bool
    sort_order: int
    created_at: datetime

    # Calculat
    file_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.image_path:
            clean_path = self.image_path.replace('\\', '/')
            self.file_url = f"/{clean_path}"


class PostResponse(PostBase):
    """Schema pentru răspuns articol."""
    id: int
    slug: str
    author_id: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    # Author info
    author_name: Optional[str] = None
    author_email: Optional[str] = None

    # Images
    images: List[PostImageResponse] = []
    featured_image: Optional[PostImageResponse] = None

    # Calculat
    reading_time_minutes: Optional[int] = None
    is_new: bool = False  # Publicat în ultimele 7 zile
    formatted_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)

        # Reading time (200 cuvinte pe minut)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time_minutes = max(1, word_count // 200)

        # Is new?
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            self.is_new = delta.days <= 7

            # Format date
            self.formatted_date = self.created_at.strftime("%d %B %Y")

        # Extract featured image
        if self.images:
            featured = [img for img in self.images if img.is_featured]
            if featured:
                self.featured_image = featured[0]


class PostListResponse(BaseModel):
    """Schema pentru listă articole."""
    items: List[PostResponse]
    total: int
    page: int
    per_page: int

    # Stats
    featured_count: int = 0
    total_views: int = 0


class PostFilter(BaseModel):
    """Schema pentru filtrare articole."""
    is_active: Optional[bool] = True
    is_featured: Optional[bool] = None
    author_id: Optional[int] = None
    search: Optional[str] = Field(None, min_length=2)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    sort_by: str = Field(default="created_at", pattern=r'^(created_at|view_count|title|sort_order)$')
    sort_desc: bool = True


class PostStats(BaseModel):
    """Schema pentru statistici blog."""
    period: str  # "week", "month", "year", "all"

    # Content
    total_posts: int
    active_posts: int
    featured_posts: int

    # Engagement
    total_views: int
    avg_views_per_post: float
    most_viewed_post_id: Optional[int]
    most_viewed_post_title: Optional[str]

    # Authors
    total_authors: int
    most_active_author: Optional[str]
    posts_by_author: dict

    # Trends
    views_trend: List[dict]  # [{"date": "2024-01-01", "views": 150}]
    posts_trend: List[dict]  # [{"month": "2024-01", "posts": 5}]


class PostSEO(BaseModel):
    """Schema pentru SEO check."""
    post_id: int

    # Checks
    has_meta_title: bool
    has_meta_description: bool
    meta_title_length: int
    meta_description_length: int

    # Recommendations
    meta_title_ok: bool  # 50-60 chars
    meta_description_ok: bool  # 150-160 chars
    slug_ok: bool  # no special chars, good length
    has_featured_image: bool

    # Score
    seo_score: int  # 0-100
    recommendations: List[str]


class RelatedPostsRequest(BaseModel):
    """Schema pentru cerere articole related."""
    post_id: int = Field(..., gt=0)
    limit: int = Field(default=3, ge=1, le=10)

    # Strategy
    strategy: str = Field(default="mixed", pattern=r'^(category|tags|mixed)$')