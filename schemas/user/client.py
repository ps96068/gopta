# schemas/user/user.py


from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from models import UserStatus


# Client Schemas
class ClientBase(BaseModel):
    """Schema de bază pentru Client."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20, pattern=r'^\+?[0-9\s\-\(\)]+$')
    email: Optional[EmailStr] = None
    language_code: str = Field(default="ro", max_length=10)


class ClientCreate(BaseModel):
    """Schema pentru crearea inițială din Telegram."""
    telegram_id: int
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    language_code: str = Field(default="ro", max_length=10)


class ClientUpdate(ClientBase):
    """Schema pentru actualizare date client (ANONIM -> USER)."""
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., max_length=20, pattern=r'^\+373[0-9]{8}$')
    email: EmailStr

    @field_validator('phone')
    def validate_moldovan_phone(cls, v):
        """Validează număr de telefon moldovenesc."""
        if not v.startswith('+373'):
            raise ValueError('Numărul de telefon trebuie să înceapă cu +373')
        return v


class ClientStatusUpdate(BaseModel):
    """Schema pentru actualizare status de către staff."""
    status: UserStatus


class ClientResponse(ClientBase):
    """Schema pentru răspuns client."""
    id: int
    telegram_id: int
    status: UserStatus
    username: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)