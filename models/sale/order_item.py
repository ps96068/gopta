# models/sale/order_item.py
"""
OrderItem model pentru produsele din comenzi.

Fiecare item reprezintă un produs cu cantitatea și prețul snapshot
la momentul comenzii. În multi-vendor, fiecare item poate avea
status propriu și vendor diferit.

Business Rules:
- Prețul este snapshot din ProductPrice la momentul comenzii
- Se salvează ce tip de preț s-a aplicat (anonim/user/etc)
- În MVP toate items au același vendor_id ca Order
- În multi-vendor, items pot avea vendor_id diferit
- Status propriu pentru tracking în multi-vendor
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal


from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property


from cfg import Base, CreatedAtMixin


if TYPE_CHECKING:
    from models import Product, Order, Vendor


class OrderItem(Base, CreatedAtMixin):
    """Model pentru produse din comandă."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot date produs la momentul comenzii
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)

    # Preț la momentul comenzii
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_type: Mapped[str] = mapped_column(String(20), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Vendor pentru tracking
    vendor_company_id: Mapped[int] = mapped_column(
        ForeignKey("vendor_companies.id"),
        nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

