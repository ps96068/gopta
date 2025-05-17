from __future__ import annotations

from datetime import datetime
from sqlalchemy import Index, String, ForeignKey, DateTime, Integer, CheckConstraint, event
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import CreatedAtMixin, UpdatedAtMixin



# models/marketing/user_activity.py

class UserActivity(Base, CreatedAtMixin):
    __tablename__ = "user_activity"
    __table_args__ = (
        CheckConstraint(
            "(session_end IS NULL) OR (session_end >= session_start)",
            name="chk_session_times",
        ),
        CheckConstraint(
            "session_duration IS NULL OR session_duration >= 0",
            name="chk_duration_positive",
        ),
        Index("ix_activity_client_time", "client_id", "session_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # Începutul sesiunii
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)  # Sfârșitul sesiunii (null dacă sesiunea este încă activă)
    session_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Durata sesiunii, calculată la final

    # Relație
    client: Mapped["Client"] = relationship("Client", back_populates="activities")


    # @property
    # def calculated_session_duration(self) -> int | None:
    #     if self.session_end:
    #         delta = self.session_end - self.session_start
    #         return int(delta.total_seconds())
    #     return None



    # ─────────── Validators ───────────
    @validates("session_end")
    def _validate_end(self, key, ses_end):
        if ses_end and ses_end < self.session_start:
            raise ValueError("session_end nu poate fi anterior lui session_start")

        if ses_end:
            delta = ses_end - self.session_start
            self.session_duration = int(delta.total_seconds())
        return ses_end


    def __repr__(self):
        return f"<UserActivity(id={self.id}, client_id='{self.client_id}', session_start='{self.session_start}', session_end='{self.session_end}', session_duration='{self.session_duration}')>"


# @event.listens_for(UserActivity, "before_update")
# def calculate_session_duration(mapper, connection, target):
#     if target.session_end:
#         delta = target.session_end - target.session_start
#         target.session_duration = int(delta.total_seconds())
#
#
