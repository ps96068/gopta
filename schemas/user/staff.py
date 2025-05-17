from __future__ import annotations

import enum
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, constr


class StaffRole(str, enum.Enum):
    super_admin = "super_admin"
    manager = "manager"
    supervisor = "supervisor"


Phone = constr(regex=r"^\+?[0-9]{7,15}$")  # type: ignore[valid-type]


# ---------- Base ----------
class StaffBase(BaseModel):
    username: str
    phone_number: Phone | None = None
    email: EmailStr | None = None
    role: StaffRole = StaffRole.supervisor
    is_active: bool = True
    telegram_id: str | None = None


# ---------- Create ----------
class StaffCreate(StaffBase):
    password_hash: str = Field(..., min_length=6)


# ---------- Update ----------
class StaffUpdate(BaseModel):
    phone_number: Phone | None = None
    email: EmailStr | None = None
    role: StaffRole | None = None
    is_active: bool | None = None
    password_hash: str | None = Field(default=None, min_length=6)


# ---------- Read ----------
class StaffRead(StaffBase):
    id: int
    created_at: datetime
    last_visit: datetime | None = None

    class Config:
        from_attributes = True
