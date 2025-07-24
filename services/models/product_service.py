# services/models/product_services.py

from __future__ import annotations
from typing import Optional, List, Dict
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from models import Product, ProductImage, UserStatus, PriceType, ProductPrice
from services.models.product_price_service import ProductPriceService


class ProductService:
    """Service pentru gestionarea produselor."""

    @staticmethod
    async def get_by_category(
            db: AsyncSession,
            category_id: int,
            skip: int = 0,
            limit: int = 20
    ) -> List[Product]:
        """Returnează produse dintr-o categorie - doar cu prețuri active."""
        result = await db.execute(
            select(Product)
            .where(
                and_(
                    Product.category_id == category_id,
                    Product.is_active == True,
                    Product.in_stock == True
                )
            )
            .options(
                selectinload(Product.images),
                selectinload(Product.prices.and_(ProductPrice.is_active == True))  # Doar prețuri active
            )
            .order_by(Product.sort_order)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Product]:
        """Găsește produs după slug cu toate relațiile - doar prețuri active."""
        result = await db.execute(
            select(Product)
            .where(
                and_(
                    Product.slug == slug,
                    Product.is_active == True
                )
            )
            .options(
                selectinload(Product.vendor_company),
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.prices.and_(ProductPrice.is_active == True))  # Doar prețuri active
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_price_for_user_status(
            db: AsyncSession,
            product_id: int,
            user_status: UserStatus
    ) -> Optional[float]:
        """Returnează prețul pentru un status de utilizator - doar din prețuri active."""
        # Mapare status -> price type
        status_to_price = {
            UserStatus.ANONIM: PriceType.ANONIM,
            UserStatus.USER: PriceType.USER,
            UserStatus.INSTALATOR: PriceType.INSTALATOR,
            UserStatus.PRO: PriceType.PRO
        }

        price_type = status_to_price.get(user_status)
        if not price_type:
            return None

        result = await db.execute(
            select(ProductPrice.amount)
            .where(
                and_(
                    ProductPrice.product_id == product_id,
                    ProductPrice.price_type == price_type,
                    ProductPrice.is_active == True  # DOAR PREȚURI ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_prices_for_status(
            db: AsyncSession,
            product_id: int,
            user_status: UserStatus
    ) -> Dict[str, float]:
        """Returnează toate prețurile vizibile pentru un status - doar active."""
        # Determinăm ce prețuri poate vedea
        visible_prices = []
        if user_status == UserStatus.ANONIM:
            visible_prices = [PriceType.ANONIM]
        elif user_status == UserStatus.USER:
            visible_prices = [PriceType.ANONIM, PriceType.USER]
        elif user_status == UserStatus.INSTALATOR:
            visible_prices = [PriceType.ANONIM, PriceType.USER, PriceType.INSTALATOR]
        elif user_status == UserStatus.PRO:
            visible_prices = list(PriceType)  # toate

        result = await db.execute(
            select(ProductPrice)
            .where(
                and_(
                    ProductPrice.product_id == product_id,
                    ProductPrice.price_type.in_(visible_prices),
                    ProductPrice.is_active == True  # DOAR PREȚURI ACTIVE
                )
            )
        )
        prices = result.scalars().all()

        return {
            price.price_type.value: float(price.amount)
            for price in prices
        }

    @staticmethod
    async def search(
            db: AsyncSession,
            query: str,
            vendor_company_id: Optional[int] = None,
            skip: int = 0,
            limit: int = 20
    ) -> List[Product]:
        """Caută produse după nume sau SKU - doar active cu prețuri active."""
        stmt = select(Product).where(
            and_(
                Product.is_active == True,
                Product.in_stock == True,
                Product.name.ilike(f"%{query}%") | Product.sku.ilike(f"%{query}%")
            )
        )

        if vendor_company_id:
            stmt = stmt.where(Product.vendor_company_id == vendor_company_id)

        stmt = stmt.options(
            selectinload(Product.images),
            selectinload(Product.prices.and_(ProductPrice.is_active == True))  # Doar prețuri active
        ).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def add_image(
            db: AsyncSession,
            product_id: int,
            image_path: str,
            file_name: str,
            file_size: int,
            alt_text: Optional[str] = None,
            is_primary: bool = False
    ) -> ProductImage:
        """Adaugă imagine la produs."""
        # Dacă e primary, dezactivează alte primary
        if is_primary:
            result = await db.execute(
                select(ProductImage)
                .where(ProductImage.product_id == product_id)
                .where(ProductImage.is_primary == True)
            )
            existing_primary = result.scalars().all()
            for img in existing_primary:
                img.is_primary = False

        image = ProductImage(
            product_id=product_id,
            image_path=image_path,
            file_name=file_name,
            file_size=file_size,
            alt_text=alt_text,
            is_primary=is_primary
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    @staticmethod
    async def delete_image(
            db: AsyncSession,
            image_id: int
    ) -> bool:
        """Șterge imagine produs (din DB și de pe disk)."""
        from services.dashboard.file_service import FileService

        result = await db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()

        if image:
            # Șterge fișierul fizic
            FileService.delete_image(image.image_path)

            # Șterge din DB
            await db.delete(image)
            await db.commit()
            return True

        return False

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

    @staticmethod
    async def reactivate_company_products(
            db: AsyncSession,
            company_id: int,
            staff_id: int
    ) -> Dict[str, int]:
        """
        Reactivează produsele și prețurile unei companii.
        Utilizat când compania este reactivată.
        """
        # 1. Reactivează produsele
        products_result = await db.execute(
            update(Product)
            .where(Product.vendor_company_id == company_id)
            .values(is_active=True)
        )
        products_count = products_result.rowcount

        # 2. Obține ID-urile produselor
        products_ids_result = await db.execute(
            select(Product.id).where(Product.vendor_company_id == company_id)
        )
        product_ids = [row[0] for row in products_ids_result.fetchall()]

        # 3. Reactivează prețurile
        prices_count = 0
        if product_ids:
            prices_result = await db.execute(
                update(ProductPrice)
                .where(ProductPrice.product_id.in_(product_ids))
                .values(is_active=True)
            )
            prices_count = prices_result.rowcount

        await db.commit()

        print(f"✅ REACTIVARE: {products_count} produse, {prices_count} prețuri")
        print(f"🔍 AUDIT: Staff {staff_id} a reactivat produsele companiei {company_id}")

        return {
            "products_reactivated": products_count,
            "prices_reactivated": prices_count
        }






