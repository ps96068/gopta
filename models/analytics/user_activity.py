# models/analytics/user_activity.py
"""
UserActivity model pentru tracking activitatea utilizatorilor.

Urmărește când și cât timp utilizatorii accesează platforma,
oferind insights despre engagement și patterns de utilizare.

Business Rules:
- O activitate = o sesiune de utilizare
- Tracking pentru toți utilizatorii (anonim + înregistrați)
- Automatizat prin middleware
- Agregare pentru rapoarte periodice
"""

from __future__ import annotations
from typing import Optional, Dict, TYPE_CHECKING, List
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin


if TYPE_CHECKING:
    from models.user.client import Client


class UserActivity(Base, CreatedAtMixin):
    """Model pentru tracking sesiuni utilizator."""
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    # Session tracking
    session_start: Mapped[datetime] = mapped_column(nullable=False)
    session_end: Mapped[Optional[datetime]] = mapped_column()
    referrer_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Device/platform info
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 ready

    # Metrici sesiune
    page_views: Mapped[int] = mapped_column(Integer, default=0)
    interactions: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="activities")


