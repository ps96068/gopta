# models/enum/order.py

import enum


class OrderStatus(enum.Enum):
    """Status-uri pentru comenzi."""
    NEW = "new"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"