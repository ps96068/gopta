# models/user/staff.py
"""
Staff model pentru utilizatorii Dashboard.

Staff reprezintă angajații PCE care gestionează platforma prin Dashboard.
Autentificare se face cu email/password.

Roluri și permisiuni:
- super_admin: Acces total la toate funcționalitățile
- manager: Acces complet cu excepția Staff management și marketing
- supervisor: Doar vizualizare (read-only)

În PCE-start, Staff operează ca proxy pentru Default Vendor.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum
import re
import bcrypt

from sqlalchemy import String, Boolean, Enum, Index, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin
from models import StaffRole

if TYPE_CHECKING:
    from models import Order, RequestResponse



class Staff(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru staff-ul care procesează comenzi."""
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Rol
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole), nullable=False, default=StaffRole.SUPERVISOR)

    # Permisiuni granulare pentru Manager
    can_manage_clients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_manage_products: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_manage_orders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Pentru tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    processed_orders: Mapped[List["Order"]] = relationship(back_populates="processed_by", cascade="all, delete-orphan")
    responses: Mapped[List["RequestResponse"]] = relationship(back_populates="staff", cascade="all, delete-orphan")