# models/user/vendor_staff.py
"""
VendorStaff model pentru angajații vendor.

Reprezintă utilizatorii care pot gestiona produsele unei companii vendor.
Similar cu Staff pentru PCE, dar pentru companii vendor.

Business Rules:
- Un VendorStaff aparține unei singure VendorCompany
- Poate avea rol de admin (toate permisiunile) sau manager (fără setări companie)
- Autentificare cu email/password ca Staff
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import re
import bcrypt

from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models.enum.vendor import VendorRole

if TYPE_CHECKING:
    from models import VendorCompany


class VendorStaff(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru staff vendor."""
    __tablename__ = "vendor_staff"
    __table_args__ = (
        Index('ix_vendor_staff_company_active', 'company_id', 'is_active'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("vendor_companies.id"),
        nullable=False,
        index=True
    )

    # Autentificare
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Date personale
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Rol și permisiuni
    role: Mapped[VendorRole] = mapped_column(
        Enum(VendorRole),
        nullable=False,
        default=VendorRole.MANAGER
    )

    # Tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    company: Mapped["VendorCompany"] = relationship(back_populates="staff_members")



    @property
    def full_name(self) -> str:
        """Returnează numele complet."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Verifică dacă e admin."""
        return self.role == VendorRole.ADMIN