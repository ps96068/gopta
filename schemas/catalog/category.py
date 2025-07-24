# schemas/catalog/category.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from fastapi import UploadFile



class CategoryBase(BaseModel):
    """Schema de bază pentru Category."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = Field(default=0, ge=0)


class CategoryCreate(CategoryBase):
    """Schema pentru creare categorie."""
    slug: str = Field(..., min_length=2, max_length=255, pattern=r'^[a-z0-9\-]+$')

    @field_validator('slug')
    def validate_slug(cls, v):
        """Validează slug unic și format corect."""
        if not v.replace('-', '').isalnum():
            raise ValueError('Slug poate conține doar litere mici, cifre și cratimă')
        return v.lower()


class CategoryUpdate(BaseModel):
    """Schema pentru actualizare categorie."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = Field(None, ge=0)
    image_path: Optional[str] = None


class CategoryImageUpload(BaseModel):
    """Schema pentru validare upload imagine."""
    file: UploadFile

    @field_validator('file')
    def validate_file(cls, v):
        """Validează tipul fișierului."""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if v.content_type not in allowed_types:
            raise ValueError(f'Tip fișier nepermis. Permise: {", ".join(allowed_types)}')
        if v.size > 2 * 1024 * 1024:  # 2MB
            raise ValueError('Fișier prea mare. Maxim 2MB')
        return v


class CategoryResponse(CategoryBase):
    """Schema pentru răspuns categorie."""
    id: int
    slug: str
    image_path: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    products_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeResponse(CategoryResponse):
    """Schema pentru arbore categorii."""
    children: List['CategoryTreeResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    """Schema pentru listă categorii."""
    items: List[CategoryResponse]
    total: int