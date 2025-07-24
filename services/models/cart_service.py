# services/models/cart_service.py

from __future__ import annotations

from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.sale import Cart, CartItem, Invoice
from models.user import Client
from models.enum import UserStatus, InvoiceType
from services.models.product_service import ProductService


class CartService:
    """Service pentru gestionarea coșului."""

    @staticmethod
    async def get_or_create_cart(
            db: AsyncSession,
            client_id: int,
            session_id: Optional[str] = None
    ) -> Cart:
        """Obține sau creează coș pentru client."""
        result = await db.execute(
            select(Cart)
            .where(Cart.client_id == client_id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .order_by(Cart.created_at.desc())
        )
        cart = result.scalar_one_or_none()

        cart_number = await CartService._generate_cart_number(db)

        if not cart:
            cart = Cart(
                client_id=client_id,
                cart_number=cart_number,
                session_id=session_id,
                total_amount=0.0
            )
            db.add(cart)
            await db.commit()
            await db.refresh(cart)

        return cart

    @staticmethod
    async def add_item(
            db: AsyncSession,
            cart_id: int,
            product_id: int,
            quantity: int,
            user_status: UserStatus
    ) -> CartItem:
        """Adaugă produs în coș."""
        # Verifică dacă produsul există deja în coș
        result = await db.execute(
            select(CartItem).where(
                and_(
                    CartItem.cart_id == cart_id,
                    CartItem.product_id == product_id
                )
            )
        )
        existing_item = result.scalar_one_or_none()

        # Obține prețul pentru status-ul utilizatorului
        price = await ProductService.get_price_for_user_status(
            db, product_id, user_status
        )

        if existing_item:
            existing_item.quantity += quantity
            existing_item.price_snapshot = price
            existing_item.price_type = user_status.value
        else:
            existing_item = CartItem(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
                price_snapshot=price,
                price_type=user_status.value
            )
            db.add(existing_item)

        await db.commit()
        await db.refresh(existing_item)
        return existing_item

    @staticmethod
    async def get_cart_total(
            db: AsyncSession,
            cart_id: int,
    )-> float:
        """Calculează totalul coșului."""

        stmt = select(
            func.sum(CartItem.quantity * CartItem.price_snapshot)
        ).where(CartItem.cart_id == cart_id)

        result = await db.execute(stmt)
        total = result.scalar() or 0

        return float(total)


    @staticmethod
    async def update_quantity(
            db: AsyncSession,
            cart_item_id: int,
            quantity: int
    ) -> Optional[CartItem]:
        """Actualizează cantitatea unui item."""
        result = await db.execute(
            select(CartItem).where(CartItem.id == cart_item_id)
        )
        item = result.scalar_one_or_none()

        if item:
            if quantity <= 0:
                await db.delete(item)
            else:
                item.quantity = quantity
            await db.commit()

        return item if quantity > 0 else None

    @staticmethod
    async def clear_cart(db: AsyncSession, cart_id: int) -> None:
        """Golește coșul."""
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id)
        )
        items = result.scalars().all()

        for item in items:
            await db.delete(item)

        await db.commit()

    @staticmethod
    async def calculate_total(db: AsyncSession, cart_id: int) -> float:
        """Calculează totalul coșului."""
        result = await db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id)
        )
        items = result.scalars().all()

        total = sum(
            float(item.price_snapshot) * item.quantity
            for item in items
        )
        return total

    @staticmethod
    async def get_cart_with_details(
            db: AsyncSession,
            cart_id: int
    ) -> Optional[Cart]:
        """Obține coș cu toate detaliile necesare."""
        result = await db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                selectinload(Cart.client),
                selectinload(Cart.items).selectinload(CartItem.product),
                selectinload(Cart.invoice)  # Include ofertele generate
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def has_active_quote(
            db: AsyncSession,
            cart_id: int
    ) -> bool:
        """Verifică dacă coșul are o ofertă activă (neexpirată)."""
        result = await db.execute(
            select(Invoice)
            .where(
                and_(
                    Invoice.cart_id == cart_id,
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.converted_to_order == False,
                    Invoice.valid_until > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_active_quotes(
            db: AsyncSession,
            cart_id: int
    ) -> List[Invoice]:
        """Obține toate ofertele active pentru un coș."""
        result = await db.execute(
            select(Invoice)
            .where(
                and_(
                    Invoice.cart_id == cart_id,
                    Invoice.invoice_type == InvoiceType.QUOTE,
                    Invoice.converted_to_order == False,
                    Invoice.valid_until > datetime.utcnow()
                )
            )
            .order_by(Invoice.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def generate_quote(
            db: AsyncSession,
            cart_id: int,
            valid_days: int = 30,
            notes: Optional[str] = None
    ) -> Invoice:
        """
        Generează ofertă pentru coș.
        Wrapper pentru InvoiceService.create_quote_from_cart
        """
        from services.models.invoice_service import InvoiceService

        return await InvoiceService.create_quote_from_cart(
            db=db,
            cart_id=cart_id,
            valid_days=valid_days,
            notes=notes
        )

    @staticmethod
    async def get_cart_summary(
            db: AsyncSession,
            cart_id: int
    ) -> Dict:
        """Obține sumar detaliat al coșului."""
        cart = await CartService.get_cart_with_details(db, cart_id)

        if not cart:
            return None

        # Calculează totaluri
        subtotal = sum(
            float(item.price_snapshot) * item.quantity
            for item in cart.items
        )

        # Numără produse unice și cantitate totală
        unique_products = len(cart.items)
        total_quantity = sum(item.quantity for item in cart.items)

        # Verifică oferte
        active_quotes = await CartService.get_active_quotes(db, cart_id)

        return {
            "cart_id": cart_id,
            "client_id": cart.client_id,
            "client_name": f"{cart.client.first_name or ''} {cart.client.last_name or ''}".strip() or "Client",
            "items_count": unique_products,
            "total_quantity": total_quantity,
            "subtotal": subtotal,
            "has_active_quote": len(active_quotes) > 0,
            "active_quotes_count": len(active_quotes),
            "latest_quote": active_quotes[0] if active_quotes else None,
            "created_at": cart.created_at,
            "updated_at": cart.updated_at
        }

    @staticmethod
    async def duplicate_cart(
            db: AsyncSession,
            cart_id: int,
            client_id: int
    ) -> Cart:
        """
        Duplică un coș pentru un client.
        Util pentru a crea o comandă nouă bazată pe una anterioară.
        """
        # Obține coșul original
        original = await CartService.get_cart_with_details(db, cart_id)
        if not original:
            raise ValueError(f"Cart {cart_id} not found")

        # Creează coș nou
        new_cart = Cart(client_id=client_id)
        db.add(new_cart)
        await db.flush()

        # Copiază items
        for item in original.items:
            new_item = CartItem(
                cart_id=new_cart.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_snapshot=item.price_snapshot,
                price_type=item.price_type
            )
            db.add(new_item)

        await db.commit()
        await db.refresh(new_cart)

        return new_cart

    @staticmethod
    async def _generate_cart_number(db: AsyncSession) -> str:
        """
        Generează număr unic de comandă.
        Format: PCE-YYYYMMDD-XXXX
        """
        today = datetime.now().strftime("%Y%m%d")

        # Numără comenzile din ziua curentă
        result = await db.execute(
            select(func.count(Cart.id))
            .where(Cart.cart_number.like(f"Oferta-{today}-%"))
        )
        count = result.scalar() or 0

        return f"Oferta-{today}-{count + 1:04d}"

    @staticmethod
    async def clear_and_delete_cart(db: AsyncSession, cart_id: int) -> None:
        """Golește și șterge complet coșul."""
        # Mai întâi golește coșul
        await CartService.clear_cart(db, cart_id)

        # Apoi șterge înregistrarea cart
        result = await db.execute(
            select(Cart).where(Cart.id == cart_id)
        )
        cart = result.scalar_one_or_none()

        if cart:
            await db.delete(cart)
            await db.commit()