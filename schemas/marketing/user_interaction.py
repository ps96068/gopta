from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel

from models import InteractionAction, InteractionTargetType


class UserInteractionBase(BaseModel):
    client_id: int
    action: InteractionAction
    target_type: InteractionTargetType
    target_id: int


class UserInteractionCreate(UserInteractionBase):
    pass


class UserInteractionRead(UserInteractionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True