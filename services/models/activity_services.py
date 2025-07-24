# services/models/activity_services.py

from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy import select, func, and_, or_

from models import UserActivity, UserRequest, UserInteraction, ActionType, TargetType, UserTargetStats


class ActivityService:
    """Service pentru tracking activitate utilizatori."""

    @staticmethod
    async def start_session(
            db: AsyncSession,
            client_id: int,
            user_agent: Optional[str] = None,
            ip_address: Optional[str] = None
    ) -> UserActivity:
        """Începe sesiune nouă."""
        activity = UserActivity(
            client_id=client_id,
            session_start=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.add(activity)
        await db.commit()
        await db.refresh(activity)
        return activity

    @staticmethod
    async def end_session(
            db: AsyncSession,
            activity_id: int
    ) -> UserActivity:
        """Închide sesiune."""
        result = await db.execute(
            select(UserActivity).where(UserActivity.id == activity_id)
        )
        activity = result.scalar_one()
        activity.session_end = datetime.utcnow()

        await db.commit()
        await db.refresh(activity)
        return activity

    @staticmethod
    async def track_interaction(
            db: AsyncSession,
            client_id: int,
            action_type: ActionType,
            target_type: TargetType,
            target_id: int,
            activity_id: Optional[int] = None,
            metadata: Optional[Dict] = None
    ) -> UserInteraction:
        """Înregistrează interacțiune și actualizează statistici."""
        # 1. Salvează interacțiunea detaliată (istoric complet)
        interaction = UserInteraction(
            client_id=client_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            activity_id=activity_id,
            extra_data=metadata
        )
        db.add(interaction)

        # 2. Actualizează sau creează statistici agregate
        result = await db.execute(
            select(UserTargetStats).where(
                and_(
                    UserTargetStats.client_id == client_id,
                    UserTargetStats.target_type == target_type,
                    UserTargetStats.target_id == target_id
                )
            )
        )
        stats = result.scalar_one_or_none()

        if stats:
            # Actualizează statistici existente
            stats.total_interactions += 1
            stats.last_interaction_at = func.now()

            if action_type == ActionType.VIEW:
                stats.total_views += 1
            elif action_type == ActionType.ADD_TO_CART:
                stats.add_to_cart_count += 1
            elif action_type == ActionType.REQUEST_QUOTE:
                stats.request_quote_count += 1
        else:
            # Creează statistici noi
            stats = UserTargetStats(
                client_id=client_id,
                target_type=target_type,
                target_id=target_id,
                total_views=1 if action_type == ActionType.VIEW else 0,
                add_to_cart_count=1 if action_type == ActionType.ADD_TO_CART else 0,
                request_quote_count=1 if action_type == ActionType.REQUEST_QUOTE else 0
            )
            db.add(stats)

        # 3. Incrementează counter în activitate
        if activity_id:
            result = await db.execute(
                select(UserActivity).where(UserActivity.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            if activity:
                activity.interactions += 1
                if action_type == ActionType.VIEW:
                    activity.page_views += 1

        await db.commit()
        await db.refresh(interaction)
        return interaction

    @staticmethod
    async def get_target_stats(
            db: AsyncSession,
            client_id: int,
            target_type: TargetType,
            target_id: int
    ) -> Optional[UserTargetStats]:
        """Obține statistici pentru un target specific."""
        result = await db.execute(
            select(UserTargetStats).where(
                and_(
                    UserTargetStats.client_id == client_id,
                    UserTargetStats.target_type == target_type,
                    UserTargetStats.target_id == target_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_client_stats(
            db: AsyncSession,
            client_id: int,
            target_type: Optional[TargetType] = None
    ) -> List[UserTargetStats]:
        """Obține toate statisticile unui client."""
        query = select(UserTargetStats).where(
            UserTargetStats.client_id == client_id
        )

        if target_type:
            query = query.where(UserTargetStats.target_type == target_type)

        query = query.order_by(UserTargetStats.last_interaction_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_user_journey(
            db: AsyncSession,
            client_id: int,
            days: int = 7
    ) -> List[UserInteraction]:
        """Obține istoricul interacțiunilor unui utilizator."""
        since = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.client_id == client_id,
                    UserInteraction.created_at >= since
                )
            )
            .order_by(UserInteraction.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def get_product_analytics(
            db: AsyncSession,
            product_id: int,
            days: int = 30
    ) -> Dict:
        """Analiză pentru un produs specific."""
        since = datetime.utcnow() - timedelta(days=days)

        # Views
        views_result = await db.execute(
            select(func.count(UserInteraction.id))
            .where(
                and_(
                    UserInteraction.target_type == TargetType.PRODUCT,
                    UserInteraction.target_id == product_id,
                    UserInteraction.action_type == ActionType.VIEW,
                    UserInteraction.created_at >= since
                )
            )
        )
        views = views_result.scalar() or 0

        # Add to cart
        cart_result = await db.execute(
            select(func.count(UserInteraction.id))
            .where(
                and_(
                    UserInteraction.target_type == TargetType.PRODUCT,
                    UserInteraction.target_id == product_id,
                    UserInteraction.action_type == ActionType.ADD_TO_CART,
                    UserInteraction.created_at >= since
                )
            )
        )
        add_to_cart = cart_result.scalar() or 0

        # Requests
        requests_result = await db.execute(
            select(func.count(UserRequest.id))
            .where(
                and_(
                    UserRequest.product_id == product_id,
                    UserRequest.created_at >= since
                )
            )
        )
        requests = requests_result.scalar() or 0

        return {
            "product_id": product_id,
            "period_days": days,
            "views": views,
            "add_to_cart": add_to_cart,
            "conversion_rate": (add_to_cart / views * 100) if views > 0 else 0,
            "requests": requests,
            "request_rate": (requests / views * 100) if views > 0 else 0
        }