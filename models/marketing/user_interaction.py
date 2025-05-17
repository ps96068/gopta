from __future__ import annotations

import enum
import asyncio
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, String, Enum, Integer, Index, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func



from cfg import Base
from models.base import CreatedAtMixin
from models.catalog import Category, Product
from models.blog import Post



# models/marketing/user_interaction.py


class InteractionTargetType(enum.Enum):
    category = "category"
    product = "product"
    post = "post"
    divers = "divers"

class InteractionAction(enum.Enum):
    viewed = "viewed"
    added_to_cart = "added_to_cart"
    removed_from_cart = "removed_from_cart"
    purchased = "purchased"
    shared = "shared"
    clicked_product_offer_request = "clicked_product_offer_request"
    clicked_cart_offer_request = "clicked_cart_offer_request"


class UserInteraction(Base, CreatedAtMixin):
    __tablename__ = "user_interactions"
    __table_args__ = (
        Index("ix_ui_client_time", "client_id", "created_at"),
        Index("ix_ui_target", "target_id", "target_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    action: Mapped[InteractionAction] = mapped_column(Enum(InteractionAction), nullable=False)  # Tipul de acțiune (ex: "viewed_category", "viewed_product", "viewed_post")
    target_type: Mapped[InteractionTargetType] = mapped_column(Enum(InteractionTargetType),
                                                               nullable=False)  # Tipul de entitate: categorie sau produs
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)  # ID-ul categoriei sau produsului sau postului vizualizat



    # Relații
    category: Mapped["Category | None"] = relationship(
        "Category",
        primaryjoin="and_(foreign(UserInteraction.target_id) == Category.id, UserInteraction.target_type == 'category')",
        back_populates="interactions",
        overlaps="product,category,post,interactions"
    )
    product: Mapped["Product | None"] = relationship(
        "Product",
        primaryjoin="and_(foreign(UserInteraction.target_id) == Product.id, UserInteraction.target_type == 'product')",
        back_populates="interactions",
        overlaps="category,product,post,interactions"
    )
    post: Mapped["Post | None"] = relationship(
        "Post",
        primaryjoin="and_(foreign(UserInteraction.target_id) == Post.id, UserInteraction.target_type == 'post')",
        back_populates="interactions",
        overlaps="category,product,post,interactions"
    )

    # ─────────── Relație utilizator ───────────
    client: Mapped["Client"] = relationship("Client", back_populates="interactions")



    def __repr__(self):
        return f"<UserInteraction(id={self.id}, client_id='{self.client_id}', action='{self.action}', target_id='{self.target_id}', target_type='{self.target_type}')>"

#
# @event.listens_for(UserInteraction, "before_insert")
# async def validate_target_before_insert(mapper, connection, target):
#     async with AsyncSession(connection) as session:
#         if target.target_type == InteractionTargetType.product:
#             stmt = select(Product).filter(Product.id == target.target_id)
#             result = await session.execute(stmt)
#             product = result.scalars().first()
#             if not product:
#                 raise ValueError("target_id nu corespunde unui produs valid.")
#
#         elif target.target_type == InteractionTargetType.category:
#             stmt = select(Category).filter(Category.id == target.target_id)
#             result = await session.execute(stmt)
#             category = result.scalars().first()
#             if not category:
#                 raise ValueError("target_id nu corespunde unei categorii valide.")
#
#         elif target.target_type == InteractionTargetType.post:
#             stmt = select(Post).filter(Post.id == target.target_id)
#             result = await session.execute(stmt)
#             post = result.scalars().first()
#             if not post:
#                 raise ValueError("target_id nu corespunde unui post valid.")
#
#
# @event.listens_for(UserInteraction, "before_update")
# async def validate_target_before_update(mapper, connection, target):
#     async with AsyncSession(connection) as session:
#         if target.target_type == InteractionTargetType.product:
#             stmt = select(Product).filter(Product.id == target.target_id)
#             result = await session.execute(stmt)
#             product = result.scalars().first()
#             if not product:
#                 raise ValueError("target_id nu corespunde unui produs valid.")
#
#         elif target.target_type == InteractionTargetType.category:
#             stmt = select(Category).filter(Category.id == target.target_id)
#             result = await session.execute(stmt)
#             category = result.scalars().first()
#             if not category:
#                 raise ValueError("target_id nu corespunde unei categorii valide.")
#
#         elif target.target_type == InteractionTargetType.post:
#             stmt = select(Post).filter(Post.id == target.target_id)
#             result = await session.execute(stmt)
#             post = result.scalars().first()
#             if not post:
#                 raise ValueError("target_id nu corespunde unui post valid.")
#
