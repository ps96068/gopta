# server/dashboard/routers/vendor/home.py
"""
Router pentru vendor home dashboard.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct, or_
from sqlalchemy.orm import selectinload

from cfg import get_db
from models import Product, Order, OrderStatus, OrderItem, UserRequest, VendorStaff, Cart, CartItem
from server.dashboard.dependencies import get_current_vendor_staff, get_template_context
from server.dashboard.utils.timezone import datetime_local, time_only, date_only
from services.models import VendorCompanyService

vendor_home_router = APIRouter()
templates = Jinja2Templates(directory="server/dashboard/templates/vend")

templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@vendor_home_router.get("/", response_class=HTMLResponse)
async def vendor_dashboard_home(
        request: Request,
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagina principală dashboard vendor."""

#     company_id = vendor_staff.company_id
#     now = datetime.utcnow()
#     month_ago = now - timedelta(days=30)
#
#     # Statistici companie
#     stats = await VendorCompanyService.get_statistics(db, company_id)
#
#     # Produse active/inactive
#     active_products = await db.execute(
#         select(func.count(Product.id))
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 Product.is_active == True,
#                 Product.in_stock == True
#             )
#         )
#     )
#     stats['active_products'] = active_products.scalar() or 0
#
#     inactive_products = await db.execute(
#         select(func.count(Product.id))
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 or_(
#                     Product.is_active == False,
#                     Product.in_stock == False
#                 )
#             )
#         )
#     )
#     stats['inactive_products'] = inactive_products.scalar() or 0
#
#     # Comenzi noi (pentru produsele vendorului)
#     new_orders = await db.execute(
#         select(func.count(distinct(Order.id)))
#         .select_from(Order)
#         .join(OrderItem)
#         .join(Product)
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 Order.status == OrderStatus.NEW
#             )
#         )
#     )
#     stats['new_orders'] = new_orders.scalar() or 0
#
#     # Cereri în așteptare pentru produsele vendorului
#     pending_requests = await db.execute(
#         select(func.count(UserRequest.id))
#         .join(Product)
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 UserRequest.is_processed == False
#             )
#         )
#     )
#     stats['pending_requests'] = pending_requests.scalar() or 0
#
#     # Recent orders pentru vendor
#     recent_orders_query = await db.execute(
#         select(Order, OrderItem)
#         .join(OrderItem)
#         .join(Product)
#         .where(Product.vendor_company_id == company_id)
#         .order_by(Order.created_at.desc())
#         .limit(10)
#     )
#     recent_orders = []
#     for order, item in recent_orders_query:
#         recent_orders.append({
#             'order': order,
#             'item': item,
#             'subtotal': float(item.subtotal)
#         })
#
#     # Context pentru template
#     context = await get_template_context(request, vendor_staff)
#     context.update({
#         "stats": stats,
#         "recent_orders": recent_orders,
#         "page_title": "Dashboard Vendor"
#     })
#
#     return templates.TemplateResponse("home/vendor.html", context)
#
#

    result = await db.execute(
        select(VendorStaff).options(selectinload(VendorStaff.company)).where(VendorStaff.id == vendor_staff.id)
    )
    vendor_staff = result.scalar_one()




    company_id = vendor_staff.company_id
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    # Statistici produse
    total_products = await db.execute(
        select(func.count(Product.id))
        .where(Product.vendor_company_id == company_id)
    )
    total_products_count = total_products.scalar() or 0

    active_products = await db.execute(
        select(func.count(Product.id))
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Product.is_active == True,
                Product.in_stock == True
            )
        )
    )
    active_products_count = active_products.scalar() or 0

    # Comenzi pentru produsele vendor-ului
    vendor_orders = await db.execute(
        select(func.count(func.distinct(Order.id)))
        .select_from(Order)
        .join(OrderItem)
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Order.created_at >= month_ago
            )
        )
    )
    total_orders = vendor_orders.scalar() or 0

    # Venituri luna curentă
    revenue = await db.execute(
        select(func.sum(OrderItem.subtotal))
        .select_from(OrderItem)
        .join(Product)
        .join(Order)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Order.created_at >= month_ago,
                Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED])
            )
        )
    )
    monthly_revenue = float(revenue.scalar() or 0)

    # Cereri neprocesate pentru produsele vendor-ului
    pending_requests = await db.execute(
        select(func.count(UserRequest.id))
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                UserRequest.is_processed == False
            )
        )
    )
    pending_requests_count = pending_requests.scalar() or 0

    # Coșuri active cu produse vendor
    active_carts = await db.execute(
        select(func.count(func.distinct(Cart.id)))
        .select_from(Cart)
        .join(CartItem)
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Cart.updated_at >= now - timedelta(hours=24)
            )
        )
    )
    active_carts_count = active_carts.scalar() or 0

    # Comenzi recente
    recent_orders_query = await db.execute(
        select(Order)
        .join(OrderItem)
        .join(Product)
        .where(Product.vendor_company_id == company_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .distinct()
    )
    recent_orders = recent_orders_query.scalars().all()

    stats = {
        "total_products": total_products_count,
        "active_products": active_products_count,
        "total_orders": total_orders,
        "monthly_revenue": monthly_revenue,
        "pending_requests": pending_requests_count,
        "active_carts": active_carts_count,
        "commission_rate": float(vendor_staff.company.commission_rate),
        "commission_due": monthly_revenue * float(vendor_staff.company.commission_rate) / 100
    }

    context = await get_template_context(request, vendor_staff)
    context.update({
        "page_title": "Dashboard",
        "stats": stats,
        "recent_orders": recent_orders
    })

    return templates.TemplateResponse("/home/index.html", context)


@vendor_home_router.get("/api/notifications")
async def get_vendor_notifications(
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """API endpoint pentru notificări vendor."""
    company_id = vendor_staff.company_id

    # Count new orders pentru produsele vendorului
    new_orders = await db.execute(
        select(func.count(func.distinct(Order.id)))
        .select_from(Order)
        .join(OrderItem)
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Order.status == OrderStatus.NEW
            )
        )
    )
    new_orders_count = new_orders.scalar() or 0

    # Count pending requests
    new_requests = await db.execute(
        select(func.count(UserRequest.id))
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                UserRequest.is_processed == False
            )
        )
    )
    new_requests_count = new_requests.scalar() or 0

    # Count active carts
    active_carts = await db.execute(
        select(func.count(func.distinct(Cart.id)))
        .select_from(Cart)
        .join(CartItem)
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Cart.updated_at >= datetime.utcnow() - timedelta(hours=24)
            )
        )
    )
    active_carts_count = active_carts.scalar() or 0

    return {
        "orders": new_orders_count,
        "requests": new_requests_count,
        "carts": active_carts_count,
        "total": new_orders_count + new_requests_count
    }


