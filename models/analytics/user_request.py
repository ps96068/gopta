# models/analytics/user_request.py
"""
UserRequest model pentru solicitări oferte speciale.

Gestionează cererile clienților pentru oferte personalizate pe produse,
comenzi sau general. Doar clienții înregistrați (non-anonimi) pot face cereri.

Business Rules:
- Doar user, instalator, pro pot solicita oferte (nu anonim)
- Tipuri: product, order, general
- Notificări automate către Staff
- Tracking conversie cerere → comandă
- Toate cererile se salvează pentru analytics
"""

from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Integer, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models.enum import RequestType

if TYPE_CHECKING:
    from models import Client, Product, Cart, RequestResponse



class UserRequest(Base, CreatedAtMixin):
    """Model pentru cererile utilizatorilor."""
    __tablename__ = "user_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    request_type: Mapped[RequestType] = mapped_column(Enum(RequestType), nullable=False)

    # Pentru cereri legate de produs/coș
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), index=True)
    cart_id: Mapped[Optional[int]] = mapped_column(ForeignKey("carts.id"))

    # Conținut cerere
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Status procesare
    is_processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column()

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="requests")
    product: Mapped[Optional["Product"]] = relationship()
    cart: Mapped[Optional["Cart"]] = relationship()
    responses: Mapped[list["RequestResponse"]] = relationship(back_populates="request", cascade="all, delete-orphan")

