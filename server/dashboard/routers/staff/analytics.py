# server/dashboard/routers/staff/analytics.py
"""
Analytics router pentru Staff Dashboard.
Gestionează vizualizarea datelor de tracking și analytics.
"""

from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional

from server.dashboard.utils.timezone import datetime_local, date_only, get_invoice_status
from server.dashboard.utils import decimal_to_float
from server.dashboard.utils.route_names import get_dashboard_url_for, RouteRegistry
from cfg import get_db
from models import (
    Client, UserActivity, UserInteraction, UserTargetStats,
    UserRequest, Product, Category, Order, OrderItem,
    ActionType, TargetType, UserStatus, OrderStatus
)
from server.dashboard.dependencies import get_current_staff, get_template_context
from services.models.activity_services import ActivityService

analytics_router = APIRouter()

# Create templates instance
templates = Jinja2Templates(directory="server/dashboard/templates/staf")

# Register template filters
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['date_only'] = date_only
templates.env.filters['to_float'] = decimal_to_float
templates.env.filters['get_invoice_status'] = get_invoice_status


# Register the url_for function with proper route resolution
def url_for(name: str, **params) -> str:
    """
    Generate URL for a named route.
    Handles both dashboard routes and static assets.
    """
    # Handle static routes - MOST IMPORTANT FIX
    if name == 'dashboard_static':
        path = params.get('path', '')
        # Remove leading slash if present
        if path.startswith('/'):
            path = path[1:]
        return f"/dashboard-static/{path}"

    # Handle dashboard root
    if name == 'dashboard_root':
        return '/dashboard/'

    # Analytics routes
    analytics_routes = {
        'analytics_overview': '/dashboard/staff/analytics/',
        'analytics_users': '/dashboard/staff/analytics/users',
        'analytics_products': '/dashboard/staff/analytics/products',
        'analytics_export': '/dashboard/staff/analytics/export',
        'analytics_user_journey': '/dashboard/staff/analytics/user/{client_id}/journey',
        'user_journey': '/dashboard/staff/analytics/user/{client_id}/journey'
    }

    # Dashboard staff routes
    staff_routes = {
        'client_detail': '/dashboard/staff/client/{id}',
        'clients_detail': '/dashboard/staff/client/{id}',  # alias
        'products_detail': '/dashboard/staff/product/{id}',
        'category_detail': '/dashboard/staff/category/{id}',
        'order_list': '/dashboard/staff/order',
        'user_request_list': '/dashboard/staff/user_request',
        'export_analytics': '/dashboard/staff/analytics/export'
    }

    # Combine all routes
    all_routes = {**analytics_routes, **staff_routes}

    # Check if route exists
    if name in all_routes:
        base_route = all_routes[name]
    else:
        # Default fallback
        base_route = f'/dashboard/staff/{name}'

    # Replace path parameters
    for param, value in params.items():
        if param not in ['path', '_anchor']:
            placeholder = f'{{{param}}}'
            if placeholder in base_route:
                base_route = base_route.replace(placeholder, str(value))

    # Add query parameters
    query_params = []
    for param, value in params.items():
        if param not in ['id', 'client_id', 'path', '_anchor'] and '{' + param + '}' not in all_routes.get(name, ''):
            query_params.append(f"{param}={value}")

    if query_params:
        base_route += '?' + '&'.join(query_params)

    # Add anchor if specified
    if '_anchor' in params:
        base_route += f"#{params['_anchor']}"

    return base_route


# Register the url_for function
templates.env.globals['url_for'] = url_for


