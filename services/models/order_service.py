# services/models/order_service.py
"""
OrderService cu lazy import pentru notification_manager.
Actualizat pentru noua logică Invoice.
"""

from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models import Product, Client
from models.sale import Order, OrderItem, Cart, CartItem, Invoice
from models.enum import OrderStatus, NotificationType, InvoiceType
from services.models.cart_service import CartService
from services.models.notification_service import NotificationService
from services.models.product_service import ProductService

# Configurare logging
logger = logging.getLogger(__name__)

# Logging special pentru notificări
notification_logger = logging.getLogger('notifications')
notification_logger.setLevel(logging.INFO)

# Creează directorul pentru logs dacă nu există
log_dir = Path("logs/notifications")
log_dir.mkdir(parents=True, exist_ok=True)

# Handler pentru fișier
file_handler = logging.FileHandler(
    log_dir / f"notifications_{datetime.now().strftime('%Y%m%d')}.log",
    encoding='utf-8'
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
notification_logger.addHandler(file_handler)


class OrderService:
    """Service pentru gestionarea comenzilor cu notificări robuste."""

    # Cache pentru notification manager
    _notification_manager = None
    _manager_checked = False
    _import_error = None

    @classmethod
    def _get_notification_manager(cls):
        """
        Lazy import pentru notification_manager.
        Se încearcă o singură dată și se cache-uiește rezultatul.
        """
        if not cls._manager_checked:
            try:
                from server.dashboard.websocket import notification_manager
                cls._notification_manager = notification_manager
                logger.info("✅ Notification manager loaded successfully")
                notification_logger.info("SYSTEM: WebSocket notification manager available")
            except ImportError as e:
                cls._import_error = str(e)
                cls._notification_manager = None
                logger.info(f"ℹ️ Notification manager not available: {e}")
                notification_logger.info(f"SYSTEM: WebSocket not available - {e}")
            except Exception as e:
                cls._import_error = str(e)
                cls._notification_manager = None
                logger.error(f"❌ Unexpected error loading notification manager: {e}")
                notification_logger.error(f"SYSTEM: Failed to load notification manager - {e}")
            finally:
                cls._manager_checked = True

        return cls._notification_manager

    @staticmethod
    async def create_from_cart(
            db: AsyncSession,
            cart_id: int,
            client_note: Optional[str] = None,
            from_quote_id: Optional[int] = None  # Dacă vine dintr-o ofertă
    ) -> Order:
        """
        Creează comandă din coș cu notificări robuste.
        Poate fi creat direct sau prin convertirea unei oferte.
        """
        logger.info(f"📦 Creating order from cart {cart_id}")

        # Obține coșul cu toate datele necesare
        result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product),
                selectinload(Cart.client)
            )
        )
        cart = result.scalar_one()

        if not cart.items:
            raise ValueError("Cannot create order from empty cart")

        # Generează număr comandă unic
        order_number = await OrderService._generate_order_number(db)

        # Calculează totalul
        total = sum(
            float(item.price_snapshot) * item.quantity
            for item in cart.items
        )

        # Creează comanda
        order = Order(
            client_id=cart.client_id,
            order_number=order_number,
            total_amount=total,
            client_note=client_note,
            status=OrderStatus.NEW
        )

        # Dacă vine dintr-o ofertă, adaugă referință în staff_note
        if from_quote_id:
            # Obține oferta pentru referință
            quote_result = await db.execute(
                select(Invoice).where(Invoice.id == from_quote_id)
            )
            quote = quote_result.scalar_one_or_none()
            if quote:
                order.staff_note = f"Convertit din oferta {quote.invoice_number}"

        db.add(order)
        await db.flush()  # Pentru a obține order.id

        # Creează order items din cart items
        items_count = 0
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                unit_price=cart_item.price_snapshot,
                price_type=cart_item.price_type,
                subtotal=float(cart_item.price_snapshot) * cart_item.quantity,
                vendor_company_id=cart_item.product.vendor_company_id  # FIX APLICAT
            )
            db.add(order_item)
            items_count += 1

        # Golește coșul după creare comandă
        cart = await db.get(Cart, cart_id)
        if cart:
            await db.delete(cart)

        # Commit pentru a salva comanda
        await db.commit()
        await db.refresh(order)

        logger.info(f"✅ Order {order.order_number} created successfully")

        # Trimite notificări cu numărul de items cunoscut
        await OrderService._send_order_notifications(order, cart, db, items_count)

        return order

    @staticmethod
    async def create_manual_order(
            db: AsyncSession,
            client_id: int,
            items: List[Dict[str, Any]],  # [{"product_id": 1, "quantity": 2}, ...]
            staff_id: int,
            client_note: Optional[str] = None
    ) -> Order:
        """
        Creează comandă manuală direct, fără coș intermediar.
        Folosit când Staff creează comandă de la zero.
        """
        logger.info(f"📦 Creating manual order for client {client_id}")

        if not items:
            raise ValueError("Cannot create order without items")

        # Obține client
        client_result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = client_result.scalar_one()

        # Generează număr comandă
        order_number = await OrderService._generate_order_number(db)

        # Calculează total și pregătește items
        total_amount = 0
        order_items = []

        for item_data in items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]

            # Obține produsul
            product_result = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one()

            # Obține prețul pentru statusul clientului
            price = await ProductService.get_price_for_user_status(
                db, product_id, client.status
            )

            if price is None:
                raise ValueError(f"No price found for product {product.sku}")

            subtotal = float(price) * quantity
            total_amount += subtotal

            # Pregătește OrderItem (nu îl adaugă încă în DB)
            order_items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": price,
                "subtotal": subtotal,
                "price_type": client.status.value
            })

        # Creează comanda
        order = Order(
            client_id=client_id,
            order_number=order_number,
            total_amount=total_amount,
            client_note=client_note,
            status=OrderStatus.PROCESSING,  # Direct în procesare când e creată manual
            processed_by_id=staff_id,
            processed_at=datetime.utcnow(),
            staff_note="Comandă creată manual de staff"
        )
        db.add(order)
        await db.flush()

        # Creează OrderItems și numără
        items_count = 0
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                quantity=item_data["quantity"],
                product_name=item_data["product"].name,
                product_sku=item_data["product"].sku,
                unit_price=item_data["unit_price"],
                price_type=item_data["price_type"],
                subtotal=item_data["subtotal"],
                vendor_company_id=item_data["product"].vendor_company_id
            )
            db.add(order_item)
            items_count += 1

        await db.commit()
        await db.refresh(order)

        logger.info(f"✅ Manual order {order.order_number} created successfully")

        # Trimite notificări (folosind un obiect mock pentru cart)
        class MockCart:
            def __init__(self, client):
                self.client = client
                self.client_id = client.id

        mock_cart = MockCart(client)
        # Trimitem și numărul de items pentru a evita lazy loading
        await OrderService._send_order_notifications(order, mock_cart, db, items_count)

        return order

    @staticmethod
    async def _send_order_notifications(order: Order, cart_or_client: Any, db: AsyncSession, items_count: int = 0) -> None:
        """Trimite notificări pentru comandă nouă."""

        # Pregătește date pentru notificare
        notification_data = {
            "id": order.id,
            "order_number": order.order_number,
            "client_id": cart_or_client.client_id if hasattr(cart_or_client, 'client_id') else cart_or_client.id,
            "client_name": f"{cart_or_client.client.first_name or ''} {cart_or_client.client.last_name or ''}".strip() or "Client",
            "total_amount": float(order.total_amount),
            "items_count": items_count,
            "created_at": order.created_at.isoformat()
        }

        # Log în fișier pentru audit
        notification_logger.info(
            f"ORDER_CREATED: {order.order_number} | "
            f"Client: {notification_data['client_name']} (ID: {notification_data['client_id']}) | "
            f"Total: {notification_data['total_amount']} MDL | "
            f"Items: {notification_data['items_count']}"
        )

        # 1. Încearcă notificare WebSocket (real-time)
        ws_sent = False
        notification_manager = OrderService._get_notification_manager()

        if notification_manager:
            try:
                await notification_manager.send_order_notification(notification_data)
                ws_sent = True
                logger.info(f"✅ WebSocket notification sent for order {order.order_number}")
                notification_logger.info(
                    f"NOTIFICATION_SENT: Order {order.order_number} | "
                    f"Channel: WebSocket | Status: SUCCESS"
                )
            except Exception as e:
                logger.error(f"❌ WebSocket notification failed: {e}")
                notification_logger.error(
                    f"NOTIFICATION_FAILED: Order {order.order_number} | "
                    f"Channel: WebSocket | Error: {str(e)}"
                )
        else:
            logger.info(
                f"ℹ️ WebSocket not available for order {order.order_number} "
                f"(Import error: {OrderService._import_error})"
            )
            notification_logger.warning(
                f"NOTIFICATION_SKIPPED: Order {order.order_number} | "
                f"Reason: WebSocket manager not available"
            )

        # 2. Întotdeauna salvează notificare în DB (fallback/istoric)
        try:
            await NotificationService.create_order_notification(db, order)
            logger.info(f"✅ DB notification saved for order {order.order_number}")
            notification_logger.info(
                f"NOTIFICATION_SAVED: Order {order.order_number} | "
                f"Channel: Database | Status: PENDING"
            )
        except Exception as e:
            logger.error(f"❌ Failed to save DB notification: {e}")
            notification_logger.error(
                f"NOTIFICATION_DB_FAILED: Order {order.order_number} | "
                f"Error: {str(e)}"
            )

        # Sumar final
        logger.info(
            f"📊 Order {order.order_number} notification summary: "
            f"WebSocket={'✓' if ws_sent else '✗'}, DB={'✓'}"
        )

    @staticmethod
    async def _generate_order_number(db: AsyncSession) -> str:
        """
        Generează număr unic de comandă.
        Format: PCE-YYYYMMDD-XXXX
        """
        today = datetime.now().strftime("%Y%m%d")

        # Numără comenzile din ziua curentă
        result = await db.execute(
            select(func.count(Order.id))
            .where(Order.order_number.like(f"Cont-{today}-%"))
        )
        count = result.scalar() or 0

        return f"Cont-{today}-{count + 1:04d}"

    @staticmethod
    async def generate_invoice(
            db: AsyncSession,
            order_id: int,
            notes: Optional[str] = None
    ) -> Invoice:
        """
        Generează factură (cont) pentru comandă.
        """
        print(f"[OrderService] Generating invoice for order {order_id}")

        # Obține comanda cu client
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.client))
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Verifică dacă există deja invoice pentru această comandă
        existing = await db.execute(
            select(Invoice).where(Invoice.order_id == order_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Order {order.order_number} already has an invoice")

        # Import InvoiceService aici pentru a evita circular imports
        from services.models.invoice_service import InvoiceService

        print(f"[OrderService] Creating invoice for order {order.order_number}")

        # Folosește InvoiceService pentru a crea factura
        invoice = await InvoiceService.create_invoice_from_order(
            db=db,
            order_id=order_id,
            notes=notes
        )

        print(f"[OrderService] Invoice created with number {invoice.invoice_number}")

        return invoice

    @staticmethod
    async def update_status(
            db: AsyncSession,
            order_id: int,
            new_status: OrderStatus,
            staff_id: Optional[int] = None,
            staff_note: Optional[str] = None
    ) -> Order:
        """
        Actualizează status comandă și trimite notificări.
        Folosit de Staff din Dashboard.
        """
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.client))
        )
        order = result.scalar_one()

        old_status = order.status
        order.status = new_status

        if staff_id:
            order.processed_by_id = staff_id
            order.processed_at = datetime.utcnow()

        if staff_note:
            order.staff_note = staff_note

        await db.commit()
        await db.refresh(order)

        logger.info(
            f"📝 Order {order.order_number} status changed: "
            f"{old_status.value} → {new_status.value}"
        )

        # Notificare pentru schimbare status
        if old_status != new_status:
            notification_data = {
                "order_id": order.id,
                "order_number": order.order_number,
                "client_id": order.client_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "changed_by": staff_id,
                "changed_at": datetime.utcnow().isoformat()
            }

            # WebSocket notification
            notification_manager = OrderService._get_notification_manager()
            if notification_manager:
                try:
                    await notification_manager.send_status_update(notification_data)
                    logger.info(f"✅ Status change notification sent via WebSocket")
                except Exception as e:
                    logger.error(f"❌ Failed to send status notification: {e}")

            # DB notification
            try:
                await NotificationService.create_notification(
                    db=db,
                    client_id=order.client_id,
                    notification_type=NotificationType.ORDER_STATUS_CHANGED,
                    message=f"Comanda #{order.order_number} - status actualizat: {new_status.value}",
                    extra_data=notification_data
                )
            except Exception as e:
                logger.error(f"❌ Failed to save status notification: {e}")

        return order

    @staticmethod
    async def get_by_status(
            db: AsyncSession,
            status: OrderStatus,
            skip: int = 0,
            limit: int = 20
    ) -> List[Order]:
        """Obține comenzi după status."""
        result = await db.execute(
            select(Order)
            .where(Order.status == status)
            .options(
                selectinload(Order.client),
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(
            db: AsyncSession,
            order_id: int
    ) -> Optional[Order]:
        """Obține comandă după ID cu toate relațiile."""
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.client),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.processed_by),
                selectinload(Order.invoice)  # Include invoice
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_order_number(
            db: AsyncSession,
            order_number: str
    ) -> Optional[Order]:
        """Găsește comandă după număr."""
        result = await db.execute(
            select(Order)
            .where(Order.order_number == order_number)
            .options(
                selectinload(Order.client),
                selectinload(Order.items),
                selectinload(Order.invoice)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def get_notification_stats() -> Dict[str, Any]:
        """
        Returnează statistici despre sistemul de notificări.
        Util pentru monitoring și debugging.
        """
        return {
            "websocket_available": OrderService._notification_manager is not None,
            "manager_checked": OrderService._manager_checked,
            "import_error": OrderService._import_error,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def cancel_order(
            db: AsyncSession,
            order_id: int,
            reason: str,
            cancelled_by: Optional[int] = None
    ) -> Order:
        """
        Anulează o comandă.
        Poate fi apelat de Staff sau Client (în anumite condiții).
        """
        order = await OrderService.get_by_id(db, order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order with status {order.status.value}")

        # Actualizează status
        order.status = OrderStatus.CANCELLED
        order.staff_note = f"Cancelled: {reason}"
        if cancelled_by:
            order.processed_by_id = cancelled_by
            order.processed_at = datetime.utcnow()

        await db.commit()

        # Notificări
        try:
            await NotificationService.create_notification(
                db=db,
                client_id=order.client_id,
                notification_type=NotificationType.ORDER_STATUS_CHANGED,
                message=f"Comanda #{order.order_number} a fost anulată. Motiv: {reason}",
                extra_data={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "reason": reason
                }
            )
        except Exception as e:
            logger.error(f"Failed to create cancellation notification: {e}")

        logger.info(f"❌ Order {order.order_number} cancelled. Reason: {reason}")

        return order

    @staticmethod
    async def create_from_quote(
            db: AsyncSession,
            quote_id: int,
            staff_id: Optional[int] = None
    ) -> Order:
        """
        Creează comandă dintr-o ofertă existentă.
        Wrapper pentru InvoiceService.convert_quote_to_order
        """
        from services.models.invoice_service import InvoiceService

        return await InvoiceService.convert_quote_to_order(db, quote_id)


