from __future__ import annotations

import re
import enum
from datetime import datetime
from starlette.requests import Request
from sqlalchemy import Index, String, Boolean, Enum, DateTime, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column, Relationship
from sqlalchemy.sql import func



from cfg import Base
from ..base import CreatedAtMixin, IsActiveMixin

# models/user/clients.py

class ClientStatus(enum.Enum):
    anonim = "anonim"
    user = "user"
    instalator = "instalator"
    pro = "pro"



class Client(Base, CreatedAtMixin, IsActiveMixin):
    __tablename__ = "clients"
    __table_args__ = (
        Index("ix_client_status_active", "status", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, unique=False, index=True, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    status: Mapped[ClientStatus] = mapped_column(Enum(ClientStatus), nullable=False, default=ClientStatus.anonim)

    # create_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_visit: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relatii
    activities: Mapped[list["UserActivity"]] = relationship("UserActivity", back_populates="client")
    interactions: Mapped[list["UserInteraction"]] = relationship("UserInteraction", back_populates="client")
    requests: Mapped[list["UserRequest"]] = relationship("UserRequest", back_populates="client")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="client")


    @validates('phone_number')
    def validate_phone(self, key, number: str | None):
        if number and not re.match(r"^\+?[0-9]{7,15}$", number):
            raise ValueError("Numărul de telefon are un format invalid")
        return number

    @validates('email')
    def validate_email(self, key, email):
        if email is None:
            return None
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Adresa de email este invalidă")
        return email

    def __repr__(self):
        return f"<Client(id={self.id}, username='{self.username}', telegram_id='{self.telegram_id}', status='{self.status.value}')>"

    def __str__(self):
        return f"{self.id}_{self.username}-({self.status})"



