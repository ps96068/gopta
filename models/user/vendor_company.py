# models/user/vendor_company.py
"""
VendorCompany model pentru companii furnizor.

Reprezintă entitatea juridică care vinde produse pe platformă.
Poate avea mai mulți angajați (VendorStaff) care gestionează produsele.

Business Rules:
- O companie poate avea mai mulți utilizatori VendorStaff
- Toate produsele aparțin companiei, nu utilizatorului individual
- Setări globale pentru companie (comision, termene plată, etc.)
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Boolean, Numeric, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Product, VendorStaff, Order


class VendorCompany(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru companie vendor."""
    __tablename__ = "vendor_companies"
    __table_args__ = (
        Index('ix_vendor_company_active_verified', 'is_active', 'is_verified'),
    )


    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Date companie
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # CUI/VAT

    # Contact
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)

    # Bancă
    bank_account: Mapped[Optional[str]] = mapped_column(String(50))
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Business info
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))

    # Setări platformă
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=15.0,  # 15% comision implicit
        nullable=False
    )
    payment_terms_days: Mapped[int] = mapped_column(
        Integer,
        default=30,  # Plată la 30 zile
        nullable=False
    )

    # Logo/branding
    logo_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Verificare și aprobare
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verified_by_id: Mapped[Optional[int]] = mapped_column(Integer)  # Staff ID

    # Statistici
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))  # 0-5
    total_sales: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Relationships
    staff_members: Mapped[List["VendorStaff"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        back_populates="vendor_company"
    )