# @vendor_home_router.get("/api/notifications")
# async def get_vendor_notifications(
#         vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
#         db: AsyncSession = Depends(get_db)
# ):
#     """API endpoint pentru notificări vendor."""
#     company_id = vendor_staff.company_id
#
#     # Count new orders pentru produsele vendorului
#     new_orders = await db.execute(
#         select(func.count(distinct(Order.id)))
#         .select_from(Order)
#         .join(OrderItem)
#         .join(Product)
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 Order.status == OrderStatus.NEW
#             )
#         )
#     )
#     new_orders_count = new_orders.scalar() or 0
#
#     # Count pending requests
#     new_requests = await db.execute(
#         select(func.count(UserRequest.id))
#         .join(Product)
#         .where(
#             and_(
#                 Product.vendor_company_id == company_id,
#                 UserRequest.is_processed == False
#             )
#         )
#     )
#     new_requests_count = new_requests.scalar() or 0
#
#     return {
#         "new_orders": new_orders_count,
#         "new_requests": new_requests_count,
#         "total": new_orders_count + new_requests_count
#     }
#
#
# @vendor_home_router.get("/api/ws-token")
# async def get_vendor_ws_token(
#         vendor_staff: VendorStaff = Depends(get_current_vendor_staff)
# ):
#     """Returnează token pentru WebSocket vendor."""
#     from server.dashboard.routers.auth import create_access_token
#
#     access_token = create_access_token(
#         data={
#             "sub": str(vendor_staff.id),
#             "user_type": "vendor",
#             "vendor_company_id": vendor_staff.company_id
#         },
#         expires_delta=timedelta(hours=1)
#     )
#     return {"token": access_token}






@vendor_home_router.get("/api/stats")
async def get_vendor_stats(
        vendor_staff: VendorStaff = Depends(get_current_vendor_staff),
        db: AsyncSession = Depends(get_db)
):
    """API endpoint pentru statistici vendor."""
    company_id = vendor_staff.company_id

    # Quick stats
    new_orders = await db.execute(
        select(func.count(func.distinct(Order.id)))
        .select_from(Order)
        .join(OrderItem)
        .join(Product)
        .where(
            and_(
                Product.vendor_company_id == company_id,
                Order.status == OrderStatus.NEW
            )
        )
    )

    return {
        "new_orders": new_orders.scalar() or 0,
        "timestamp": datetime.utcnow().isoformat()
    }