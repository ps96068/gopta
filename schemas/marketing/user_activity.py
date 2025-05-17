from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel




class UserActivityRead(BaseModel):
    id: int
    client_id: int
    session_start: datetime
    session_end: datetime | None
    session_duration: int | None
    created_at: datetime

    class Config:
        from_attributes = True