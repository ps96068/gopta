from __future__ import annotations

import re
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, event, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base




class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    image_path: Mapped[str] = mapped_column(String, nullable=False)

    # new
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relație
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    # new
    product_image_author: Mapped["Staff"] = relationship("Staff", foreign_keys=[author_id], back_populates="product_images")

    __table_args__ = (
        UniqueConstraint("product_id", "is_primary", name="uix_product_primary_img"),
    )

    @validates('image_path')
    def validate_image_path(self, key, value):
        if not value.strip():
            raise ValueError("Calea către imagine nu poate fi goală.")
        if not re.match(r".*\.(jpg|jpeg|png)$", value, re.IGNORECASE):
            raise ValueError("Imaginea trebuie să aibă o extensie validă (.jpg, .jpeg, .png)")
        return value




# @event.listens_for(ProductImage, "before_insert")
# def receive_before_insert(mapper, connection, target):
#     """ "listen for the 'before_insert' event" """
#
#     print("ProductImage - receive_before_insert")
#
#     print(f"ProductImage - receive_before_insert => mapper = {mapper}")
#     print(f"ProductImage - receive_before_insert => connection = {connection}")
#     print(f"ProductImage - receive_before_insert => target = {target}")
#     print(f"ProductImage - receive_before_insert => target.post_id = {target.product_id}")
#     print(f"ProductImage - receive_before_insert => target.image = {target.image}")
#
#
#     if target.product_id:
#         # product_id = str(target.product_id)
#         product_id = f"product-{target.product_id}"
#     else:
#         product_id = 'undefined'
#
#     print(f"ProductImage - receive_before_insert => post_id = {product_id}")
#
#
#     # set_current_storage(
#     #     path="./static/shop/product",
#     #     storage_id=product_id
#     # )
#
#
#
#     print("ProductImage - Inapoi in <receive_before_insert> din <set_current_storage>")
