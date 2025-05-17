from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlalchemy import Date, Integer, String, ForeignKey, Numeric, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import CreatedAtMixin



# models/catalog/exchange_rate.py


class ExchangeRate(Base, CreatedAtMixin):
    """
    1 rând / zi   –   USD → MDL
    """
    __tablename__ = "exchange_rates"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    usd_mdl: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    @validates("usd_mdl")
    def _positive(self, key, value: Decimal):
        if value <= 0:
            raise ValueError("Cursul USD→MDL trebuie să fie pozitiv.")
        return value