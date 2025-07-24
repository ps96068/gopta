#services/models/vendor_services.py


from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.enum.client import UserStatus
from models.user import Client, Staff, Vendor


class VendorService:
    """Service pentru gestionarea vendorilor."""

    @staticmethod
    async def create(
            db: AsyncSession,
            name: str,
            email: str,
            phone: str,
            **kwargs
    ) -> Vendor:
        """Creează vendor nou."""
        vendor = Vendor(
            name=name,
            email=email,
            phone=phone,
            **kwargs
        )
        db.add(vendor)
        await db.commit()
        await db.refresh(vendor)
        return vendor

    @staticmethod
    async def get_active(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100
    ) -> List[Vendor]:
        """Returnează vendori activi."""
        result = await db.execute(
            select(Vendor)
            .where(Vendor.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(
            db: AsyncSession,
            vendor_id: int
    ) -> Optional[Vendor]:
        """Găsește vendor după ID."""
        result = await db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(
            db: AsyncSession,
            email: str
    ) -> Optional[Vendor]:
        """Găsește vendor după email."""
        result = await db.execute(
            select(Vendor).where(Vendor.email == email)
        )
        return result.scalar_one_or_none()



