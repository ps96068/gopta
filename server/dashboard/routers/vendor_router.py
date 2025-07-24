# server/dashboard/routers/vendor_router.py

from fastapi import APIRouter, Depends, HTTPException

from server.dashboard.dependencies import get_current_vendor_staff

from server.dashboard.routers.vendors.home import vendor_home_router
from server.dashboard.routers.vendors.products import vendor_products_router
from server.dashboard.routers.vendors.team import vendor_team_router

vendor_dashboard_router = APIRouter(
    prefix="/vendor",
    tags=["dashboard-vendor"]
)



# Toate rutele sub vendor trebuie să ceară vendor autentificat


# Home dashboard pentru vendor
vendor_dashboard_router.include_router(
    vendor_home_router,
    prefix="/home",
    tags=["vendor-home"],
    dependencies=[Depends(get_current_vendor_staff)]
)

# Produse vendor
vendor_dashboard_router.include_router(
    vendor_products_router,
    prefix="/product",
    tags=["vendor-products"],
    dependencies=[Depends(get_current_vendor_staff)]
)

# Echipa vendor
vendor_dashboard_router.include_router(
    vendor_team_router,
    prefix="/team",
    tags=["vendor-team"],
    dependencies=[Depends(get_current_vendor_staff)]
)

#
# # Comenzi vendor
# vendor_dashboard_router.include_router(
#     vendor_orders_router,
#     prefix="/order",
#     tags=["vendor-orders"],
#     dependencies=[Depends(get_current_vendor_staff)]
# )
#
# # Cereri clienți
# vendor_dashboard_router.include_router(
#     vendor_requests_router,
#     prefix="/user_request",
#     tags=["vendor-requests"],
#     dependencies=[Depends(get_current_vendor_staff)]
# )
#
# # Profil companie
# vendor_dashboard_router.include_router(
#     vendor_company_router,
#     prefix="/company",
#     tags=["vendor-company"],
#     dependencies=[Depends(get_current_vendor_staff)]
# )
#
# # Analytics
# vendor_dashboard_router.include_router(
#     vendor_analytics_router,
#     prefix="/analytics",
#     tags=["vendor-analytics"],
#     dependencies=[Depends(get_current_vendor_staff)]
# )
#