@analytics_router.get("/", response_class=HTMLResponse)
async def analytics_overview(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        days: int = Query(30, description="Perioada de analiză în zile")
):
    """Dashboard Analytics Overview."""
    context = await get_template_context(request, staff)
    context['request'] = request

    since = datetime.utcnow() - timedelta(days=days)

    # 1. Metrici principale
    # Total utilizatori
    total_users = await db.execute(
        select(func.count(Client.id))
    )

    # Utilizatori noi în perioadă
    new_users = await db.execute(
        select(func.count(Client.id))
        .where(Client.created_at >= since)
    )

    # Sesiuni active azi
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    active_sessions = await db.execute(
        select(func.count(UserActivity.id))
        .where(UserActivity.session_start >= today_start)
    )

    # Conversion rate (ANONIM -> USER)
    conversions = await db.execute(
        select(
            func.count(Client.id).filter(Client.status == UserStatus.ANONIM).label('anonim'),
            func.count(Client.id).filter(Client.status != UserStatus.ANONIM).label('registered')
        )
        .where(Client.created_at >= since)
    )
    conv_data = conversions.first()
    total_new = (conv_data.anonim + conv_data.registered) if conv_data else 0
    conversion_rate = (conv_data.registered / total_new * 100) if total_new > 0 else 0

    # Bounce rate
    bounce_sessions = await db.execute(
        select(func.count(UserActivity.id))
        .where(
            and_(
                UserActivity.created_at >= since,
                UserActivity.page_views <= 1
            )
        )
    )
    total_sessions = await db.execute(
        select(func.count(UserActivity.id))
        .where(UserActivity.created_at >= since)
    )
    bounce_count = bounce_sessions.scalar() or 0
    total_count = total_sessions.scalar() or 1
    bounce_rate = (bounce_count / total_count * 100) if total_count > 0 else 0

    # 2. User status distribution
    status_dist = await db.execute(
        select(
            Client.status,
            func.count(Client.id).label('count')
        )
        .group_by(Client.status)
    )
    status_counts = {status.value: 0 for status in UserStatus}
    for row in status_dist:
        status_counts[row.status.value] = row.count

    # 3. Top viewed products
    top_products_query = await db.execute(
        select(
            Product.id,
            Product.name,
            Product.sku,
            func.count(UserInteraction.id).label('views'),
            func.count(UserInteraction.id).filter(
                UserInteraction.action_type == ActionType.ADD_TO_CART
            ).label('cart_adds')
        )
        .join(UserInteraction, and_(
            UserInteraction.target_id == Product.id,
            UserInteraction.target_type == TargetType.PRODUCT,
            UserInteraction.created_at >= since
        ))
        .group_by(Product.id, Product.name, Product.sku)
        .order_by(func.count(UserInteraction.id).desc())
        .limit(10)
    )

    top_products = []
    for row in top_products_query:
        conversion = (row.cart_adds / row.views * 100) if row.views > 0 else 0
        top_products.append({
            'id': row.id,
            'name': row.name,
            'sku': row.sku,
            'views': row.views,
            'cart_adds': row.cart_adds,
            'conversion': round(conversion, 1)
        })

    # 4. Top categories
    top_categories_query = await db.execute(
        select(
            Category.id,
            Category.name,
            func.count(UserInteraction.id).label('views')
        )
        .join(UserInteraction, and_(
            UserInteraction.target_id == Category.id,
            UserInteraction.target_type == TargetType.CATEGORY,
            UserInteraction.created_at >= since
        ))
        .group_by(Category.id, Category.name)
        .order_by(func.count(UserInteraction.id).desc())
        .limit(5)
    )

    top_categories = []
    for row in top_categories_query:
        top_categories.append({
            'id': row.id,
            'name': row.name,
            'views': row.views
        })

    # 5. Recent requests
    recent_requests_query = await db.execute(
        select(UserRequest, Client)
        .join(Client)
        .where(UserRequest.created_at >= since)
        .order_by(UserRequest.created_at.desc())
        .limit(10)
    )

    recent_requests = []
    for request_obj, client in recent_requests_query:
        recent_requests.append({
            'id': request_obj.id,
            'client_id': client.id,  # Add client_id for the link
            'client_name': f"{client.first_name or ''} {client.last_name or ''}".strip() or f"ID: {client.telegram_id}",
            'type': request_obj.request_type.value.replace('_', ' ').title(),
            'created_at': request_obj.created_at,
            'is_processed': request_obj.is_processed
        })

    # 6. Chart data - Sessions over time
    chart_labels = []
    sessions_data = []
    pageviews_data = []
    orders_data = []

    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i - 1)
        date_start = date.replace(hour=0, minute=0, second=0)
        date_end = date_start + timedelta(days=1)

        # Sessions for this day
        day_sessions = await db.execute(
            select(func.count(UserActivity.id))
            .where(
                and_(
                    UserActivity.session_start >= date_start,
                    UserActivity.session_start < date_end
                )
            )
        )

        # Page views for this day
        day_pageviews = await db.execute(
            select(func.sum(UserActivity.page_views))
            .where(
                and_(
                    UserActivity.session_start >= date_start,
                    UserActivity.session_start < date_end
                )
            )
        )

        # Orders for this day
        day_orders = await db.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    Order.created_at >= date_start,
                    Order.created_at < date_end
                )
            )
        )

        chart_labels.append(date.strftime('%d/%m'))
        sessions_data.append(day_sessions.scalar() or 0)
        pageviews_data.append(day_pageviews.scalar() or 0)
        orders_data.append(day_orders.scalar() or 0)

    # 7. Referrer sources distribution - Empty for now
    referrer_sources = {}

    # Metrics summary
    metrics = {
        'total_users': total_users.scalar() or 0,
        'new_users': new_users.scalar() or 0,
        'active_sessions': active_sessions.scalar() or 0,
        'conversion_rate': round(conversion_rate, 1),
        'bounce_rate': round(bounce_rate, 1),
        'total_sessions': total_count,
        'total_orders': await db.scalar(
            select(func.count(Order.id))
            .where(Order.created_at >= since)
        ) or 0
    }

    context.update({
        'metrics': metrics,
        'status_distribution': list(status_counts.values()),
        'status_labels': list(status_counts.keys()),
        'top_products': top_products,
        'top_categories': top_categories,
        'recent_requests': recent_requests,
        'chart_labels': chart_labels,
        'sessions_data': sessions_data,
        'pageviews_data': pageviews_data,
        'orders_data': orders_data,
        'referrer_sources': referrer_sources,
        'current_period': days
    })

    return templates.TemplateResponse(
        "analytics/overview.html",
        context
    )


