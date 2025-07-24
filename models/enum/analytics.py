# models/enum/analytics.py




import enum
class RequestType(enum.Enum):
    """Tipuri de cereri utilizator."""
    PRICE_REQUEST = "price_request"  # Cerere preț mai bun
    BULK_ORDER = "bulk_order"  # Comandă în cantitate mare
    PRODUCT_INFO = "product_info"  # Informații suplimentare produs
    CUSTOM_REQUEST = "custom_request"  # Cerere personalizată


class TargetType(enum.Enum):
    """Tipuri de ținte pentru interacțiuni."""
    PRODUCT = "product"
    CATEGORY = "category"
    BLOG = "blog"
    CART = "cart"


class ActionType(enum.Enum):
    """Tipuri de acțiuni pentru interacțiuni."""
    VIEW = "view"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    REQUEST_QUOTE = "request_quote"
    SHARE = "share"
