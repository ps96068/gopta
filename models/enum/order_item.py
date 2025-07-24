# models/enum/order_item.py

import enum


class OrderItemStatus(enum.Enum):
    """
    Statusuri pentru order items în context multi-vendor.
    În MVP, toate items au același status ca Order.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"