@analytics_router.get("/users", response_class=HTMLResponse)
async def analytics_users(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        days: int = Query(30),
        status: Optional[str] = Query(None)
):
    """Analiză detaliată utilizatori."""
    context = await get_template_context(request, staff)
    context['request'] = request

    since = datetime.utcnow() - timedelta(days=days)

    # Build query
    query = select(
        Client.id,
        Client.telegram_id,
        Client.first_name,
        Client.last_name,
        Client.status,
        Client.created_at,
        func.count(UserActivity.id).label('sessions_count'),
        func.sum(UserActivity.page_views).label('total_pageviews'),
        func.max(UserActivity.session_start).label('last_activity')
    ).outerjoin(
        UserActivity, UserActivity.client_id == Client.id
    ).group_by(
        Client.id, Client.telegram_id, Client.first_name,
        Client.last_name, Client.status, Client.created_at
    )

    if status:
        try:
            status_filter = UserStatus[status.upper()]
            query = query.where(Client.status == status_filter)
        except KeyError:
            pass

    result = await db.execute(query.order_by(Client.created_at.desc()))

    users = []
    for row in result:
        users.append({
            'id': row.id,
            'telegram_id': row.telegram_id,
            'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or "Anonim",
            'status': row.status.value,
            'created_at': row.created_at,
            'sessions_count': row.sessions_count or 0,
            'total_pageviews': row.total_pageviews or 0,
            'last_activity': row.last_activity
        })

    context.update({
        'users': users,
        'current_status': status,
        'current_period': days
    })

    return templates.TemplateResponse(
        "analytics/users.html",
        context
    )


@analytics_router.get("/user/{client_id}/journey", response_class=HTMLResponse)
async def user_journey(
        request: Request,
        client_id: int,
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        days: int = Query(30)
):
    """User journey detaliat pentru un client."""
    context = await get_template_context(request, staff)
    context['request'] = request

    # Get client
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get journey
    journey = await ActivityService.get_user_journey(db, client_id, days)

    # Get stats
    stats = await ActivityService.get_client_stats(db, client_id)

    # Format journey for display
    journey_formatted = []
    for interaction in journey:
        # Get target name
        target_name = f"{interaction.target_type.value} #{interaction.target_id}"

        if interaction.target_type == TargetType.PRODUCT:
            product = await db.execute(
                select(Product.name).where(Product.id == interaction.target_id)
            )
            product_name = product.scalar()
            if product_name:
                target_name = product_name
        elif interaction.target_type == TargetType.CATEGORY:
            category = await db.execute(
                select(Category.name).where(Category.id == interaction.target_id)
            )
            category_name = category.scalar()
            if category_name:
                target_name = category_name

        journey_formatted.append({
            'timestamp': interaction.created_at,
            'action': interaction.action_type.value.replace('_', ' ').title(),
            'target_type': interaction.target_type.value.title(),
            'target_name': target_name,
            'target_id': interaction.target_id
        })

    context.update({
        'client': client,
        'journey': journey_formatted,
        'stats': stats,
        'current_period': days,
        'TargetType': TargetType
    })

    return templates.TemplateResponse(
        "analytics/user_journey.html",
        context
    )


@analytics_router.get("/products", response_class=HTMLResponse)
async def analytics_products(
        request: Request,
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        days: int = Query(30),
        category_id: Optional[int] = Query(None)
):
    """Analiză produse cu metrici detaliate."""
    context = await get_template_context(request, staff)
    context['request'] = request

    # Get all products analytics
    products_analytics = []

    # Base query
    query = select(Product).where(Product.is_active == True)
    if category_id:
        query = query.where(Product.category_id == category_id)

    result = await db.execute(query)
    products = result.scalars().all()

    for product in products:
        analytics = await ActivityService.get_product_analytics(db, product.id, days)
        analytics['product'] = product
        products_analytics.append(analytics)

    # Sort by views
    products_analytics.sort(key=lambda x: x['views'], reverse=True)

    # Get categories for filter
    categories = await db.execute(
        select(Category).where(Category.is_active == True)
    )

    context.update({
        'products_analytics': products_analytics[:50],  # Top 50
        'categories': categories.scalars().all(),
        'current_category': category_id,
        'current_period': days
    })

    return templates.TemplateResponse(
        "analytics/products.html",
        context
    )


@analytics_router.get("/api/stats", response_class=JSONResponse)
async def get_analytics_stats(
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        days: int = Query(7)
):
    """API endpoint pentru statistici real-time."""
    # Simple implementation
    total_sessions = await db.execute(
        select(func.count(UserActivity.id))
        .where(UserActivity.created_at >= datetime.utcnow() - timedelta(days=days))
    )

    return JSONResponse(content={
        "total_sessions": total_sessions.scalar() or 0,
        "period_days": days
    })


@analytics_router.get("/export")
async def export_analytics(
        db: AsyncSession = Depends(get_db),
        staff=Depends(get_current_staff),
        report_type: str = Query("overview"),
        days: int = Query(30),
        format: str = Query("csv")
):
    """Export date analytics în CSV/Excel."""
    # TODO: Implementare export
    return {"message": "Export functionality coming soon"}