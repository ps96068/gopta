# services/models/notification_service.py

from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models import Client, Order, Notification, NotificationType, NotificationChannel, NotificationStatus


class NotificationService:
    """Service pentru gestionarea notificărilor."""

    @staticmethod
    async def create_notification(
            db: AsyncSession,
            client_id: int,
            notification_type: NotificationType,
            message: str,
            channel: NotificationChannel = NotificationChannel.TELEGRAM,
            subject: Optional[str] = None,
            extra_data: Optional[Dict] = None,
            scheduled_for: Optional[datetime] = None
    ) -> Notification:
        """Creează notificare nouă."""
        notification = Notification(
            client_id=client_id,
            notification_type=notification_type,
            channel=channel,
            message=message,
            subject=subject,
            extra_data=extra_data,
            scheduled_for=scheduled_for
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def create_order_notification(
            db: AsyncSession,
            order: Order,
            notification_type: NotificationType = NotificationType.ORDER_CREATED
    ) -> Notification:
        """Creează notificare pentru comandă."""
        message = f"Comanda #{order.order_number} a fost înregistrată cu succes!"
        if notification_type == NotificationType.ORDER_STATUS_CHANGED:
            message = f"Status comandă #{order.order_number}: {order.status.value}"

        return await NotificationService.create_notification(
            db=db,
            client_id=order.client_id,
            notification_type=notification_type,
            message=message,
            extra_data={"order_id": order.id, "order_number": order.order_number}
        )

    @staticmethod
    async def get_pending_notifications(
            db: AsyncSession,
            limit: int = 50
    ) -> List[Notification]:
        """Obține notificări în așteptare."""
        now = datetime.utcnow()

        result = await db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.status == NotificationStatus.PENDING,
                    Notification.retry_count < Notification.max_retries,
                    (Notification.scheduled_for == None) | (Notification.scheduled_for <= now)
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def mark_as_sent(
            db: AsyncSession,
            notification_id: int
    ) -> Notification:
        """Marchează notificare ca trimisă."""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one()

        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()

        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def mark_as_failed(
            db: AsyncSession,
            notification_id: int,
            error_message: str
    ) -> Notification:
        """Marchează notificare ca eșuată."""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one()

        notification.retry_count += 1
        notification.error_message = error_message

        if notification.retry_count >= notification.max_retries:
            notification.status = NotificationStatus.FAILED

        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def create_cart_reminder(
            db: AsyncSession,
            client_id: int,
            cart_id: int,
            hours_delay: int = 24
    ) -> Notification:
        """Creează reminder pentru coș abandonat."""
        scheduled_time = datetime.utcnow() + timedelta(hours=hours_delay)

        return await NotificationService.create_notification(
            db=db,
            client_id=client_id,
            notification_type=NotificationType.CART_REMINDER,
            message="Ai produse în coș! Nu uita să finalizezi comanda.",
            extra_data={"cart_id": cart_id},
            scheduled_for=scheduled_time
        )

