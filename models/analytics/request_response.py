# models/analytics/request_response.py
"""
RequestResponse model pentru răspunsuri la cereri oferte.

Gestionează răspunsurile Staff/Vendor la cererile clienților.
Permite conversații multi-turn și tracking pentru conversie.

Business Rules:
- Un request poate avea multiple răspunsuri
- Staff și Vendor pot răspunde
- Notificare automată către client
- Tracking pentru analytics și conversie
"""

from __future__ import annotations
from typing import Optional, Dict, TYPE_CHECKING, List
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models.enum import RequestType

if TYPE_CHECKING:
    from models.user.staff import Staff
    # from models.user.vendor import Vendor
    from .user_request import UserRequest


class RequestResponse(Base, CreatedAtMixin):
    """Model pentru răspunsurile la cereri."""
    __tablename__ = "request_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("user_requests.id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Pentru tracking comunicare
    sent_via: Mapped[Optional[str]] = mapped_column(String(50))  # telegram/email/phone

    # Relationships
    request: Mapped["UserRequest"] = relationship(back_populates="responses")
    staff: Mapped["Staff"] = relationship(back_populates="responses")







