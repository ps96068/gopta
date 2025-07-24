# models/user/vendor.py

"""
Model temporar Vendor pentru migrare.
Va fi înlocuit complet cu VendorCompany și VendorStaff.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import re
import bcrypt

from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from cfg import Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin

if TYPE_CHECKING:
    from models import Product


class Vendor(Base, CreatedAtMixin, UpdatedAtMixin, IsActiveMixin):
    """Model pentru vendor/furnizor."""
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)


