from __future__ import annotations

from datetime import datetime
import enum
from sqlalchemy import Index, CheckConstraint, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func



# from database import Base
from cfg import Base
from models.base import CreatedAtMixin, UpdatedAtMixin
from models.blog.post import Post


# models/blog/post_edit_history.py

class ModificationTypeEnum(enum.Enum):
    created      = "created"
    edited       = "edited"
    image_added  = "image_added"

class PostEditHistory(Base, CreatedAtMixin):
    __tablename__ = "post_edit_history"
    __table_args__ = (
        CheckConstraint("old_content IS NOT NULL OR modification_type='created'",
                        name="chk_post_history_content"),
        Index("ix_post_history_post_time", "post_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    changed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True, index=True
    )
    modification_type: Mapped[ModificationTypeEnum] = mapped_column(
        String(32), nullable=False
    )
    old_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relații
    post:  Mapped["Post"]  = relationship("Post",  back_populates="edit_history")
    staff: Mapped["Staff"] = relationship("Staff", foreign_keys=[changed_by])

    def __repr__(self) -> str:
        return (
            f"<PostEditHistory(id={self.id}, post_id={self.post_id}, "
            f"type={self.modification_type}, by={self.changed_by})>"
        )

# @event.listens_for(Post, "before_update", propagate=True)
# def add_edit_history(mapper, connection, target: Post):
#     history = PostEditHistory(
#         post_id=target.id,
#         changed_by=target.modified_by,              # presupunem că setezi `modified_by` în serviciu
#         modification_type="edited",
#         content_snapshot=target.content             # snapshot înainte de commit
#     )
#     connection.execute(PostEditHistory.__table__.insert(), history.__dict__)
#
#
