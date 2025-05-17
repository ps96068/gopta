from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func



from cfg import Base
from models.base import CreatedAtMixin, UpdatedAtMixin, IsActiveMixin


# models/blog/post.py

class Post(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    __tablename__ = "posts"
    __table_args__ = (
        Index(
            "idx_post_is_active_publish_date",
            "is_active",
            "publish_date"
        ),
    )

    # ---------- Coloane ----------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.id"), nullable=False, index=True
    )
    publish_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    modified_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("staff.id"),
        nullable=True
    )

    # ---------- Relații ----------
    post_author: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[author_id],
        back_populates="posts"
    )
    modifier: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[modified_by],
    )
    images: Mapped[list["PostImage"]] = relationship(
        "PostImage",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    edit_history: Mapped[list["PostEditHistory"]] = relationship(
        "PostEditHistory",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        primaryjoin=(
            "and_("
            "Post.id==foreign(UserInteraction.target_id),"
            "UserInteraction.target_type=='post'"
            ")"
        ),
        back_populates="post",
        overlaps="category,product,post,interactions"
    )

    # ---------- Validatori ----------
    @validates("title")
    def validate_title(self, key, value: str) -> str:
        if not value.strip():
            raise ValueError("Titlul nu poate fi gol sau doar spații albe.")
        return value

    @validates("is_active")
    def validate_is_active(self, key, value: bool) -> bool:
        from datetime import datetime, timezone
        if value and self.publish_date > datetime.now(timezone.utc):
            raise ValueError(
                "Postarea nu poate fi activă înainte de data de publicare."
            )
        return value

    # ---------- Repr & Str ----------
    def __repr__(self) -> str:
        return (
            f"<Post(id={self.id}, title='{self.title}', "
            f"is_active={self.is_active}, publish_date={self.publish_date})>"
        )

    def __str__(self):
        return f"Post: {self.id}_{self.title}"

