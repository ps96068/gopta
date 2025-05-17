from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ---------- Base ----------
class ExchangeRateBase(BaseModel):
    date: date = Field(..., description="Ziua la care se aplică cursul")
    usd_mdl: Decimal = Field(..., gt=0, description="Curs USD → MDL (4 zecimale)")


# ---------- Create ----------
class ExchangeRateCreate(ExchangeRateBase):
    """Schema folosită la POST /exchange-rate"""


# ---------- Read ----------
class ExchangeRateRead(ExchangeRateBase):
    created_at: datetime

    class Config:
        from_attributes = True