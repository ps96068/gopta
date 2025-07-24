# schemas/user/staff.py


from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator

from models import StaffRole


# Staff Schemas
class StaffBase(BaseModel):
    """Schema de bază pentru Staff."""
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: StaffRole = Field(default=StaffRole.SUPERVISOR)


class StaffCreate(StaffBase):
    """Schema pentru creare staff."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    def validate_password(cls, v):
        """Validează complexitatea parolei."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Parola trebuie să conțină cel puțin o cifră')
        if not any(char.isupper() for char in v):
            raise ValueError('Parola trebuie să conțină cel puțin o literă mare')
        return v


class StaffUpdate(StaffBase):
    """Schema pentru actualizare staff."""
    pass


class StaffLogin(BaseModel):
    """Schema pentru autentificare staff."""
    email: EmailStr
    password: str


class StaffResponse(BaseModel):
    """Schema pentru răspuns staff (fără parolă)."""
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: StaffRole
    last_login: Optional[datetime]
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)