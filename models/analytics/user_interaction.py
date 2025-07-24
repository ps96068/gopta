# models/marketing/user_interaction.py
"""
UserInteraction model pentru tracking interacțiunilor utilizatorilor.

Urmărește acțiunile specifice ale utilizatorilor: views, clicks, shares, etc.
Oferă date granulare pentru analiza comportamentului și personalizare.

Business Rules:
- Event tracking pentru toate acțiunile importante
- Support pentru target-uri multiple (product, category, blog)
- Agregare pentru analytics și recomandări
- Privacy-compliant (hashing pentru date sensibile)
"""

from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
import enum

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Index, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin
from models.enum import ActionType, TargetType

if TYPE_CHECKING:
    from models.user.client import Client
    from models.catalog.product import Product
    from models.catalog.category import Category
    from models.blog.post import Post


class UserInteraction(Base, CreatedAtMixin):
    """Model pentru tracking interacțiuni specifice."""
    __tablename__ = "user_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)

    # Ce fel de interacțiune
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False, index=True)
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), nullable=False, index=True)

    # ID-ul țintei (product_id, category_id, post_id, cart_id)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Metadata suplimentară (ex: search query, share platform)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Context sesiune
    activity_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_activities.id"))

    # Tracking vizite repetate
    view_count: Mapped[int] = mapped_column(Integer, default=1)
    last_viewed_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="interactions")
    activity: Mapped[Optional["UserActivity"]] = relationship()


