# services/models/request_services.py

from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy import select

from models import RequestType, UserRequest, RequestResponse, Client
from server.dashboard.websocket import notification_manager


class RequestService:
    """Service pentru gestionarea cererilor utilizatorilor."""

    @staticmethod
    async def create_request(
            db: AsyncSession,
            client_id: int,
            request_type: RequestType,
            message: str,
            product_id: Optional[int] = None,
            cart_id: Optional[int] = None
    ) -> UserRequest:
        """Creează cerere nouă."""
        request = UserRequest(
            client_id=client_id,
            request_type=request_type,
            message=message,
            product_id=product_id,
            cart_id=cart_id
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)

        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one()

        # Trimite notificare WebSocket - AICI, după refresh
        await notification_manager.send_request_notification({
            "id": request.id,
            "request_type": request_type.value,
            "client_name": f"{client.first_name} {client.last_name}"
        })


        return request

    @staticmethod
    async def add_response(
            db: AsyncSession,
            request_id: int,
            staff_id: int,
            message: str,
            sent_via: Optional[str] = None
    ) -> RequestResponse:
        """Adaugă răspuns la cerere."""
        response = RequestResponse(
            request_id=request_id,
            staff_id=staff_id,
            message=message,
            sent_via=sent_via
        )
        db.add(response)

        # Marchează cererea ca procesată
        result = await db.execute(
            select(UserRequest).where(UserRequest.id == request_id)
        )
        request = result.scalar_one()
        request.is_processed = True
        request.processed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(response)
        return response

    @staticmethod
    async def get_unprocessed(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 20
    ) -> List[UserRequest]:
        """Obține cereri neprocesate."""
        result = await db.execute(
            select(UserRequest)
            .where(UserRequest.is_processed == False)
            .order_by(UserRequest.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()