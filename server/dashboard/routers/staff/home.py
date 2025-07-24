# dashboard/routers/home.py
"""
Router pentru home dashboard cu statistici - ACTUALIZAT pentru coșuri.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from cfg import get_db, SECRET_KEY, ALGORITHM
from models import Client, UserStatus, Vendor, Order, OrderStatus, UserRequest, Staff, Product, Cart, CartItem, \
    StaffRole

from server.dashboard.dependencies import get_current_staff, get_template_context, require_role
from server.dashboard.routers.auth import create_access_token
from server.dashboard.utils.timezone import datetime_local, time_only, date_only, datetime_iso
from services.dashboard.stats_service import DashboardStatsService
from server.dashboard.websocket import notification_manager, get_current_staff_ws

home_router = APIRouter()

templates = Jinja2Templates(directory="server/dashboard/templates/staf")
templates.env.filters['datetime_local'] = datetime_local
templates.env.filters['time_only'] = time_only
templates.env.filters['date_only'] = date_only


@home_router.get("/", response_class=HTMLResponse)
async def dashboard_home(
        request: Request,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagina principală dashboard cu statistici actualizate pentru coșuri."""
    # Get stats cu coșuri incluse
    stats = await DashboardStatsService.get_dashboard_stats(db)

    # Get recent activity
    recent_activity = await DashboardStatsService.get_recent_activity(db, limit=10)

    # Get recent carts
    recent_carts = await DashboardStatsService.get_recent_carts(db, limit=5)

    # Get base context
    context = await get_template_context(request, staff)

    # Add stats to context
    context.update({
        "stats": stats,
        "recent_activity": recent_activity,
        "recent_carts": recent_carts,
        "page_title": "Dashboard",
        "datetime_iso": datetime_iso
    })

    return templates.TemplateResponse("home/index.html", context)


