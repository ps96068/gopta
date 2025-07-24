# models/marketing/user_target_status.py


from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
import enum

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Index, JSON, Boolean, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin, UpdatedAtMixin
from models.enum import ActionType, TargetType




class UserTargetStats(Base, CreatedAtMixin, UpdatedAtMixin):
    """Statistici agregate pentru vizualizări per user/target."""
    __tablename__ = "user_target_stats"
    __table_args__ = (
        UniqueConstraint('client_id', 'target_type', 'target_id', name='uq_user_target'),
    )



    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Statistici
    total_views: Mapped[int] = mapped_column(Integer, default=1)
    total_interactions: Mapped[int] = mapped_column(Integer, default=1)
    add_to_cart_count: Mapped[int] = mapped_column(Integer, default=0)
    request_quote_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timpul primei și ultimei interacțiuni
    first_interaction_at: Mapped[datetime] = mapped_column(default=func.now())
    last_interaction_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    client: Mapped["Client"] = relationship()

