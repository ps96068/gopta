# services/models/vendor_company_service.py

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import VendorCompany, Product, OrderItem, Order, OrderStatus, ProductPrice


class VendorCompanyService:
    """Service pentru gestionarea companiilor vendor."""

    @staticmethod
    async def create(
            db: AsyncSession,
            name: str,
            legal_name: str,
            tax_id: str,
            email: str,
            phone: str,
            address: str,
            is_active: bool = True,
            **kwargs
    ) -> VendorCompany:
        """Creează companie vendor nouă."""
        company = VendorCompany(
            name=name,
            legal_name=legal_name,
            tax_id=tax_id,
            email=email,
            phone=phone,
            address=address,
            is_active=is_active,
            **kwargs
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)




        return company

    @staticmethod
    async def get_by_id(
            db: AsyncSession,
            company_id: int,
            include_staff: bool = False
    ) -> Optional[VendorCompany]:
        """Găsește companie după ID."""
        query = select(VendorCompany).where(VendorCompany.id == company_id)

        if include_staff:
            query = query.options(selectinload(VendorCompany.staff_members))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_company(
            db: AsyncSession,
            company_id: int,
            staff_id: int
    ) -> VendorCompany:
        """Verifică și aprobă o companie vendor."""
        company = await VendorCompanyService.get_by_id(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        company.is_verified = True
        company.verified_at = datetime.utcnow()
        company.verified_by_id = staff_id

        await db.commit()
        await db.refresh(company)
        return company

    @staticmethod
    async def get_statistics(
            db: AsyncSession,
            company_id: int
    ) -> dict:
        """Obține statistici pentru companie - inclusiv produse inactive."""
        from sqlalchemy import case

        # Total produse cu breakdown active/inactive
        products_stats = await db.execute(
            select(
                func.count(Product.id).label('total_products'),
                func.sum(case((Product.is_active == True, 1), else_=0)).label('active_products'),
                func.sum(case((Product.is_active == False, 1), else_=0)).label('inactive_products')
            ).where(Product.vendor_company_id == company_id)
        )
        products_row = products_stats.first()

        # Comenzi și venituri
        orders_stats = await db.execute(
            select(
                func.count(distinct(Order.id)).label('total_orders'),
                func.sum(OrderItem.subtotal).label('total_revenue')
            )
            .select_from(OrderItem)
            .join(Product)
            .join(Order)
            .where(
                Product.vendor_company_id == company_id,
                Order.status.in_([OrderStatus.PROCESSING, OrderStatus.COMPLETED])
            )
        )
        stats_row = orders_stats.first()

        # Statistici prețuri - doar dacă există produse
        total_prices = 0
        active_prices = 0
        inactive_prices = 0

        if products_row.total_products > 0:
            prices_stats = await db.execute(
                select(
                    func.count(ProductPrice.id).label('total_prices'),
                    func.sum(case((ProductPrice.is_active == True, 1), else_=0)).label('active_prices'),
                    func.sum(case((ProductPrice.is_active == False, 1), else_=0)).label('inactive_prices')
                )
                .select_from(Product)
                .join(ProductPrice)
                .where(Product.vendor_company_id == company_id)
            )
            prices_row = prices_stats.first()

            total_prices = prices_row.total_prices or 0
            active_prices = prices_row.active_prices or 0
            inactive_prices = prices_row.inactive_prices or 0

        return {
            # Produse - FIX: folosește products_row, nu prices_row
            'total_products': products_row.total_products or 0,
            'active_products': products_row.active_products or 0,
            'inactive_products': products_row.inactive_products or 0,  # FIX: era prices_row.inactive_products

            # Prețuri
            'total_prices': total_prices,
            'active_prices': active_prices,
            'inactive_prices': inactive_prices,

            # Comenzi și financiar
            'total_orders': stats_row.total_orders or 0,
            'total_revenue': float(stats_row.total_revenue or 0),
            'commission_due': 0  # TODO: calculează comision
        }
