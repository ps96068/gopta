# services/dashboard/email_service.py
"""
Service pentru trimitere email-uri folosind SendGrid.
"""

from __future__ import annotations
import os
import base64
from typing import Optional, List, Dict
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)

from models import Invoice, InvoiceType


from typing import Optional
import logging

logger = logging.getLogger(__name__)



#
# class EmailService:
#     """Service pentru gestionarea email-urilor."""
#
#     # Configurare SendGrid
#     SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "your-api-key-here")
#     FROM_EMAIL = "noreply@pce.md"
#     FROM_NAME = "PCE Distribution"
#
#     # Template IDs în SendGrid (opțional)
#     TEMPLATE_QUOTE = None  # Poate fi setat dacă folosiți template-uri SendGrid
#     TEMPLATE_INVOICE = None
#
#     @staticmethod
#     def _get_client() -> SendGridAPIClient:
#         """Obține client SendGrid."""
#         return SendGridAPIClient(EmailService.SENDGRID_API_KEY)
#
#     @staticmethod
#     def _attach_pdf(message: Mail, pdf_path: str, filename: str) -> None:
#         """Atașează PDF la email."""
#         with open(pdf_path, 'rb') as f:
#             data = f.read()
#             encoded = base64.b64encode(data).decode()
#
#         attachment = Attachment()
#         attachment.file_content = FileContent(encoded)
#         attachment.file_type = FileType('application/pdf')
#         attachment.file_name = FileName(filename)
#         attachment.disposition = Disposition('attachment')
#
#         message.attachment = attachment
#
#     @staticmethod
#     def _get_email_content(invoice_type: InvoiceType) -> Dict[str, str]:
#         """Returnează template-uri email pentru fiecare tip."""
#         if invoice_type == InvoiceType.QUOTE:
#             return {
#                 'subject': 'Oferta PCE #{invoice_number}',
#                 'html': """
#                 <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#                     <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
#                         <h1 style="color: #333; margin: 0;">PCE Distribution</h1>
#                     </div>
#
#                     <div style="padding: 30px;">
#                         <h2 style="color: #333;">Bună ziua {client_name},</h2>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Vă mulțumim pentru interesul acordat produselor noastre!
#                         </p>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Atașat găsiți oferta solicitată <strong>#{invoice_number}</strong>,
#                             valabilă până la <strong>{valid_until}</strong>.
#                         </p>
#
#                         <div style="background-color: #e9ecef; padding: 20px; margin: 20px 0; border-radius: 5px;">
#                             <h3 style="margin: 0 0 10px 0; color: #333;">Detalii ofertă:</h3>
#                             <p style="margin: 5px 0;"><strong>Număr produse:</strong> {items_count}</p>
#                             <p style="margin: 5px 0;"><strong>Valoare totală:</strong> {total_amount} MDL (TVA inclus)</p>
#                         </div>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Pentru a transforma această ofertă în comandă, vă rugăm să ne contactați:
#                         </p>
#
#                         <ul style="font-size: 16px; line-height: 1.8;">
#                             <li>Telefon: +373 22 123 456</li>
#                             <li>Email: vanzari@pce.md</li>
#                             <li>Telegram: @pce_bot</li>
#                         </ul>
#
#                         <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
#
#                         <p style="font-size: 14px; color: #666;">
#                             Cu stimă,<br>
#                             Echipa PCE Distribution
#                         </p>
#                     </div>
#
#                     <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
#                         <p style="margin: 5px 0;">PCE Distribution SRL | str. Mihai Eminescu 47, Chișinău</p>
#                         <p style="margin: 5px 0;">© 2024 Toate drepturile rezervate</p>
#                     </div>
#                 </div>
#                 """,
#                 'text': """
# Bună ziua {client_name},
#
# Vă mulțumim pentru interesul acordat produselor noastre!
#
# Atașat găsiți oferta solicitată #{invoice_number}, valabilă până la {valid_until}.
#
# Detalii ofertă:
# - Număr produse: {items_count}
# - Valoare totală: {total_amount} MDL (TVA inclus)
#
# Pentru a transforma această ofertă în comandă, vă rugăm să ne contactați:
# - Telefon: +373 22 123 456
# - Email: vanzari@pce.md
# - Telegram: @pce_bot
#
# Cu stimă,
# Echipa PCE Distribution
#                 """
#             }
#         else:  # INVOICE
#             return {
#                 'subject': 'Factură PCE #{invoice_number}',
#                 'html': """
#                 <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
#                     <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
#                         <h1 style="color: #333; margin: 0;">PCE Distribution</h1>
#                     </div>
#
#                     <div style="padding: 30px;">
#                         <h2 style="color: #333;">Bună ziua {client_name},</h2>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Vă mulțumim pentru comanda dumneavoastră!
#                         </p>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Atașat găsiți factura <strong>#{invoice_number}</strong> pentru comanda dumneavoastră.
#                         </p>
#
#                         <div style="background-color: #e9ecef; padding: 20px; margin: 20px 0; border-radius: 5px;">
#                             <h3 style="margin: 0 0 10px 0; color: #333;">Detalii factură:</h3>
#                             <p style="margin: 5px 0;"><strong>Număr comandă:</strong> {order_number}</p>
#                             <p style="margin: 5px 0;"><strong>Data:</strong> {invoice_date}</p>
#                             <p style="margin: 5px 0;"><strong>Valoare totală:</strong> {total_amount} MDL (TVA inclus)</p>
#                         </div>
#
#                         <p style="font-size: 16px; line-height: 1.6;">
#                             Pentru orice întrebări sau nelămuriri, nu ezitați să ne contactați.
#                         </p>
#
#                         <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
#
#                         <p style="font-size: 14px; color: #666;">
#                             Cu stimă,<br>
#                             Echipa PCE Distribution
#                         </p>
#                     </div>
#
#                     <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
#                         <p style="margin: 5px 0;">PCE Distribution SRL | str. Mihai Eminescu 47, Chișinău</p>
#                         <p style="margin: 5px 0;">© 2024 Toate drepturile rezervate</p>
#                     </div>
#                 </div>
#                 """,
#                 'text': """
# Bună ziua {client_name},
#
# Vă mulțumim pentru comanda dumneavoastră!
#
# Atașat găsiți factura #{invoice_number} pentru comanda dumneavoastră.
#
# Detalii factură:
# - Număr comandă: {order_number}
# - Data: {invoice_date}
# - Valoare totală: {total_amount} MDL (TVA inclus)
#
# Pentru orice întrebări sau nelămuriri, nu ezitați să ne contactați.
#
# Cu stimă,
# Echipa PCE Distribution
#                 """
#             }
#
#     @staticmethod
#     async def send_invoice_email(
#             invoice: Invoice,
#             pdf_path: str,
#             recipient_email: str,
#             recipient_name: Optional[str] = None
#     ) -> bool:
#         """
#         Trimite email cu PDF atașat.
#
#         Args:
#             invoice: Invoice object
#             pdf_path: Path către PDF
#             recipient_email: Email destinatar
#             recipient_name: Nume destinatar
#
#         Returns:
#             True dacă s-a trimis cu succes
#         """
#         try:
#             # Pregătește datele pentru template
#             template_data = {
#                 'client_name': recipient_name or invoice.client_name,
#                 'invoice_number': invoice.invoice_number,
#                 'total_amount': f"{float(invoice.total_amount):,.0f}",
#                 'items_count': 0,  # Va fi calculat din invoice
#             }
#
#             # Date specifice pentru tip
#             if invoice.is_quote:
#                 template_data['valid_until'] = invoice.valid_until.strftime("%d.%m.%Y") if invoice.valid_until else ""
#             else:
#                 template_data['order_number'] = invoice.order.order_number if invoice.order else ""
#                 template_data['invoice_date'] = invoice.created_at.strftime("%d.%m.%Y")
#
#             # Obține template
#             content = EmailService._get_email_content(invoice.invoice_type)
#
#             # Creează mesajul
#             message = Mail(
#                 from_email=(EmailService.FROM_EMAIL, EmailService.FROM_NAME),
#                 to_emails=recipient_email,
#                 subject=content['subject'].format(**template_data),
#                 html_content=content['html'].format(**template_data),
#                 plain_text_content=content['text'].format(**template_data)
#             )
#
#             # Atașează PDF
#             if pdf_path and Path(pdf_path).exists():
#                 EmailService._attach_pdf(
#                     message,
#                     pdf_path,
#                     f"{invoice.invoice_number}.pdf"
#                 )
#
#             # Trimite email
#             sg = EmailService._get_client()
#             response = sg.send(message)
#
#             # Verifică răspuns
#             return response.status_code in [200, 201, 202]
#
#         except Exception as e:
#             print(f"Error sending email: {e}")
#             return False
#
#     @staticmethod
#     async def send_bulk_emails(
#             invoice: Invoice,
#             pdf_path: str,
#             recipients: List[Dict[str, str]]
#     ) -> Dict[str, bool]:
#         """
#         Trimite email la mai mulți destinatari.
#
#         Args:
#             invoice: Invoice object
#             pdf_path: Path către PDF
#             recipients: Listă de dict cu 'email' și 'name'
#
#         Returns:
#             Dict cu rezultate pentru fiecare email
#         """
#         results = {}
#
#         for recipient in recipients:
#             email = recipient.get('email')
#             name = recipient.get('name')
#
#             if email:
#                 success = await EmailService.send_invoice_email(
#                     invoice, pdf_path, email, name
#                 )
#                 results[email] = success
#
#         return results


class EmailService:
    """Service pentru trimitere email-uri."""

    @staticmethod
    async def send_invoice_email(
            invoice,
            pdf_path: str,
            recipient_email: str,
            recipient_name: str
    ) -> bool:
        """
        Trimite invoice prin email.
        În development doar logăm.
        """
        logger.info(f"[EmailService] Would send email to {recipient_email}")
        logger.info(f"[EmailService] Invoice: {invoice.invoice_number}")
        logger.info(f"[EmailService] PDF: {pdf_path}")
        logger.info(f"[EmailService] Recipient: {recipient_name}")

        # În development returnăm success
        return True