# models/user/client.py
"""
Client model pentru utilizatorii WebApp.

Clienții se autentifică exclusiv prin Telegram ID și pot face achiziții
atât pentru uz personal (B2C) cât și pentru compania la care lucrează (B2B).

Price Type Logic:
- anonim: Client nou, fără date suplimentare
- user: După completarea datelor (email, telefon, nume)
- instalator/pro: Setat manual de către Staff
- Auto-upgrade la 'pro' dacă telegram_id aparține unui Staff
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING


from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Enum, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models.enum.client import UserStatus

if TYPE_CHECKING:
    from models import Cart, Order, UserRequest, UserActivity, UserInteraction, Notification


class Client(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru clienții din Telegram."""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ANONIM, nullable=False)

    # Date personale (completate când devine USER)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Telegram data
    username: Mapped[Optional[str]] = mapped_column(String(100))
    language_code: Mapped[Optional[str]] = mapped_column(String(10), default="ro")

    # Relationships
    carts: Mapped[List["Cart"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    requests: Mapped[List["UserRequest"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    activities: Mapped[List["UserActivity"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    interactions: Mapped[List["UserInteraction"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="client", cascade="all, delete-orphan")