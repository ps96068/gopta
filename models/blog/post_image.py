# models/blog/post_image.py
"""
PostImage model pentru imaginile articolelor blog.

Fiecare articol poate avea maxim 5 imagini:
- 1 imagine principală (hero/featured)
- 4 imagini pentru conținut

Imaginile sunt stocate local și șterse fizic la eliminare.

Business Rules:
- Maxim 5 imagini per post
- O singură imagine principală
- Ordine afișare 0 pentru primary, 1-4 pentru content
- Ștergere fizică a fișierului la delete
- Format: jpg, jpeg, png
- Dimensiune max: 2MB
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING


from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Post


class PostImage(Base, CreatedAtMixin):
    """Model pentru imaginile articolelor."""
    __tablename__ = "post_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)

    # Path către imagine
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # în bytes

    alt_text: Mapped[Optional[str]] = mapped_column(String(255))
    caption: Mapped[Optional[str]] = mapped_column(String(500))

    # Pentru ordonare și tip
    is_featured: Mapped[bool] = mapped_column(default=False)  # Imagine principală
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="images")


