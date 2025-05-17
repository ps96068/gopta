from contextvars import ContextVar

current_staff_id: ContextVar[int | None] = ContextVar(
    "current_staff_id", default=None
)