#services/models/client_services.py


from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.enum.client import UserStatus
from models.user import Client, Staff, Vendor
class ClientService:
    """Service pentru gestionarea clienților."""

    @staticmethod
    async def get_or_create_by_telegram_id(
            db: AsyncSession,
            telegram_id: int,
            username: Optional[str] = None,
            first_name: Optional[str] = None,
            language_code: Optional[str] = "ro"
    ) -> Client:
        """Găsește sau creează un client după Telegram ID."""
        result = await db.execute(
            select(Client).where(Client.telegram_id == telegram_id)
        )
        client = result.scalar_one_or_none()

        if not client:
            client = Client(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
                status=UserStatus.ANONIM
            )
            db.add(client)
            await db.commit()
            await db.refresh(client)

        return client

    @staticmethod
    async def update_to_user_status(
            db: AsyncSession,
            client_id: int,
            first_name: str,
            last_name: str,
            phone: str,
            email: str
    ) -> Client:
        """Actualizează client anonim la status USER."""
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one()

        client.first_name = first_name
        client.last_name = last_name
        client.phone = phone
        client.email = email
        client.status = UserStatus.USER

        await db.commit()
        await db.refresh(client)
        return client

    @staticmethod
    async def update_status(
            db: AsyncSession,
            client_id: int,
            new_status: UserStatus
    ) -> Client:
        """Actualizează status-ul clientului (manual de către staff)."""
        result = await db.execute(
            select(Client).where(Client.id == client_id)
        )
        client = result.scalar_one()

        client.status = new_status
        await db.commit()
        await db.refresh(client)
        return client

    @staticmethod
    async def get_by_status(
            db: AsyncSession,
            status: UserStatus,
            skip: int = 0,
            limit: int = 100
    ) -> List[Client]:
        """Returnează clienți după status."""
        result = await db.execute(
            select(Client)
            .where(Client.status == status)
            .where(Client.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
