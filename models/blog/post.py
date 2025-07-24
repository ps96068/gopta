# models/blog/post.py
"""
Post model pentru articolele blog.

Postările sunt create de Staff (super_admin și manager) și servesc
pentru a informa clienții despre noutăți, tutoriale, ghiduri etc.

Business Rules:
- Create/Edit/Unpublish: super_admin și manager
- Delete: doar super_admin
- Slug auto-generat din titlu
- Notificări automate la publicare
- Maxim 5 imagini per post
- HTML sanitizat pentru conținut
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING


from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates


from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Staff, PostImage



class Post(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru articole blog."""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Conținut
    excerpt: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Autor
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255))
    meta_description: Mapped[Optional[str]] = mapped_column(String(500))

    # Ordine și featured
    is_featured: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Statistici
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    author: Mapped["Staff"] = relationship()
    images: Mapped[List["PostImage"]] = relationship(back_populates="post", cascade="all, delete-orphan")

