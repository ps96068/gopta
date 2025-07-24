# schemas/blog/post_image.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostImageBase(BaseModel):
    """Schema de bază pentru PostImage."""
    alt_text: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = Field(None, max_length=500)
    is_featured: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)


class PostImageUpload(BaseModel):
    """Schema pentru upload imagine articol."""
    post_id: int = Field(..., gt=0)
    alt_text: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = Field(None, max_length=500)
    is_featured: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)

    class Config:
        arbitrary_types_allowed = True


class PostImageCreate(PostImageBase):
    """Schema pentru creare înregistrare imagine (după upload fizic)."""
    post_id: int = Field(..., gt=0)
    image_path: str = Field(..., min_length=5)
    file_name: str = Field(..., min_length=5)
    file_size: int = Field(..., gt=0)


class PostImageUpdate(BaseModel):
    """Schema pentru actualizare imagine articol."""
    alt_text: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = Field(None, max_length=500)
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class PostImageResponse(PostImageBase):
    """Schema pentru răspuns imagine articol."""
    id: int
    post_id: int
    image_path: str
    file_name: str
    file_size: int
    created_at: datetime

    # Calculat
    file_url: Optional[str] = None
    file_size_kb: Optional[float] = None
    is_valid: bool = True

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # URL pentru frontend
        if self.image_path:
            clean_path = self.image_path.replace('\\', '/')
            self.file_url = f"/{clean_path}"

        # Size în KB
        if self.file_size:
            self.file_size_kb = round(self.file_size / 1024, 2)

        # Verifică dacă fișierul există
        import os
        if self.image_path:
            self.is_valid = os.path.exists(self.image_path)


class PostImageBulkUpdate(BaseModel):
    """Schema pentru actualizare bulk imagini articol."""
    updates: List[dict] = Field(..., min_items=1)

    # Format: [{"id": 1, "sort_order": 0, "is_featured": true}]

    @field_validator('updates')
    def validate_updates(cls, v):
        """Validează structura."""
        for item in v:
            if 'id' not in item:
                raise ValueError('Fiecare item trebuie să aibă "id"')
            if not isinstance(item['id'], int) or item['id'] <= 0:
                raise ValueError('ID trebuie să fie întreg pozitiv')

        # Verifică doar un featured
        featured = [item for item in v if item.get('is_featured', False)]
        if len(featured) > 1:
            raise ValueError('Doar o imagine poate fi featured')

        return v


class PostImagesReorder(BaseModel):
    """Schema pentru reordonare imagini articol."""
    post_id: int = Field(..., gt=0)
    image_ids: List[int] = Field(..., min_items=1)

    @field_validator('image_ids')
    def validate_unique_ids(cls, v):
        """Verifică ID-uri unice."""
        if len(v) != len(set(v)):
            raise ValueError('ID-urile trebuie să fie unice')
        return v


class PostImageGallery(BaseModel):
    """Schema pentru galerie imagini articol."""
    post_id: int
    post_title: str
    total_images: int
    featured_image: Optional[PostImageResponse] = None
    images: List[PostImageResponse] = []

    # Stats
    total_size_mb: float = 0.0
    has_captions: bool = False
    has_alt_texts: bool = False

    def __init__(self, **data):
        super().__init__(**data)

        # Calculate stats
        if self.images:
            total_bytes = sum(img.file_size for img in self.images)
            self.total_size_mb = round(total_bytes / (1024 * 1024), 2)

            self.has_captions = any(img.caption for img in self.images)
            self.has_alt_texts = any(img.alt_text for img in self.images)

            # Extract featured
            featured = [img for img in self.images if img.is_featured]
            if featured:
                self.featured_image = featured[0]


class PostImageOptimization(BaseModel):
    """Schema pentru sugestii optimizare imagini."""
    image_id: int
    current_size_kb: float

    # Issues
    too_large: bool = False  # > 500KB
    missing_alt_text: bool = False
    missing_caption: bool = False
    invalid_path: bool = False

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    optimization_score: int = 100  # 0-100

    def calculate_score(self):
        """Calculează scor optimizare."""
        score = 100

        if self.too_large:
            score -= 30
            self.recommendations.append("Reduceți dimensiunea imaginii sub 500KB")

        if self.missing_alt_text:
            score -= 20
            self.recommendations.append("Adăugați text alternativ pentru SEO")

        if self.missing_caption:
            score -= 10
            self.recommendations.append("Adăugați descriere pentru imagine")

        if self.invalid_path:
            score = 0
            self.recommendations.append("Imaginea nu există pe disk!")

        self.optimization_score = max(0, score)