# Actualizare pentru endpoint-ul de notificări
@home_router.get("/api/notifications")
async def get_notifications(
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """API endpoint pentru notificări cu coșuri incluse."""
    # Count new orders
    new_orders = await db.execute(
        select(func.count(Order.id))
        .where(Order.status == OrderStatus.NEW)
    )
    new_orders_count = new_orders.scalar() or 0

    # Count unprocessed requests
    new_requests = await db.execute(
        select(func.count(UserRequest.id))
        .where(UserRequest.is_processed == False)
    )
    new_requests_count = new_requests.scalar() or 0

    # Count active carts (updated in last 24h with items)
    active_carts = await db.execute(
        select(func.count(Cart.id.distinct()))
        .join(CartItem)
        .where(Cart.updated_at >= datetime.utcnow() - timedelta(hours=24))
    )
    active_carts_count = active_carts.scalar() or 0

    return {
        "new_orders": new_orders_count,
        "new_requests": new_requests_count,
        "active_carts": active_carts_count,
        "total": new_orders_count + new_requests_count
    }


# Restul codului rămâne la fel...
@home_router.get("/stats", response_class=HTMLResponse)
async def dashboard_stats(
        request: Request,
        period: str = "week",
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagină statistici detaliate."""
    # Validate period
    if period not in ["today", "week", "month", "year"]:
        period = "week"

    # Get detailed stats
    stats = await DashboardStatsService.get_detailed_stats(db, period)

    # Get charts data
    charts_data = await DashboardStatsService.get_charts_data(db, period)

    # Get base context
    context = await get_template_context(request, staff)

    context.update({
        "stats": stats,
        "charts_data": charts_data,
        "period": period,
        "page_title": "Statistici Detaliate"
    })

    return templates.TemplateResponse("home/stats.html", context)


@home_router.get("/activity", response_class=HTMLResponse)
async def dashboard_activity(
        request: Request,
        page: int = 1,
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Pagină activitate recentă."""
    per_page = 50
    offset = (page - 1) * per_page

    # Get activity
    activity_items = await DashboardStatsService.get_recent_activity(
        db,
        limit=per_page,
        offset=offset
    )

    # Get total count
    total_count = await DashboardStatsService.get_activity_count(db)
    total_pages = (total_count + per_page - 1) // per_page

    # Get base context
    context = await get_template_context(request, staff)

    context.update({
        "activity_items": activity_items,
        "page": page,
        "total_pages": total_pages,
        "page_title": "Activitate Recentă"
    })

    return templates.TemplateResponse("home/activity.html", context)


@home_router.get("/api/dashboard-stats")
async def get_dashboard_stats_api(
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """API endpoint pentru refresh dashboard stats."""
    stats = await DashboardStatsService.get_dashboard_stats(db)
    return stats


@home_router.get("/api/quick-stats")
async def get_quick_stats(
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """API endpoint pentru statistici rapide."""
    stats = await DashboardStatsService.get_quick_stats(db)
    return stats


@home_router.get("/api/dashboard-stats")
async def get_dashboard_stats(
        staff=Depends(get_current_staff)
):
    """Stats pentru dashboard incluzând WebSocket."""
    # Stats normale
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "websocket_connections": notification_manager.get_connections_count()
    }

    # DB pool stats doar pentru super_admin
    if staff.role == StaffRole.SUPER_ADMIN:
        from cfg import engine
        pool = engine.pool
        stats["db_pool"] = {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow()
        }

    return stats



# WebSocket endpoint pentru notificari
@home_router.websocket("/ws/notifications")
async def websocket_notifications(
        websocket: WebSocket,
        token: str = Query(...),
):
    """WebSocket endpoint pentru notificări real-time."""
    staff_id = None

    try:
        # Validare token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        staff_id = payload.get("sub")

        if not staff_id:
            await websocket.close(code=1008)
            return

        staff_id = int(staff_id)

        # Acceptă conexiunea ÎNAINTE de orice operație DB
        await websocket.accept()
        print(f"WS Accepted connection for staff_id: {staff_id}")

        # Verifică staff DUPĂ ce ai acceptat conexiunea
        from cfg import get_db_context

        try:
            async with get_db_context() as db:
                result = await db.execute(
                    select(Staff).where(Staff.id == staff_id)
                )
                staff = result.scalar_one_or_none()

                if not staff or not staff.is_active:
                    print(f"WS Invalid staff: {staff_id}")
                    await websocket.close(code=1008, reason="Invalid staff")
                    return

            print(f"WS Connected: Staff {staff.email} (ID: {staff_id})")

            # Conectează la manager
            await notification_manager.connect(websocket, staff_id)

            # Keep-alive loop
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            print(f"WS Disconnected: Staff ID {staff_id}")
        except Exception as e:
            print(f"WS Error in loop: {type(e).__name__}: {e}")
            if websocket.client_state.value == 1:  # Still connected
                await websocket.close(code=1011, reason="Internal error")

    except jwt.ExpiredSignatureError:
        print("WS Error: Token expired")
        if websocket.client_state.value == 0:  # Not yet accepted
            await websocket.close(code=1008)
    except jwt.JWTError as e:
        print(f"WS Error: Invalid token - {e}")
        if websocket.client_state.value == 0:
            await websocket.close(code=1008)
    except Exception as e:
        print(f"WS Error: {type(e).__name__}: {e}")
        if websocket.client_state.value == 0:
            await websocket.close(code=1011)

    finally:
        # Cleanup
        if staff_id:
            await notification_manager.disconnect(websocket, staff_id)







@home_router.get("/api/db-stats")
async def get_db_stats(
        staff=Depends(get_current_staff),
        _=Depends(require_role(["super_admin"]))
):
    """Returnează statistici despre conexiunile DB."""
    from cfg import engine

    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.total()
    }


@home_router.get("/api/ws-token")
async def get_ws_token(
        staff=Depends(get_current_staff)
):
    """Returnează token pentru WebSocket."""
    access_token = create_access_token(
        data={"sub": str(staff.id)},
        expires_delta=timedelta(hours=1)
    )
    return {"token": access_token}

@home_router.get("/api/recent-activity-partial")
async def get_recent_activity_partial(
        staff=Depends(get_current_staff),
        db: AsyncSession = Depends(get_db)
):
    """Returnează date pentru recent activity."""
    recent_activity = await DashboardStatsService.get_recent_activity(db, limit=8)

    return {
        "items": [
            {
                "type": activity.get("type"),  # IMPORTANT: adaugă type
                "link": activity.get("link", "#"),
                "color": activity.get("color", "primary"),
                "icon": activity.get("icon", "bi-info-circle"),
                "title": activity.get("title", ""),
                "description": activity.get("description", ""),
                "timestamp": time_only(activity.get("timestamp"))
            }
            for activity in recent_activity
        ]
    }