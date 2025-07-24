# services/models/product_price_services.py


from __future__ import annotations
from typing import Optional, List, Dict
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from models import PriceType, ProductPrice


class ProductPriceService:
    """Service pentru gestionarea prețurilor."""

    @staticmethod
    async def set_price(
            db: AsyncSession,
            product_id: int,
            price_type: PriceType,
            amount: float
    ) -> ProductPrice:
        """Setează sau actualizează un preț."""
        result = await db.execute(
            select(ProductPrice).where(
                and_(
                    ProductPrice.product_id == product_id,
                    ProductPrice.price_type == price_type
                )
            )
        )
        price = result.scalar_one_or_none()

        if price:
            price.amount = amount
        else:
            price = ProductPrice(
                product_id=product_id,
                price_type=price_type,
                amount=amount
            )
            db.add(price)

        await db.commit()
        await db.refresh(price)
        return price

    @staticmethod
    async def bulk_update_prices(
            db: AsyncSession,
            product_id: int,
            prices: Dict[PriceType, float]
    ) -> List[ProductPrice]:
        """Actualizează toate prețurile unui produs."""
        updated = []
        for price_type, amount in prices.items():
            price = await ProductPriceService.set_price(
                db, product_id, price_type, amount
            )
            updated.append(price)
        return updated