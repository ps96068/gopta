from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import Index, ForeignKey, DateTime, Text, Enum, Integer, CheckConstraint, event
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func


from cfg import Base
from models.base import CreatedAtMixin


# models/marketing/user_request.py

class RequestTypeEnum(enum.Enum):
    product = "product"
    order = "order"
    general = "general"


class UserRequest(Base, CreatedAtMixin):
    __tablename__ = "user_requests"
    __table_args__ = (
        CheckConstraint(
            "(request_type = 'product' AND product_id IS NOT NULL AND order_id IS NULL) OR "
            "(request_type = 'order'   AND order_id   IS NOT NULL AND product_id IS NULL) OR "
            "(request_type = 'general' AND product_id IS NULL AND order_id   IS NULL)",
            name="check_request_type_consistency",
        ),
        Index("ix_user_requests_client_type", "client_id", "request_type"),
    )


    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id",   ondelete="SET NULL"), nullable=True)

    request_type: Mapped[RequestTypeEnum] = mapped_column(Enum(RequestTypeEnum), nullable=False)
    request_details: Mapped[str] = mapped_column(Text, nullable=False)


    # Relații
    client: Mapped["Client"] = relationship("Client", back_populates="requests")
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="requests",
        foreign_keys=[product_id],
        uselist=False
    )
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="requests",
        foreign_keys=[order_id],
        uselist=False
    )

    @validates("request_details")
    def validate_request_details(self, key, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Detaliile cererii nu pot fi goale.")
        return value

    @validates("request_type", "product_id", "order_id")
    def validate_consistency(self, key: str, value):
        # Aplicăm temporar modificarea
        setattr(self, key, value)
        # Verificăm regula de consistență
        if self.request_type == RequestTypeEnum.product:
            if self.product_id is None or self.order_id is not None:
                raise ValueError(
                    "Pentru request_type='product', product_id trebuie setat și order_id trebuie NULL."
                )
        elif self.request_type == RequestTypeEnum.order:
            if self.order_id is None or self.product_id is not None:
                raise ValueError(
                    "Pentru request_type='order', order_id trebuie setat și product_id trebuie NULL."
                )
        elif self.request_type == RequestTypeEnum.general:
            if self.product_id is not None or self.order_id is not None:
                raise ValueError(
                    "Pentru request_type='general', nici product_id și nici order_id nu trebuie setate."
                )
        return value

    def __repr__(self):
        return (
            f"<UserRequest(id={self.id}, client_id={self.client_id}, "
            f"type={self.request_type.value}, details={self.request_details!r})>"
        )



#
# @event.listens_for(UserRequest, "before_insert")
# async def validate_before_insert(mapper, connection, target):
#     if target.request_type == RequestTypeEnum.product and not target.product_id:
#         raise ValueError("Pentru request_type='product', product_id trebuie să fie setat.")
#     if target.request_type == RequestTypeEnum.order and not target.order_id:
#         raise ValueError("Pentru request_type='order', order_id trebuie să fie setat.")
#     if target.request_type == RequestTypeEnum.general and (target.product_id or target.order_id):
#         raise ValueError("Pentru request_type='general', product_id și order_id trebuie să fie NULL.")
#
