# server/dashboard/router.py
"""
Router principal pentru Dashboard Module.
"""
from fastapi import APIRouter, Depends, Request, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional



from .config import DashboardConfig, default_config
from .dependencies import get_current_staff, require_role, get_current_vendor_staff, get_current_user
from .routers import (
    auth_router,
    # home_router,
    # user_request_router,
    # client_router,
    # staff_router,
    # vendor_router,
    # vendor_home_router,  # Use vendor_home_router for vendor dashboard
    # category_router,
    # products_router,
    # product_image_router,
    # product_price_router,
    # cart_router,
    #
    # order_router,
#     import_router,
#     export_router
)

from .routers.staff_router import staff_dashboard_router
from .routers.vendor_router import vendor_dashboard_router



def create_dashboard_router(
        config: Optional[DashboardConfig] = None,
        prefix: Optional[str] = None
) -> APIRouter:
    """
    Creează router pentru dashboard cu configurarea specificată.

    Args:
        config: Configurare dashboard (optional)
        prefix: Prefix pentru rute (override config.base_route)

    Returns:
        APIRouter configurat
    """
    # Use provided config or default
    cfg = config or default_config
    base_prefix = prefix or cfg.base_route

    # Create main router
    dashboard = APIRouter(
        prefix=base_prefix,
        tags=["dashboard"],
        responses={404: {"description": "Not found"}}
    )

    # Test WebSocket direct pe dashboard router
    @dashboard.websocket("/test-ws")
    async def test_websocket(websocket: WebSocket):
        print("TEST WS - Someone trying to connect!")
        await websocket.accept()
        await websocket.send_text("Hello from test!")
        await websocket.close()






    # Root redirect temporar
    # @dashboard.get("/", response_class=HTMLResponse)
    # async def dashboard_root(request: Request):
    #     """Redirect la login pentru test."""
    #     return RedirectResponse(url=f"{base_prefix}/auth/login")


    # Include sub-routers

    dashboard.include_router(
        auth_router,
        prefix="/auth",
        tags=["dashboard-auth"]
    )


    dashboard.include_router(staff_dashboard_router)
    dashboard.include_router(vendor_dashboard_router)


    # Root redirect
    @dashboard.get("/", response_class=HTMLResponse)
    async def dashboard_root(
            request: Request,
            user=Depends(get_current_user)
    ):
        """Redirect la home dashboard."""

        if hasattr(user, "role"):  # ai grijă, rolul poate avea value, deci comparații directe
            # Staff
            if user.__class__.__name__ == "Staff":
                return RedirectResponse(url=f"{base_prefix}/staff/home")
            # Vendor
            elif user.__class__.__name__ == "VendorStaff":
                return RedirectResponse(url=f"{base_prefix}/vendor/home")
            # fallback (de ex. nu-i logat)
        return RedirectResponse(url=f"{base_prefix}/auth/login")




    # dashboard.include_router(
    #     home_router,
    #     prefix="/home",
    #     tags=["dashboard-home"],
    #     # dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     client_router,
    #     prefix="/client",
    #     tags=["dashboard-client"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     staff_router,
    #     prefix="/staff",
    #     tags=["dashboard-staff"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     vendor_router,
    #     prefix="/vendor",
    #     tags=["dashboard-vendor"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     category_router,
    #     prefix="/category",
    #     tags=["dashboard-category"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     products_router,
    #     prefix="/product",
    #     tags=["dashboard-product"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # # Include product_images router
    # dashboard.include_router(
    #     product_image_router,
    #     prefix="/product_image",
    #     tags=["dashboard-product-image"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    #
    # # Include product_prices router
    # dashboard.include_router(
    #     product_price_router,
    #     prefix="/product_price",
    #     tags=["dashboard-product-price"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     cart_router,
    #     prefix="/cart",
    #     tags=["dashboard-cart"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     order_router,
    #     prefix="/order",
    #     tags=["dashboard-order"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    #
    # dashboard.include_router(
    #     user_request_router,
    #     prefix="/user_request",
    #     tags=["dashboard-user-request"],
    #     dependencies=[Depends(get_current_staff)]
    # )


    # dashboard.include_router(
    #     vendor_home_router,
    #     prefix="/vendor/home",
    #     tags=["vendor-dashboard-home"],
    #     dependencies=[Depends(get_current_vendor_staff)]
    # )


    # # Models routers (cu permisiuni)
    # dashboard.include_router(
    #     users_router,
    #     prefix="/users",
    #     tags=["dashboard-users"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     products_router,
    #     prefix="/products",
    #     tags=["dashboard-products"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # dashboard.include_router(
    #     orders_router,
    #     prefix="/orders",
    #     tags=["dashboard-orders"],
    #     dependencies=[Depends(get_current_staff)]
    # )
    #
    # # Import/Export routers (doar pentru Manager+)
    # if cfg.enable_import:
    #     dashboard.include_router(
    #         import_router,
    #         prefix="/import",
    #         tags=["dashboard-import"],
    #         dependencies=[Depends(require_role(["super_admin", "manager"]))]
    #     )
    #
    # if cfg.enable_export:
    #     dashboard.include_router(
    #         export_router,
    #         prefix="/export",
    #         tags=["dashboard-export"],
    #         dependencies=[Depends(get_current_staff)]
    #     )

    # Error handlers
    # @dashboard.exception_handler(404)
    # async def dashboard_not_found(request: Request, exc):
    #     """404 page pentru dashboard."""
    #     return HTMLResponse(
    #         content="<h1>404 - Pagină negăsită</h1>",
    #         status_code=404
    #     )
    #
    # @dashboard.exception_handler(403)
    # async def dashboard_forbidden(request: Request, exc):
    #     """403 page pentru dashboard."""
    #     return HTMLResponse(
    #         content="<h1>403 - Acces interzis</h1>",
    #         status_code=403
    #     )

    return dashboard


# Funcție helper pentru integrare ușoară
def setup_dashboard(app, config: Optional[DashboardConfig] = None):
    """
    Setup rapid pentru dashboard în aplicația FastAPI.

    Usage:
        from dashboard import setup_dashboard

        app = FastAPI()
        setup_dashboard(app)
    """
    dashboard_router = create_dashboard_router(config)


    # Mount static files for dashboard
    app.mount(
        "/dashboard-static",
        StaticFiles(directory="server/dashboard/static", html=True),
        name="dashboard_static"
    )


    app.include_router(dashboard_router)

    return dashboard_router