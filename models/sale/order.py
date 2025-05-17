from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Text, Integer, ForeignKey, Numeric, Enum, String, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from cfg.mixins import AuditMixin
from models.base import IsActiveMixin, CreatedAtMixin, UpdatedAtMixin


# catalog/sale/order.py

class OrderStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    canceled = "canceled"


class Order(Base, AuditMixin, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_client", "client_id"),
        Index("ix_orders_status", "status"),
    )

    # ---------- PK & FK ----------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)

    # ---------- Status ----------
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.pending,
        nullable=False,
    )

    # ---------- Totals snapshot ----------
    total_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_mdl: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    currency_rate_used: Mapped[Decimal] = mapped_column(Numeric(10, 4))

    # ---------- Client contact snapshot ----------
    client_username: Mapped[str] = mapped_column(String, nullable=False)
    client_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    client_email: Mapped[str] = mapped_column(String, nullable=False)

    # ---------- Optional ----------
    invoice_qr_path: Mapped[str | None] = mapped_column(String, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---------- Relații ----------
    client: Mapped["Client"] = relationship("Client", back_populates="orders")

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    status_changes: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    requests: Mapped[list["UserRequest"]] = relationship(
        "UserRequest",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # ---------- Proprietăți ----------
    @property
    def total_amount_mdl(self) -> Decimal:
        """Calculează dinamically din OrderItem dacă vrei verificare."""
        return sum(item.total_price_mdl for item in self.items)

    # ---------- Validators ----------
    @validates("status")
    def validate_status(self, key, value: OrderStatus):
        if self.status == OrderStatus.completed and value != OrderStatus.completed:
            raise ValueError("O comandă finalizată nu poate fi modificată.")
        return value

    def __repr__(self):
        return (
            f"<Order(id={self.id}, client={self.client_id}, "
            f"total_mdl={self.total_mdl}, status={self.status.value})>"
        )


"""

DIN ALTA VIATA !!!!!!!!!!!

# Metoda pentru a gestiona schimbarea statutului și pentru a crea o nouă înregistrare în OrderStatusHistory de fiecare dată când o comandă este modificată
def change_status(self, new_status: OrderStatus, changed_by: int, session):
    if self.status == new_status:
        raise ValueError("Starea comenzii este deja setată la această valoare.")

    # Creăm istoricul schimbării
    status_history = OrderStatusHistory(
        order_id=self.id,
        old_status=self.status,
        new_status=new_status,
        changed_by=changed_by
    )
    session.add(status_history)

    # Actualizăm starea comenzii
    self.status = new_status
    session.commit()

"""

