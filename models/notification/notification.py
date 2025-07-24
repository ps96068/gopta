# models/notification/notification.py
"""
Notification model pentru sistemul de notificări.

Gestionează notificările trimise către clienți prin multiple canale (Telegram, Email)
cu suport pentru template-uri, variabile dinamice și rate limiting.

Business Rules:
- Max 10 notificări/zi/client între 8:00-19:00
- Template-uri predefinite cu variabile
- HTML pentru email, Markdown pentru Telegram
- Clienții pot dezactiva tipuri de notificări
- Tracking pentru citire unde e posibil
"""

from __future__ import annotations
from typing import Optional, Dict, List, TYPE_CHECKING
from datetime import datetime, time



from sqlalchemy import String, Integer, Text, Boolean, DateTime, Enum, JSON, ForeignKey, Index, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin
from models import NotificationChannel, NotificationType, NotificationStatus


if TYPE_CHECKING:
    from models import Client


class Notification(Base, CreatedAtMixin):
    """Model pentru notificări."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    # Tip și canal
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)

    # Conținut
    subject: Mapped[Optional[str]] = mapped_column(String(255))  # Pentru email
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata (ex: order_id, product_id, etc.)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Status și tracking
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False
    )

    # Programare
    scheduled_for: Mapped[Optional[datetime]] = mapped_column()

    # Rezultat trimitere
    sent_at: Mapped[Optional[datetime]] = mapped_column()
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Retry logic
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="notifications")




