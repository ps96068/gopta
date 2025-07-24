# models/sale/invoice.py
"""
Invoice model pentru chitanțele generate automat.

Invoice model pentru chitanțe și oferte.

Invoice poate fi generat din:
1. Cart -> Ofertă (quote) cu format "Oferta nr. O_XXXXX"
2. Order -> Cont/Factură cu format "Cont nr. C_XXXXX"

Business Rules:
- Un Cart poate avea o ofertă (one-to-one)
- O Order poate avea o factură (one-to-one)
- PDF generat automat și salvat local
- Trimis automat prin Telegram la client
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime


from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Enum, DateTime, Boolean, Index, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin
from models.enum import InvoiceType

if TYPE_CHECKING:
    from models import Order, Cart


class Invoice(Base, CreatedAtMixin):
    """Model pentru facturi și oferte."""
    __tablename__ = "invoices"

    # Constraints pentru a asigura că invoice e legat ori de cart, ori de order
    __table_args__ = (
        UniqueConstraint('cart_id', name='uq_invoice_cart'),
        UniqueConstraint('order_id', name='uq_invoice_order'),
        Index('ix_invoice_type', 'invoice_type'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Tip invoice
    invoice_type: Mapped[InvoiceType] = mapped_column(
        SQLEnum(InvoiceType),
        nullable=False,
        index=True
    )

    # Număr unic (O_XXXXX sau C_XXXXX)
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # Legături opționale - unul sau altul
    cart_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("carts.id"),
        nullable=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True
    )

    # Date client (snapshot la momentul generării)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[Optional[str]] = mapped_column(String(20))
    client_company: Mapped[Optional[str]] = mapped_column(String(255))

    # Total
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="MDL", nullable=False)

    # Validitate (pentru oferte)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Status trimitere
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sent_via: Mapped[Optional[str]] = mapped_column(String(50))  # telegram/email

    # Conversie (pentru tracking ofertă → comandă)
    converted_to_order: Mapped[bool] = mapped_column(Boolean, default=False)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Document generat (path local)
    document_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Note/Observații
    notes: Mapped[Optional[str]] = mapped_column(Text)

    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500))
    cancelled_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"))


    # Relationships
    order: Mapped[Optional["Order"]] = relationship(back_populates="invoice")
    cart: Mapped[Optional["Cart"]] = relationship(back_populates="invoice")

    @validates('invoice_type')
    def validate_relations(self, key, invoice_type):
        """Validează că invoice are relația corectă."""
        if invoice_type == InvoiceType.QUOTE and not self.cart_id:
            raise ValueError("Quote invoice requires cart_id")
        if invoice_type == InvoiceType.INVOICE and not self.order_id:
            raise ValueError("Order invoice requires order_id")
        return invoice_type

    @property
    def display_name(self) -> str:
        """Returnează numele afișat pentru invoice."""
        if self.invoice_type == InvoiceType.QUOTE:
            return f"Oferta nr. {self.invoice_number}"
        return f"Cont nr. {self.invoice_number}"

    @property
    def is_quote(self) -> bool:
        """Verifică dacă e ofertă."""
        return self.invoice_type == InvoiceType.QUOTE

    @property
    def is_invoice(self) -> bool:
        """Verifică dacă e factură."""
        return self.invoice_type == InvoiceType.INVOICE



