# models/sale/cart.py


from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Numeric, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Client, CartItem

class Cart(Base, CreatedAtMixin, UpdatedAtMixin):
    """Model pentru coș de cumpărături."""
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    # Session tracking
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # Număr cos unic
    cart_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Total cos
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


    # Relationships
    client: Mapped["Client"] = relationship(back_populates="carts")
    items: Mapped[List["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")
    invoice: Mapped[List["Invoice"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan"
    )


