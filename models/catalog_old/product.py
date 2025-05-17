from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    cod_produs: Mapped[int | None] = mapped_column(index=True, unique=True, nullable=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    datasheet_url: Mapped[str | None] = mapped_column(nullable=True, default="Nicio fișă tehnică disponibilă momentan")

    #new
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    create_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    publish_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relație

    # new
    product_author: Mapped["Staff"] = relationship("Staff", foreign_keys=[author_id], back_populates="products")

    # category: Mapped["Category | None"] = relationship("Category", foreign_keys=[category_id], back_populates="products")
    category: Mapped["Category | None"] = relationship("Category", back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    prices: Mapped[list["ProductPrice"]] = relationship(
        "ProductPrice",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        primaryjoin="and_(Product.id == foreign(UserInteraction.target_id), UserInteraction.target_type == 'product')",
        back_populates="product",
        overlaps="category,product,interactions"
    )
    requests: Mapped[list["UserRequest"]] = relationship("UserRequest", back_populates="product")

    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")




    @validates('name')
    def validate_name(self, key, value):
        if not value.strip():
            raise ValueError("Numele produsului nu poate fi gol sau să conțină doar spații.")
        return value


    @validates('datasheet_url')
    def validate_datasheet_url(self, key, url):
        if url and not re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url):
            raise ValueError("Datasheet URL trebuie să fie un URL valid")
        return url

    @validates('cod_produs')
    def validate_cod_produs(self, key, value):
        if value is not None and value <= 0:
            raise ValueError("cod_produs trebuie să fie un număr pozitiv.")
        return value

    @validates('publish_date')
    def validate_publish_date(self, key, value):
        if value and value < datetime.now():
            raise ValueError("Data de publicare nu poate fi în trecut.")
        return value



    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', category_id={self.category_id})>"

