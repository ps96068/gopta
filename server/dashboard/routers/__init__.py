# dashboard/routers/__init__.py
"""
Dashboard routers.
"""
from .auth import auth_router

# Import other routers as they are created
from server.dashboard.routers.staff.home import home_router
# from .client import client_router
# from .staff import staff_router
# from .vendor import vendor_router
# from .vendors.home import vendor_home_router
# from .category import category_router
# from .products import products_router
# from .product_image import product_image_router
# from .product_price import product_price_router
# from .cart import cart_router
# from .order import order_router
#
# from .user_request import user_request_router
#
# __all__ = [
#     "auth_router",
#     "home_router",
#     "user_request_router",
#     "client_router",
#     "staff_router",
#     "vendor_router",
#     "vendor_home_router",
#     "category_router",
#     "products_router",
#
#     "product_image_router",
#     "product_price_router",
#     'cart_router',
#     "order_router",
#     # "import_router",
#     # "export_router"
# ]

