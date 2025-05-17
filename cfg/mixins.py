from sqlalchemy import ForeignKey, event
from sqlalchemy.orm import Mapped, mapped_column
from utils.context import current_staff_id

class AuditMixin:
    """
    Adaugă automat:
      created_by  – staff ID la inserare
      modified_by – staff ID la orice update
    """
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    modified_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )


# ─── Listener global aplicat tuturor claselor ce moștenesc AuditMixin ───
@event.listens_for(AuditMixin, "before_insert", propagate=True)
def _set_created_by(mapper, connection, target):
    staff_id = current_staff_id.get()
    if target.created_by is None:
        target.created_by = staff_id
    target.modified_by = staff_id   # inițial identic

@event.listens_for(AuditMixin, "before_update", propagate=True)
def _set_modified_by(mapper, connection, target):
    target.modified_by = current_staff_id.get()