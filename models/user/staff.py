from __future__ import annotations

import re
import enum
from datetime import datetime
from starlette.requests import Request
from sqlalchemy import Index, String, Boolean, Enum, DateTime, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column, Relationship
from sqlalchemy.sql import func



from cfg import Base
from ..base import CreatedAtMixin, IsActiveMixin


# models/user/staff.py

class StaffRole(enum.Enum):
    super_admin = "super_admin"
    manager = "manager"
    supervisor = "supervisor"


class Staff(Base, CreatedAtMixin, IsActiveMixin):
    __tablename__ = "staff"
    __table_args__ = (
        Index("ix_staff_role_active", "role", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[StaffRole | None] = mapped_column(Enum(StaffRole), default=StaffRole.supervisor, nullable=False)
    last_visit: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())

    # Relații
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="post_author")
    categories_created: Mapped[list["Category"]] = relationship(
        "Category",
        foreign_keys="Category.author_id",
        back_populates="category_author"
    )
    categories_modified: Mapped[list["Category"]] = relationship(
        "Category",
        foreign_keys="Category.last_modified_by",
        back_populates="last_modifier"
    )
    products: Mapped[list["Product"]] = relationship("Product", back_populates="product_author")
    product_images: Mapped[list["ProductImage"]] = relationship("ProductImage", back_populates="product_image_author")
    product_prices: Mapped[list["ProductPrice"]] = relationship("ProductPrice", back_populates="product_price_author")
    img_author: Mapped[list["PostImage"]] = relationship("PostImage", back_populates="img_author")
    edit_history: Mapped[list["PostEditHistory"]] = relationship("PostEditHistory", back_populates="staff")

    @validates("phone_number")
    def validate_phone(self, key, number: str | None):
        if number is not None and not re.match(r"^\+?[0-9]{7,15}$", number):
            raise ValueError("Numărul de telefon are un format invalid")
        return number

    @validates("email")
    def validate_email(self, key, email: str | None):
        if email is None:
            return None
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Adresa de email este invalidă")
        return email

    def __repr__(self):
        return f"<Staff(id={self.id}, username='{self.username}', role='{self.role}')>"

    def __str__(self):
        return f"{self.id}_{self.username}-({self.role})"




