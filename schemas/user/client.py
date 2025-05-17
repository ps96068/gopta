from __future__ import annotations

import enum
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, constr


class ClientStatus(str, enum.Enum):
    anonim = "anonim"
    user = "user"
    instalator = "instalator"
    pro = "pro"


Phone = constr(regex=r"^\+?[0-9]{7,15}$")  # type: ignore[valid-type]


# ---------- Base ----------
class ClientBase(BaseModel):
    telegram_id: str
    username: str | None = None
    phone_number: Phone | None = None
    email: EmailStr | None = None
    status: ClientStatus = ClientStatus.anonim
    is_active: bool = True


# ---------- Create ----------
class ClientCreate(ClientBase):
    """Creat de bot – status rămâne implicit 'anonim'."""


# ---------- Update ----------
class ClientUpdate(BaseModel):
    username: str | None = None
    phone_number: Phone | None = None
    email: EmailStr | None = None
    status: ClientStatus | None = None
    is_active: bool | None = None


# ---------- Read ----------
class ClientRead(ClientBase):
    id: int
    created_at: datetime
    last_visit: datetime | None = None

    class Config:
        from_attributes = True
