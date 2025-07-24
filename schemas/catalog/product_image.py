# schemas/catalog/product_image.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import UploadFile


class ProductImageBase(BaseModel):
    """Schema de bază pentru imagine produs."""
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)


class ProductImageUpload(BaseModel):
    """Schema pentru upload imagine produs."""
    product_id: int = Field(..., gt=0)
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: bool = Field(default=False)
    sort_order: int = Field(default=0, ge=0)

    class Config:
        # Pentru a permite UploadFile în endpoint
        arbitrary_types_allowed = True


class ProductImageCreate(ProductImageBase):
    """Schema pentru creare înregistrare imagine (după upload fizic)."""
    product_id: int = Field(..., gt=0)
    image_path: str = Field(..., min_length=5)
    file_name: str = Field(..., min_length=5)
    file_size: int = Field(..., gt=0)


class ProductImageUpdate(BaseModel):
    """Schema pentru actualizare imagine."""
    alt_text: Optional[str] = Field(None, max_length=255)
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class ProductImageResponse(ProductImageBase):
    """Schema pentru răspuns imagine."""
    id: int
    product_id: int
    image_path: str
    file_name: str
    file_size: int
    created_at: datetime

    # Calculat pentru frontend
    file_url: Optional[str] = None  # URL complet pentru accesare
    file_size_kb: Optional[float] = None  # Dimensiune în KB

    model_config = ConfigDict(from_attributes=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Calculează URL relativ pentru frontend
        if self.image_path:
            # Fix pentru Python 3.11 - nu permite backslash în f-string
            clean_path = self.image_path.replace('\\', '/')
            self.file_url = f"/{clean_path}"
        # Calculează dimensiune în KB
        if self.file_size:
            self.file_size_kb = round(self.file_size / 1024, 2)


class ProductImageBulkUpdate(BaseModel):
    """Schema pentru actualizare bulk ordine imagini."""
    updates: List[dict] = Field(..., min_items=1)

    # Format: [{"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1}]

    @field_validator('updates')
    def validate_updates(cls, v):
        """Validează structura update-urilor."""
        for item in v:
            if 'id' not in item or 'sort_order' not in item:
                raise ValueError('Fiecare item trebuie să aibă "id" și "sort_order"')
            if not isinstance(item['id'], int) or item['id'] <= 0:
                raise ValueError('ID trebuie să fie întreg pozitiv')
            if not isinstance(item['sort_order'], int) or item['sort_order'] < 0:
                raise ValueError('sort_order trebuie să fie întreg >= 0')
        return v


class ProductImagesReorder(BaseModel):
    """Schema pentru reordonare imagini."""
    product_id: int = Field(..., gt=0)
    image_ids: List[int] = Field(..., min_items=1)

    @field_validator('image_ids')
    def validate_unique_ids(cls, v):
        """Verifică că ID-urile sunt unice."""
        if len(v) != len(set(v)):
            raise ValueError('ID-urile trebuie să fie unice')
        return v


class ProductImageStats(BaseModel):
    """Schema pentru statistici imagini produs."""
    product_id: int
    total_images: int
    total_size_bytes: int
    total_size_mb: float
    has_primary: bool
    primary_image_id: Optional[int] = None