from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Text, Integer, ForeignKey, Numeric, Enum, DateTime, Index, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import IsActiveMixin, CreatedAtMixin, UpdatedAtMixin
from .order import OrderStatus



# catalog/sale/order_status_history.py

class OrderStatusHistory(Base, CreatedAtMixin):
    __tablename__ = "order_status_history"
    __table_args__ = (
        CheckConstraint("old_status <> new_status", name="chk_status_diff"),
        Index("ix_hist_order_time", "order_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    old_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)

    changed_by: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ─────────── Relații ───────────
    order: Mapped["Order"] = relationship("Order", back_populates="status_changes")
    staff: Mapped["Staff"] = relationship("Staff")

    def __repr__(self):
        return (
            f"<OrderStatusHistory(order={self.order_id}, {self.old_status.value}"
            f"→{self.new_status.value}, by={self.changed_by})>"
        )