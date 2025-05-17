from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import UserInteraction, InteractionTargetType
from models.catalog import Category, Product
from models.blog import Post



# models.marketing/signals/user_interaction_signals.py
#
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
#
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
#
#
#
#
# event.listen(UserInteraction, "before_insert", validate_target_before_insert)
# event.listen(UserInteraction, "before_update", validate_target_before_update)

