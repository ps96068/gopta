# services/dashboard/pdf_service_reportlab.py
"""
Service pentru generare PDF-uri folosind ReportLab (alternativă la WeasyPrint).

"""

from __future__ import annotations
import os
import pprint
import traceback
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Invoice, InvoiceType, Cart, Order, CartItem, OrderItem


class NumberedCanvas:
    """Canvas personalizat pentru numerotare pagini."""

    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
        self.page_num = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def save(self):
        """Salvează canvas-ul și adaugă numărul paginii."""
        self.page_num += 1
        self.draw_page_number()
        self.canvas.save()

    def draw_page_number(self):
        """Desenează numărul paginii în colțul din dreapta jos."""
        self.canvas.setFont("Helvetica", 10)
        self.canvas.drawRightString(
            A4[0] - 1.5 * cm,  # X - margine dreapta
            1.5 * cm,  # Y - margine jos
            f"Pagina {self.page_num}"
        )


def add_page_numbers(canvas, doc):
    """Funcție callback pentru adăugarea numerelor de pagină."""
    canvas.saveState()

    # Setează font și culoare
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.grey)

    # Desenează numărul paginii
    page_num = canvas.getPageNumber()
    text = f"Pagina {page_num}"

    # Poziționează în colțul din dreapta jos
    canvas.drawRightString(
        A4[0] - 1.5 * cm,  # X - la 1.5cm de marginea dreaptă
        1.5 * cm,  # Y - la 1.5cm de marginea de jos
        text
    )

    canvas.restoreState()


