# server/dashboard/routers/staff_router.py


from fastapi import APIRouter, Depends, HTTPException

from server.dashboard.dependencies import get_current_staff
from .staff.analytics import analytics_router

from .staff.home import home_router
from .staff.client import client_router
from .staff.import_products import import_router
from .staff.staff import staff_router
from .staff.vendor import vendor_router
from .staff.category import category_router
from .staff.products import products_router
from .staff.product_image import product_image_router
from .staff.product_price import product_price_router
from .staff.cart import cart_router
from .staff.order import order_router
from .staff.user_request import user_request_router
from .staff.vendor_company import vendor_company_router
from .staff.vendor_staff import vendor_staff_router
from .staff.invoice import invoice_router
from .staff.post import post_router
from .staff.post_image import post_image_router

staff_dashboard_router = APIRouter(
    prefix="/staff",
    tags=["dashboard-staff"]
)



# Toate rutele sub staff trebuie să ceară staff autentificat
staff_dashboard_router.include_router(
    home_router,
    prefix="/home",
    tags=["dashboard-home"]
)

staff_dashboard_router.include_router(
    client_router,
    prefix="/client",
    tags=["dashboard-client"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    staff_router,
    prefix="/staff",
    tags=["dashboard-staff"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    vendor_router,
    prefix="/vendor",
    tags=["dashboard-vendor"],
    dependencies=[Depends(get_current_staff)]
)


staff_dashboard_router.include_router(
    vendor_company_router,
    prefix="/vendor_company",
    tags=["dashboard-vendor-company"],
    dependencies=[Depends(get_current_staff)]
)


staff_dashboard_router.include_router(
    vendor_staff_router,
    prefix="/vendor_staff",
    tags=["dashboard-vendor-staff"],
    dependencies=[Depends(get_current_staff)]
)


staff_dashboard_router.include_router(
    category_router,
    prefix="/category",
    tags=["dashboard-category"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    products_router,
    prefix="/product",
    tags=["dashboard-product"],
    dependencies=[Depends(get_current_staff)]
)

# Include product_images router
staff_dashboard_router.include_router(
    product_image_router,
    prefix="/product_image",
    tags=["dashboard-product-image"],
    dependencies=[Depends(get_current_staff)]
)

# Include product_prices router
staff_dashboard_router.include_router(
    product_price_router,
    prefix="/product_price",
    tags=["dashboard-product-price"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    cart_router,
    prefix="/cart",
    tags=["dashboard-cart"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    order_router,
    prefix="/order",
    tags=["dashboard-order"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    user_request_router,
    prefix="/user_request",
    tags=["dashboard-user-request"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    invoice_router,
    prefix="/invoice",
    tags=["staff-invoice"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    post_router,
    prefix="/post",
    tags=["post"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    post_image_router,
    prefix="/post_image",
    tags=["post-image"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["dashboard-analytics"],
    dependencies=[Depends(get_current_staff)]
)

staff_dashboard_router.include_router(
    import_router,
    prefix="/import",
    tags=["dashboard-import"],
    dependencies=[Depends(get_current_staff)]
)

