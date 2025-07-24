# services/models/vendor_staff_service.py (nou)
from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from sqlalchemy.orm import selectinload

from models import VendorStaff, VendorRole, VendorCompany


class VendorStaffService:
    """Service pentru gestionarea staff vendor."""

    @staticmethod
    async def authenticate(
            db: AsyncSession,
            email: str,
            password: str
    ) -> Optional[VendorStaff]:
        """Autentifică vendor staff."""
        result = await db.execute(
            select(VendorStaff)
            .where(VendorStaff.email == email)
            .where(VendorStaff.is_active == True)
            .options(selectinload(VendorStaff.company))
        )
        vendor_staff = result.scalar_one_or_none()

        if vendor_staff and vendor_staff.company:
            # VERIFICARE CRITICĂ: Compania trebuie să fie activă
            if not vendor_staff.company.is_active:
                print(f"🚫 AUTENTIFICARE REFUZATĂ: Compania {vendor_staff.company.name} este dezactivată")
                print(f"   User: {vendor_staff.email}")
                return None

            # Verifică parola doar dacă compania e activă
            if bcrypt.checkpw(password.encode('utf-8'), vendor_staff.password_hash.encode('utf-8')):
                vendor_staff.last_login = func.now()
                await db.commit()
                await db.refresh(vendor_staff)

                print(f"✅ AUTENTIFICARE REUȘITĂ: {vendor_staff.email} - {vendor_staff.company.name}")
                return vendor_staff

        print(f"🚫 AUTENTIFICARE EȘUATĂ: {email}")

        return None

    @staticmethod
    async def create(
            db: AsyncSession,
            company_id: int,
            email: str,
            password: str,
            first_name: str,
            last_name: str,
            role,
            **kwargs
    ) -> VendorStaff:
        """Creează membru staff vendor nou."""
        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        vendor_staff = VendorStaff(
            company_id=company_id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **kwargs
        )

        db.add(vendor_staff)
        await db.commit()
        await db.refresh(vendor_staff)
        return vendor_staff

    @staticmethod
    async def get_by_email(
            db: AsyncSession,
            email: str
    ) -> Optional[VendorStaff]:
        """Găsește vendor după email."""
        result = await db.execute(
            select(VendorStaff).where(VendorStaff.email == email)
        )
        return result.scalar_one_or_none()
