import re
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Integer, CheckConstraint, Text
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column, Relationship
from sqlalchemy.sql import func



from database import Base


class MessageStatus(enum.Enum):
    pending = "pending"
    resolved = "resolved"
    rejected = "rejected"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), default=MessageStatus.pending, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    # Relații
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

