# models/enum/notification.py

import enum




class NotificationType(enum.Enum):
    """Tipuri de notificări."""
    ORDER_CREATED = "order_created"
    ORDER_STATUS_CHANGED = "order_status_changed"
    REQUEST_RESPONSE = "request_response"
    PRICE_ALERT = "price_alert"
    PRODUCT_BACK_IN_STOCK = "product_back_in_stock"
    CART_REMINDER = "cart_reminder"
    PROMOTIONAL = "promotional"


class NotificationChannel(enum.Enum):
    """Canale de notificare."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    BOTH = "both"


class NotificationStatus(enum.Enum):
    """Status notificare."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"