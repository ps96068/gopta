# models/sale/order.py
"""
Order model pentru comenzile clienților.

Comenzile pot fi plasate pentru uz personal (B2C) sau pentru companie (B2B).
Fiecare comandă generează automat o factură și notificări.

Business Rules:
- Order number format: ORD-YYYY-XXXXX
- Status flow: pending → processing → completed (sau cancelled)
- La anulare se cere motiv obligatoriu
- Notificări automate la creare și schimbare status
- Prețurile sunt snapshot la momentul comenzii
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Numeric, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin
from models import OrderStatus


if TYPE_CHECKING:
    from models import Client, Staff, OrderItem, Invoice


class Order(Base, CreatedAtMixin, UpdatedAtMixin):
    """Model pentru comenzi."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    # Număr comandă unic
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Status și procesare
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    processed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"))
    processed_at: Mapped[Optional[datetime]] = mapped_column()

    # Total comandă
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="MDL", nullable=False)

    # Note și comentarii
    client_note: Mapped[Optional[str]] = mapped_column(Text)
    staff_note: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="orders")
    processed_by: Mapped[Optional["Staff"]] = relationship(back_populates="processed_orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    invoice: Mapped[Optional["Invoice"]] = relationship(
        back_populates="order",
        uselist=False
    )


