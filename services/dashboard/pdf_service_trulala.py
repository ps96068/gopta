# services/dashboard/pdf_service.py
"""
Service pentru generare PDF-uri (facturi și oferte).
Folosește WeasyPrint pentru conversie HTML -> PDF.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Invoice, InvoiceType, Cart, Order, CartItem, OrderItem


class PDFService:
    """Service pentru generare PDF-uri."""

    # Configurare paths
    TEMPLATE_DIR = Path("server/dashboard/templates/staff/invoice/PDF")
    OUTPUT_DIR = Path("server/dashboard/static/PDF/invoices")

    # Cache pentru template environment
    _template_env = None

    @classmethod
    def _get_template_env(cls) -> Environment:
        """Obține Jinja2 environment cu cache."""
        if cls._template_env is None:
            cls._template_env = Environment(
                loader=FileSystemLoader(cls.TEMPLATE_DIR),
                autoescape=True
            )
            # Adaugă filtre custom
            cls._template_env.filters['int'] = int
            cls._template_env.filters['date_ro'] = lambda d: d.strftime("%d.%m.%Y") if d else ""
        return cls._template_env

    @staticmethod
    def _ensure_directory_structure(invoice_number: str) -> Path:
        """
        Creează structura de directoare pentru anul/luna curentă.
        Format: /2024/12/
        """
        now = datetime.now()
        year_month_path = PDFService.OUTPUT_DIR / str(now.year) / f"{now.month:02d}"
        year_month_path.mkdir(parents=True, exist_ok=True)
        return year_month_path

    @staticmethod
    async def generate_invoice_pdf(
            invoice: Invoice,
            db: AsyncSession,
            force_regenerate: bool = False
    ) -> str:
        """
        Generează PDF și returnează path-ul relativ.

        Args:
            invoice: Invoice object
            db: Database session
            force_regenerate: Regenerează chiar dacă există

        Returns:
            Path relativ către PDF (ex: server/dashboard/static/PDF/invoices/2024/12/O_20241225_0001.pdf)
        """
        # Verifică dacă PDF există deja
        if invoice.document_path and not force_regenerate:
            if Path(invoice.document_path).exists():
                return invoice.document_path

        # Obține date complete pentru invoice
        if invoice.invoice_type == InvoiceType.QUOTE and invoice.cart_id:
            # Pentru ofertă - date din Cart
            result = await db.execute(
                select(Cart)
                .where(Cart.id == invoice.cart_id)
                .options(
                    selectinload(Cart.items).selectinload(CartItem.product),
                    selectinload(Cart.client)
                )
            )
            cart = result.scalar_one()
            items = [
                {
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'quantity': item.quantity,
                    'unit_price': float(item.price_snapshot),
                    'subtotal': float(item.price_snapshot) * item.quantity,
                    'price_type': item.price_type
                }
                for item in cart.items
            ]
            client = cart.client

        elif invoice.invoice_type == InvoiceType.INVOICE and invoice.order_id:
            # Pentru factură - date din Order
            result = await db.execute(
                select(Order)
                .where(Order.id == invoice.order_id)
                .options(
                    selectinload(Order.items),
                    selectinload(Order.client)
                )
            )
            order = result.scalar_one()
            items = [
                {
                    'name': item.product_name,
                    'sku': item.product_sku,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'subtotal': float(item.subtotal),
                    'price_type': item.price_type
                }
                for item in order.items
            ]
            client = order.client
        else:
            raise ValueError("Invoice invalid - lipsește cart_id sau order_id")

        # Calculează totaluri
        subtotal = sum(item['subtotal'] for item in items)
        tva_amount = subtotal * 0.20  # TVA 20%

        # Date pentru template
        context = {
            'invoice': invoice,
            'client': client,
            'items': items,
            'subtotal': subtotal,
            'tva_amount': tva_amount,
            'total': float(invoice.total_amount),
            'company': {
                'name': 'PCE Distribution SRL',
                'address': 'str. Mihai Eminescu 47, Chișinău',
                'phone': '+373 22 123 456',
                'email': 'contact@pce.md',
                'cui': '1234567890',
                'iban': 'MD12 AG00 0000 0000 1234 5678'
            },
            'generated_at': datetime.now()
        }

        # Selectează template
        template_name = 'quote_template.html' if invoice.is_quote else 'invoice_template.html'

        # Generează HTML
        env = PDFService._get_template_env()
        template = env.get_template(template_name)
        html_content = template.render(**context)

        # Creează directorul pentru output
        output_dir = PDFService._ensure_directory_structure(invoice.invoice_number)

        # Nume fișier
        filename = f"{invoice.invoice_number}.pdf"
        output_path = output_dir / filename

        # Generează PDF cu WeasyPrint
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string="""
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.6;
                }
            """)]
        )

        # Returnează path relativ
        relative_path = str(output_path.relative_to(Path.cwd()))
        return relative_path

    @staticmethod
    def delete_invoice_pdf(document_path: str) -> bool:
        """Șterge PDF-ul unei facturi."""
        try:
            if document_path and Path(document_path).exists():
                Path(document_path).unlink()
                return True
        except Exception as e:
            print(f"Error deleting PDF: {e}")
        return False

    @staticmethod
    async def regenerate_all_pdfs(db: AsyncSession, invoice_type: Optional[InvoiceType] = None) -> int:
        """
        Regenerează toate PDF-urile (util după schimbare template).

        Args:
            db: Database session
            invoice_type: Regenerează doar un tip specific

        Returns:
            Număr de PDF-uri regenerate
        """
        query = select(Invoice)
        if invoice_type:
            query = query.where(Invoice.invoice_type == invoice_type)

        result = await db.execute(query)
        invoices = result.scalars().all()

        count = 0
        for invoice in invoices:
            try:
                new_path = await PDFService.generate_invoice_pdf(invoice, db, force_regenerate=True)
                invoice.document_path = new_path
                count += 1
            except Exception as e:
                print(f"Failed to regenerate PDF for {invoice.invoice_number}: {e}")

        await db.commit()
        return count