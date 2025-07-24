#services/models/staff_services.py


from __future__ import annotations
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

from models import Staff, StaffRole


class StaffService:
    """Service pentru gestionarea staff-ului."""

    @staticmethod
    async def authenticate(
            db: AsyncSession,
            email: str,
            password: str
    ) -> Optional[Staff]:
        """Autentifică staff verificând parola cu bcrypt."""
        result = await db.execute(
            select(Staff)
            .where(Staff.email == email)
            .where(Staff.is_active == True)
        )
        staff = result.scalar_one_or_none()

        if staff and bcrypt.checkpw(password.encode('utf-8'), staff.password_hash.encode('utf-8')):
            # Update last login
            staff.last_login = func.now()
            await db.commit()
            await db.refresh(staff)
            return staff

        return None

    @staticmethod
    async def create(
            db: AsyncSession,
            email: str,
            password: str,  # Plain text password
            first_name: str,
            last_name: str,
            role: StaffRole = StaffRole.SUPERVISOR,
            phone: Optional[str] = None
    ) -> Staff:
        """Creează membru staff nou cu parolă hash-uită."""
        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        staff = Staff(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone
        )
        db.add(staff)
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def get_by_id(
            db: AsyncSession,
            staff_id: int
    ) -> Optional[Staff]:
        """Găsește staff după ID."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(
            db: AsyncSession,
            email: str
    ) -> Optional[Staff]:
        """Găsește staff după email."""
        result = await db.execute(
            select(Staff).where(Staff.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_role(
            db: AsyncSession,
            role: StaffRole
    ) -> List[Staff]:
        """Returnează staff după rol."""
        result = await db.execute(
            select(Staff)
            .where(Staff.role == role)
            .where(Staff.is_active == True)
        )
        return result.scalars().all()

    @staticmethod
    async def get_all(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            include_inactive: bool = False
    ) -> List[Staff]:
        """Returnează toți membrii staff."""
        query = select(Staff)

        if not include_inactive:
            query = query.where(Staff.is_active == True)

        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update(
            db: AsyncSession,
            staff_id: int,
            **kwargs
    ) -> Optional[Staff]:
        """Actualizează date staff."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        staff = result.scalar_one_or_none()

        if not staff:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(staff, key) and key != 'id':
                setattr(staff, key, value)

        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def update_password(
            db: AsyncSession,
            staff_id: int,
            new_password: str
    ) -> Optional[Staff]:
        """Actualizează parola unui staff."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        staff = result.scalar_one_or_none()

        if not staff:
            return None

        # Hash new password
        staff.password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def update_role(
            db: AsyncSession,
            staff_id: int,
            new_role: StaffRole
    ) -> Optional[Staff]:
        """Actualizează rolul unui membru staff."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        staff = result.scalar_one_or_none()

        if not staff:
            return None

        staff.role = new_role
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def deactivate(
            db: AsyncSession,
            staff_id: int
    ) -> Optional[Staff]:
        """Dezactivează un membru staff (soft delete)."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        staff = result.scalar_one_or_none()

        if not staff:
            return None

        staff.is_active = False
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def activate(
            db: AsyncSession,
            staff_id: int
    ) -> Optional[Staff]:
        """Activează un membru staff."""
        result = await db.execute(
            select(Staff).where(Staff.id == staff_id)
        )
        staff = result.scalar_one_or_none()

        if not staff:
            return None

        staff.is_active = True
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def count_by_role(
            db: AsyncSession
    ) -> dict:
        """Returnează numărul de staff pe fiecare rol."""
        result = await db.execute(
            select(
                Staff.role,
                func.count(Staff.id).label('count')
            )
            .where(Staff.is_active == True)
            .group_by(Staff.role)
        )

        counts = {role.value: 0 for role in StaffRole}
        for row in result:
            counts[row.role.value] = row.count

        return counts



