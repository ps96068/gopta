# schemas/user/vendor.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


class VendorBase(BaseModel):
    """Schema de bază pentru Vendor."""
    name: str = Field(..., min_length=3, max_length=255)
    phone: str = Field(..., max_length=20, pattern=r'^\+?[0-9\s\-\(\)]+$')
    contact_person: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)


class VendorCreate(VendorBase):
    """Schema pentru creare vendor."""
    email: EmailStr

    @field_validator('name')
    def validate_name(cls, v):
        """Verifică nume vendor unic și valid."""
        if v.upper() in ['TEST', 'DEMO', 'ADMIN']:
            raise ValueError('Nume rezervat, alegeți altul')
        return v.strip()


class VendorUpdate(BaseModel):
    """Schema pentru actualizare vendor."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    contact_person: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)


class VendorResponse(VendorBase):
    """Schema pentru răspuns vendor."""
    id: int
    email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    products_count: Optional[int] = 0  # număr produse active

    model_config = ConfigDict(from_attributes=True)


class VendorListResponse(BaseModel):
    """Schema pentru listă vendori cu paginare."""
    items: List[VendorResponse]
    total: int
    page: int
    per_page: int