class PDFService:
    """Service pentru generare PDF-uri cu ReportLab."""

    # Configurare paths
    OUTPUT_DIR = Path("server/dashboard/static/PDF/invoices")

    @staticmethod
    def _ensure_directory_structure(invoice_number: str) -> Path:
        """Creează structura de directoare pentru anul/luna curentă."""
        try:
            now = datetime.now()
            year_month_path = PDFService.OUTPUT_DIR / str(now.year) / f"{now.month:02d}"
            year_month_path.mkdir(parents=True, exist_ok=True)
            print(f"[PDFService] Created directory: {year_month_path}")
            return year_month_path
        except Exception as e:
            print(f"[PDFService] ERROR creating directory: {e}")
            raise

    @staticmethod
    def _register_fonts():
        """Înregistrează fonturi Roboto pentru suport UTF-8 complet."""
        try:
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfbase import pdfmetrics

            # Definește căile către fonturile Roboto
            # Descarcă fonturile de la: https://fonts.google.com/specimen/Roboto
            # și pune-le în directorul specificat

            font_dir = Path("server/dashboard/static/fonts")
            font_dir.mkdir(parents=True, exist_ok=True)

            fonts_to_register = {
                'Roboto': 'Roboto-Regular.ttf',
                'Roboto-Bold': 'Roboto-Bold.ttf',
                'Roboto-Italic': 'Roboto-Italic.ttf',
                'Roboto-BoldItalic': 'Roboto-BoldItalic.ttf',
            }

            registered = False
            for font_name, font_file in fonts_to_register.items():
                font_path = font_dir / font_file
                if font_path.exists():
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                        print(f"[PDFService] Registered font: {font_name}")
                        registered = True
                    except Exception as e:
                        print(f"[PDFService] Failed to register {font_name}: {e}")
                else:
                    print(f"[PDFService] Font file not found: {font_path}")

            if not registered:
                # Fallback la Arial Unicode (dacă există în sistem)
                try:
                    # Pe Windows
                    pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                    print("[PDFService] Fallback to Arial fonts")
                except:
                    print("[PDFService] WARNING: No UTF-8 fonts available!")

        except Exception as e:
            print(f"[PDFService] Font registration error: {e}")

    @staticmethod
    def _create_styles():
        """Creează stiluri pentru document cu font Roboto."""
        styles = getSampleStyleSheet()

        # Font implicit pentru document
        default_font = 'Roboto'
        bold_font = 'Roboto-Bold'

        # Verifică dacă fonturile sunt înregistrate
        from reportlab.pdfbase import pdfmetrics
        if default_font not in pdfmetrics.getRegisteredFontNames():
            default_font = 'Arial'  # Fallback la Arial care suportă diacritice
            bold_font = 'Arial-Bold'
            print(f"[PDFService] Using fallback fonts: {default_font}")

        # Actualizează stilul Normal pentru tot documentul
        styles['Normal'].fontName = default_font
        styles['Normal'].fontSize = 11
        styles['Normal'].leading = 14  # Spațiere între linii

        # Stil pentru titlu companie
        styles.add(ParagraphStyle(
            name='CompanyTitle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=24,
            leading=30,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_LEFT
        ))

        # Stil pentru subtitlu
        styles.add(ParagraphStyle(
            name='DocumentType',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#e74c3c'),
            alignment=TA_RIGHT
        ))

        # Stil pentru număr document
        styles.add(ParagraphStyle(
            name='DocumentNumber',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=14,
            leading=18,
            alignment=TA_RIGHT
        ))

        # Stil pentru secțiuni
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading3'],
            fontName=bold_font,
            fontSize=14,
            leading=20,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12
        ))

        return styles

    @staticmethod
    async def generate_invoice_pdf(
            invoice: Invoice,
            db: AsyncSession,
            force_regenerate: bool = False
    ) -> str:
        """Generează PDF folosind ReportLab."""

        print(f"\n{'=' * 60}")
        print(f"[PDFService] Starting PDF generation for invoice {invoice.invoice_number}")
        print(f"[PDFService] Invoice type: {invoice.invoice_type}")
        print(f"[PDFService] Invoice ID: {invoice.id}")
        print(f"[PDFService] Cart ID: {invoice.cart_id}, Order ID: {invoice.order_id}")
        print(f"{'=' * 60}\n")

        PDFService.debug_fonts()

        try:
            # Verifică dacă PDF există deja
            if invoice.document_path and not force_regenerate:
                if Path(invoice.document_path).exists():
                    print(f"[PDFService] PDF already exists at {invoice.document_path}")
                    return invoice.document_path

            # Înregistrează fonturi
            PDFService._register_fonts()

            # Obține date pentru invoice
            print(f"[PDFService] Fetching data for invoice type: {invoice.invoice_type}")

            if invoice.invoice_type == InvoiceType.QUOTE and invoice.cart_id:
                result = await db.execute(
                    select(Cart)
                    .where(Cart.id == invoice.cart_id)
                    .options(
                        selectinload(Cart.items).selectinload(CartItem.product),
                        selectinload(Cart.client)
                    )
                )
                cart = result.scalar_one_or_none()

                if not cart:
                    raise ValueError(f"Cart {invoice.cart_id} not found")

                items = [
                    {
                        'name': item.product.name if item.product else "Produs necunoscut",
                        'sku': item.product.sku if item.product else "N/A",
                        'quantity': item.quantity,
                        'unit_price': float(item.price_snapshot),
                        'subtotal': float(item.price_snapshot) * item.quantity,
                    }
                    for item in cart.items
                ]
                client = cart.client
                print(f"[PDFService] Found {len(items)} items in cart")

            elif invoice.invoice_type == InvoiceType.INVOICE and invoice.order_id:
                result = await db.execute(
                    select(Order)
                    .where(Order.id == invoice.order_id)
                    .options(
                        selectinload(Order.items),
                        selectinload(Order.client)
                    )
                )
                order = result.scalar_one_or_none()

                if not order:
                    raise ValueError(f"Order {invoice.order_id} not found")

                items = [
                    {
                        'name': item.product_name,
                        'sku': item.product_sku,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'subtotal': float(item.subtotal),
                    }
                    for item in order.items
                ]
                client = order.client
                print(f"[PDFService] Found {len(items)} items in order")
            else:
                raise ValueError("Invoice has no cart_id or order_id")

            # Calculează totaluri
            subtotal = sum(item['subtotal'] for item in items)
            tva_amount = subtotal * 0.20
            total = float(invoice.total_amount)

            print(f"[PDFService] Totals - Subtotal: {subtotal}, TVA: {tva_amount}, Total: {total}")

            # Creează directorul
            output_dir = PDFService._ensure_directory_structure(invoice.invoice_number)
            filename = f"{invoice.invoice_number}.pdf"
            output_path = output_dir / filename

            print(f"[PDFService] Output path: {output_path}")

            # Creează PDF cu margini mai mici
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=A4,
                rightMargin=1.5 * cm,  # Redus de la 2cm
                leftMargin=1.5 * cm,  # Redus de la 2cm
                topMargin=2 * cm,
                bottomMargin=2 * cm,
                title=f"{invoice.invoice_number}",
                author="PCE Distribution SRL"
            )

            # Stiluri
            styles = PDFService._create_styles()

            # Conținut
            story = []

            # Header
            company_data = [
                [
                    Paragraph("PCE Distribution SRL", styles['CompanyTitle']),
                    Paragraph("OFERTĂ" if invoice.is_quote else "FACTURĂ", styles['DocumentType'])
                ],
                [
                    Paragraph("str. Mihai Eminescu 47, Chișinău<br/>Tel: +373 22 123 456<br/>Email: contact@pce.md",
                              styles['Normal']),
                    Paragraph(f"{invoice.invoice_number}<br/>Data: {invoice.created_at.strftime('%d.%m.%Y')}",
                              styles['DocumentNumber'])
                ]
            ]

            header_table = Table(company_data, colWidths=[11.5 * cm, 6.5 * cm])  # Ajustat pentru margini mai mici
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 0.5 * inch))

            # Date client
            story.append(Paragraph("DATE CLIENT", styles['SectionTitle']))

            client_info = f"""
            <b>Nume:</b> {invoice.client_name}<br/>
            <b>Email:</b> {invoice.client_email or 'N/A'}<br/>
            """
            if invoice.client_phone:
                client_info += f"<b>Telefon:</b> {invoice.client_phone}<br/>"
            story.append(Paragraph(client_info, styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Validitate (pentru oferte)
            if invoice.is_quote and invoice.valid_until:
                validity_style = ParagraphStyle(
                    'Validity',
                    parent=styles['Normal'],
                    fontSize=14,
                    textColor=colors.red,
                    alignment=TA_CENTER,
                    borderWidth=2,
                    borderColor=colors.HexColor('#ffc107'),
                    borderPadding=10,
                    backColor=colors.HexColor('#fff3cd')
                )
                story.append(Paragraph(
                    f"<b>Ofertă valabilă până la: {invoice.valid_until.strftime('%d.%m.%Y')}</b>",
                    validity_style
                ))
                story.append(Spacer(1, 0.3 * inch))

            # Tabel produse - STRUCTURĂ NOUĂ
            story.append(Paragraph("PRODUSE", styles['SectionTitle']))

            # Header tabel - 6 coloane
            data = [['Nr.', 'Cod produs', 'Denumire produs', 'Cant.', 'Preț unit.\n(MDL)', 'Total\n(MDL)']]

            # Adaugă produse
            for idx, item in enumerate(items, 1):
                data.append([
                    str(idx),
                    item['sku'],
                    item['name'],
                    str(item['quantity']),
                    f"{item['unit_price']:,.0f}",
                    f"{item['subtotal']:,.0f}"
                ])

            # Crează tabel - colWidths ajustate pentru 6 coloane
            items_table = Table(
                data,
                colWidths=[
                    0.8 * cm,  # Nr.
                    2.5 * cm,  # Cod produs
                    7.7 * cm,  # Denumire produs (mai mult spațiu)
                    1.5 * cm,  # Cant.
                    2.5 * cm,  # Preț unit.
                    2.5 * cm  # Total
                ]
            )

            items_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                # Body
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Nr.
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Cod
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Denumire
                ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Cant.
                ('ALIGN', (4, 1), (5, -1), 'RIGHT'),  # Prețuri
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Roboto'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))

            story.append(items_table)
            story.append(Spacer(1, 0.3 * inch))

            # Totaluri - ajustăm colWidths pentru noua structură
            totals_data = [
                ['', '', '', '', 'Subtotal:', f"{(subtotal / 1.2):,.0f} MDL"],
                ['', '', '', '', 'TVA (20%):', f"{(subtotal - subtotal / 1.2):,.0f} MDL"],
                ['', '', '', '', 'TOTAL:', f"{total:,.0f} MDL"],
            ]

            totals_table = Table(
                totals_data,
                colWidths=[
                    0.8 * cm,  # Nr.
                    2.5 * cm,  # Cod produs
                    7.2 * cm,  # Denumire produs (redus)
                    1.5 * cm,  # Cant.
                    2.0 * cm,  # Label (redus)
                    3.5 * cm  # Valoare (mărit pentru sume mari)
                ]
            )

            totals_table.setStyle(TableStyle([
                ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
                ('FONTNAME', (4, 0), (5, -2), 'Roboto'),
                ('FONTNAME', (4, -1), (5, -1), 'Roboto-Bold'),
                ('FONTSIZE', (4, -1), (5, -1), 13),  # Redus din 14
                ('LINEABOVE', (4, -1), (5, -1), 2, colors.HexColor('#2c3e50')),
                ('LINEBELOW', (4, -1), (5, -1), 2, colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (5, -1), (5, -1), colors.HexColor('#27ae60')),
                ('RIGHTPADDING', (5, 0), (5, -1), 8),  # Adăugat padding dreapta
            ]))

            story.append(totals_table)

            # Note
            if invoice.notes:
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("OBSERVAȚII", styles['SectionTitle']))
                story.append(Paragraph(invoice.notes, styles['Normal']))

            # Footer
            story.append(Spacer(1, 0.5 * inch))
            footer_text = "Vă mulțumim pentru încrederea acordată!<br/>"
            footer_text += f"Document generat electronic la {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Paragraph(footer_text, footer_style))

            # Generează PDF cu numerotare pagini
            print("[PDFService] Building PDF document...")
            doc.build(story, onFirstPage=add_page_numbers, onLaterPages=add_page_numbers)
            print(f"[PDFService] PDF generated successfully at {output_path}")

            # Verifică că fișierul chiar există
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"[PDFService] PDF file created successfully:")
                print(f"  - Path: {output_path}")
                print(f"  - Size: {file_size} bytes")
                print(f"  - Exists: {output_path.exists()}")
            else:
                print(f"[PDFService] ERROR: PDF file was not created at {output_path}")
                raise Exception("PDF file was not created")

            # Returnează path-ul ca string
            result_path = str(output_path).replace('\\', '/')
            print(f"[PDFService] Returning path: {result_path}")
            print(f"{'=' * 60}\n")
            return result_path

        except Exception as e:
            print(f"\n[PDFService] ERROR generating PDF: {str(e)}")
            print(f"[PDFService] Error type: {type(e)}")
            print(f"[PDFService] Traceback: {traceback.format_exc()}")
            print(f"{'=' * 60}\n")

            # În loc să arunci excepția, returnează None
            return None

    @staticmethod
    def delete_invoice_pdf(document_path: str, cleanup_empty_dirs: bool = True) -> bool:
        """
        Șterge PDF-ul unei facturi și opțional curăță directoarele goale.

        Args:
            document_path: Calea către fișierul PDF
            cleanup_empty_dirs: Dacă să șteargă directoarele goale după ștergerea fișierului

        Returns:
            True dacă fișierul a fost șters cu succes, False altfel
        """
        try:
            if not document_path:
                print("[PDFService] No document path provided")
                return False

            pdf_file = Path(document_path)

            # Verifică dacă path-ul este absolut sau relativ
            if not pdf_file.is_absolute():
                pdf_file = Path.cwd() / pdf_file

            if pdf_file.exists():
                # Șterge fișierul
                pdf_file.unlink()
                print(f"[PDFService] PDF deleted: {pdf_file}")

                if cleanup_empty_dirs:
                    # Curăță directoarele goale (luna)
                    month_dir = pdf_file.parent
                    if month_dir.exists() and not any(month_dir.iterdir()):
                        month_dir.rmdir()
                        print(f"[PDFService] Empty month directory removed: {month_dir}")

                        # Curăță directorul anului dacă e gol
                        year_dir = month_dir.parent
                        if year_dir.exists() and not any(year_dir.iterdir()):
                            year_dir.rmdir()
                            print(f"[PDFService] Empty year directory removed: {year_dir}")

                return True
            else:
                print(f"[PDFService] PDF file not found: {pdf_file}")
                return False

        except Exception as e:
            print(f"[PDFService] Error deleting PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Adaugă această funcție temporar pentru debug
    @staticmethod
    def debug_fonts():
        """Verifică ce fonturi sunt disponibile."""
        from reportlab.pdfbase import pdfmetrics

        print("\n[PDFService] Checking fonts...")
        font_dir = Path("server/dashboard/static/fonts")
        print(f"Font directory: {font_dir.absolute()}")
        print(f"Directory exists: {font_dir.exists()}")

        if font_dir.exists():
            print("Files in font directory:")
            for file in font_dir.iterdir():
                print(f"  - {file.name}")

        print("\nRegistered fonts in ReportLab:")
        for font in pdfmetrics.getRegisteredFontNames():
            print(f"  - {font}")
        print("\n")