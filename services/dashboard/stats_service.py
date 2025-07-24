# services/dashboard/stats_service.py
"""
Service pentru statistici dashboard.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func, and_, or_, case, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    Client, UserStatus, Vendor, Staff,
    Order, OrderStatus, OrderItem,
    Product, Category, Post,
    UserRequest, UserActivity, UserInteraction, ActionType,
    Cart, CartItem, Invoice, InvoiceType
)


class DashboardStatsService:
    """Service pentru statistici dashboard."""

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        """Obține statisticile principale pentru dashboard - ACTUALIZAT cu coșuri."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        day_ago = now - timedelta(hours=24)

        # Total users
        total_users_result = await db.execute(
            select(func.count(Client.id))
            .where(Client.is_active == True)
        )
        total_users = total_users_result.scalar() or 0

        # New users this week
        new_users_result = await db.execute(
            select(func.count(Client.id))
            .where(
                and_(
                    Client.created_at >= week_ago,
                    Client.is_active == True
                )
            )
        )
        new_users_week = new_users_result.scalar() or 0

        # Orders stats
        total_orders_result = await db.execute(
            select(func.count(Order.id))
        )
        total_orders = total_orders_result.scalar() or 0

        new_orders_result = await db.execute(
            select(func.count(Order.id))
            .where(Order.status == OrderStatus.NEW)
        )
        new_orders = new_orders_result.scalar() or 0

        completed_orders_result = await db.execute(
            select(func.count(Order.id))
            .where(
                and_(
                    Order.status == OrderStatus.COMPLETED,
                    Order.created_at >= month_ago
                )
            )
        )
        completed_orders_month = completed_orders_result.scalar() or 0

        # Revenue this month
        revenue_result = await db.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED]),
                    Order.created_at >= month_ago
                )
            )
        )
        revenue_month = float(revenue_result.scalar() or 0)

        # Pending requests
        pending_requests_result = await db.execute(
            select(func.count(UserRequest.id))
            .where(UserRequest.is_processed == False)
        )
        pending_requests = pending_requests_result.scalar() or 0

        # Active products
        active_products_result = await db.execute(
            select(func.count(Product.id))
            .where(
                and_(
                    Product.is_active == True,
                    Product.in_stock == True
                )
            )
        )
        active_products = active_products_result.scalar() or 0

        # Inactive products
        inactive_products_result = await db.execute(
            select(func.count(Product.id))
            .where(
                or_(
                    Product.is_active == False,
                    Product.in_stock == False
                )
            )
        )
        inactive_products = inactive_products_result.scalar() or 0

        # CART STATISTICS
        # Total carts cu items (nu putem avea coșuri goale)
        total_carts_result = await db.execute(
            select(func.count(distinct(Cart.id)))
            .select_from(Cart)
            .join(CartItem)
        )
        total_carts = total_carts_result.scalar() or 0

        # Active carts (coșuri cu items actualizate în ultimele 24h)
        active_carts_result = await db.execute(
            select(func.count(distinct(Cart.id)))
            .select_from(Cart)
            .join(CartItem)
            .where(Cart.updated_at >= day_ago)
        )
        active_carts = active_carts_result.scalar() or 0

        # Carts with quotes - doar oferte valide
        carts_with_quotes_result = await db.execute(
            select(func.count(distinct(Invoice.cart_id)))
            .where(
                and_(
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.valid_until > now,
                    Invoice.cart_id.isnot(None)
                )
            )
        )
        carts_with_quotes = carts_with_quotes_result.scalar() or 0

        # Abandoned carts - calculat ca diferența
        abandoned_carts = total_carts - active_carts

        # Cart conversion rate
        cart_conversion_rate = 0
        if total_carts > 0:
            # Calculăm câte comenzi au fost create în ultima lună vs coșuri create în ultima lună
            carts_last_month_result = await db.execute(
                select(func.count(distinct(Cart.id)))
                .select_from(Cart)
                .join(CartItem)
                .where(Cart.created_at >= month_ago)
            )
            carts_last_month = carts_last_month_result.scalar() or 0

            orders_last_month_result = await db.execute(
                select(func.count(Order.id))
                .where(Order.created_at >= month_ago)
            )
            orders_last_month = orders_last_month_result.scalar() or 0

            if carts_last_month > 0:
                cart_conversion_rate = (orders_last_month / carts_last_month) * 100

        # User distribution by status
        user_distribution = await db.execute(
            select(
                Client.status,
                func.count(Client.id).label('count')
            )
            .where(Client.is_active == True)
            .group_by(Client.status)
        )

        distribution_dict = {status.value: 0 for status in UserStatus}
        for row in user_distribution:
            distribution_dict[row.status.value] = row.count

        return {
            "total_users": total_users,
            "new_users_week": new_users_week,
            "total_orders": total_orders,
            "new_orders": new_orders,
            "completed_orders_month": completed_orders_month,
            "revenue_month": revenue_month,
            "pending_requests": pending_requests,
            "active_products": active_products,
            "inactive_products": inactive_products,
            "user_distribution": distribution_dict,
            # Cart stats
            "total_carts": total_carts,
            "active_carts": active_carts,
            "carts_with_quotes": carts_with_quotes,
            "abandoned_carts": abandoned_carts,
            "cart_conversion_rate": cart_conversion_rate,
            "last_updated": now
        }

    @staticmethod
    async def get_recent_activity(
            db: AsyncSession,
            limit: int = 20,
            offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Obține activitatea recentă din sistem."""
        activities = []

        # Recent orders
        orders = await db.execute(
            select(Order, Client)
            .join(Client)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        for order, client in orders:
            activities.append({
                "type": "order",
                "icon": "bi-cart-check",
                "color": "primary",
                "title": f"Comandă nouă #{order.order_number}",
                "description": f"{client.first_name or 'Client'} {client.last_name or ''} - {order.total_amount} MDL",
                "timestamp": order.created_at,
                "link": f"/dashboard/staff/orders/{order.id}"
            })

        # Recent carts
        carts = await db.execute(
            select(Cart, Client)
            .join(Client)
            .order_by(Cart.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        # for cart, client in carts:
        #     activities.append({
        #         "type": "card",
        #         "icon": "bi-cart-check",
        #         "color": "primary",
        #         "title": f"Cos nou #{cart.id}",
        #         "description": f"{client.first_name or 'Client'} {client.last_name or ''} - {cart.total_amount} MDL",
        #         "timestamp": cart.created_at,
        #         "link": f"/dashboard/cart/{cart.id}"
        #     })


        # Recent requests
        requests = await db.execute(
            select(UserRequest, Client)
            .join(Client)
            .order_by(UserRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        for request, client in requests:
            activities.append({
                "type": "request",
                "icon": "bi-envelope",
                "color": "warning",
                "title": f"Cerere nouă: {request.request_type.value}",
                "description": f"{client.first_name or 'Client'} {client.last_name or ''}",
                "timestamp": request.created_at,
                "link": f"/dashboard/staff/user_request/{request.id}"
            })

        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        return activities[:limit]

    @staticmethod
    async def get_recent_carts(
            db: AsyncSession,
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Obține coșurile recente cu detalii - CORECTAT."""
        day_ago = datetime.utcnow() - timedelta(hours=24)

        # Query optimizat pentru coșuri active
        carts_with_items = await db.execute(
            select(
                Cart.id,
                Cart.updated_at,
                Client.id.label('client_id'),
                Client.first_name,
                Client.last_name,
                func.count(distinct(CartItem.id)).label('items_count'),
                func.sum(CartItem.quantity * CartItem.price_snapshot).label('total_amount')
            )
            .select_from(Cart)
            .join(Client, Cart.client_id == Client.id)
            .join(CartItem, Cart.id == CartItem.cart_id)
            .where(Cart.updated_at >= day_ago)
            .group_by(Cart.id, Cart.updated_at, Client.id, Client.first_name, Client.last_name)
            .order_by(Cart.updated_at.desc())
            .limit(limit)
        )

        result = []
        for row in carts_with_items:
            # Check if has valid quote
            has_quote_result = await db.execute(
                select(func.count(Invoice.id))
                .where(
                    and_(
                        Invoice.cart_id == row.id,
                        Invoice.invoice_type == InvoiceType.QUOTE,
                        Invoice.valid_until > datetime.utcnow()
                    )
                )
            )
            has_quote = has_quote_result.scalar() > 0

            client_name = f"{row.first_name or 'Client'} {row.last_name or ''}".strip()

            result.append({
                "id": row.id,
                "client_name": client_name,
                "client_id": row.client_id,
                "items_count": row.items_count or 0,
                "total_amount": float(row.total_amount or 0),
                "has_quote": has_quote,
                "updated_at": row.updated_at
            })

        return result

    @staticmethod
    async def get_quick_stats(db: AsyncSession) -> Dict[str, Any]:
        """Statistici rapide pentru API."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Today's stats
        orders_today_result = await db.execute(
            select(func.count(Order.id))
            .where(Order.created_at >= today_start)
        )
        orders_today = orders_today_result.scalar() or 0

        revenue_today_result = await db.execute(
            select(func.sum(Order.total_amount))
            .where(
                and_(
                    Order.created_at >= today_start,
                    Order.status != OrderStatus.CANCELLED
                )
            )
        )
        revenue_today = float(revenue_today_result.scalar() or 0)

        users_online_result = await db.execute(
            select(func.count(UserActivity.id))
            .where(
                and_(
                    UserActivity.session_end == None,
                    UserActivity.session_start >= now - timedelta(minutes=30)
                )
            )
        )
        users_online = users_online_result.scalar() or 0

        return {
            "orders_today": orders_today,
            "revenue_today": revenue_today,
            "users_online": users_online,
            "timestamp": now
        }

    @staticmethod
    async def get_detailed_stats(
            db: AsyncSession,
            period: str = "week"
    ) -> Dict[str, Any]:
        """Statistici detaliate pentru perioada specificată."""
        now = datetime.utcnow()

        # Calculate date range
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=7)

        # Orders by status
        orders_by_status = await db.execute(
            select(
                Order.status,
                func.count(Order.id).label('count'),
                func.sum(Order.total_amount).label('total')
            )
            .where(Order.created_at >= start_date)
            .group_by(Order.status)
        )

        status_stats = {}
        for row in orders_by_status:
            status_stats[row.status.value] = {
                "count": row.count,
                "total": float(row.total or 0)
            }

        # Top products
        top_products = await db.execute(
            select(
                Product.name,
                Product.sku,
                func.sum(OrderItem.quantity).label('quantity'),
                func.sum(OrderItem.subtotal).label('revenue')
            )
            .join(OrderItem)
            .join(Order)
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(func.sum(OrderItem.subtotal).desc())
            .limit(10)
        )

        products_list = []
        for row in top_products:
            products_list.append({
                "name": row.name,
                "sku": row.sku,
                "quantity": row.quantity,
                "revenue": float(row.revenue)
            })

        # Top categories
        top_categories = await db.execute(
            select(
                Category.name,
                func.count(distinct(Order.id)).label('orders'),
                func.sum(OrderItem.subtotal).label('revenue')
            )
            .join(Product, Category.id == Product.category_id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order)
            .where(
                and_(
                    Order.created_at >= start_date,
                    Order.status != OrderStatus.CANCELLED
                )
            )
            .group_by(Category.id, Category.name)
            .order_by(func.sum(OrderItem.subtotal).desc())
            .limit(5)
        )

        categories_list = []
        for row in top_categories:
            categories_list.append({
                "name": row.name,
                "orders": row.orders,
                "revenue": float(row.revenue)
            })

        return {
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "orders_by_status": status_stats,
            "top_products": products_list,
            "top_categories": categories_list
        }

    @staticmethod
    async def get_charts_data(
            db: AsyncSession,
            period: str = "week"
    ) -> Dict[str, Any]:
        """Date pentru grafice."""
        now = datetime.utcnow()

        if period == "today":
            # Hourly data
            labels = [f"{i:02d}:00" for i in range(24)]
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Orders per hour
            orders_data = await db.execute(
                select(
                    func.extract('hour', Order.created_at).label('hour'),
                    func.count(Order.id).label('count')
                )
                .where(Order.created_at >= start_date)
                .group_by(func.extract('hour', Order.created_at))
            )

        elif period == "week":
            # Daily data for last 7 days
            labels = []
            for i in range(7, -1, -1):
                date = now - timedelta(days=i)
                labels.append(date.strftime("%d %b"))

            start_date = now - timedelta(days=7)

            # Orders per day
            orders_data = await db.execute(
                select(
                    func.date(Order.created_at).label('date'),
                    func.count(Order.id).label('count')
                )
                .where(Order.created_at >= start_date)
                .group_by(func.date(Order.created_at))
            )

        else:
            # Default to week
            return await DashboardStatsService.get_charts_data(db, "week")

        # Process orders data
        orders_dict = {row.hour if period == "today" else row.date: row.count
                       for row in orders_data}

        orders_values = []
        if period == "today":
            for i in range(24):
                orders_values.append(orders_dict.get(i, 0))
        else:
            for i in range(7, -1, -1):
                date = (now - timedelta(days=i)).date()
                orders_values.append(orders_dict.get(date, 0))

        return {
            "labels": labels,
            "orders": orders_values,
            "revenue": [],  # To be implemented
            "users": []  # To be implemented
        }

    @staticmethod
    async def get_activity_count(db: AsyncSession) -> int:
        """Număr total activități."""
        orders_count_result = await db.execute(
            select(func.count(Order.id))
        )
        orders_count = orders_count_result.scalar() or 0

        requests_count_result = await db.execute(
            select(func.count(UserRequest.id))
        )
        requests_count = requests_count_result.scalar() or 0

        return orders_count + requests_count