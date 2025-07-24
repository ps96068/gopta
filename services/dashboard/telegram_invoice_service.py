# services/dashboard/telegram_invoice_service.py
"""
Extensie pentru TelegramService - funcționalități Invoice.
"""

from __future__ import annotations
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from models import Invoice, InvoiceType, Client

from typing import Optional
import logging

logger = logging.getLogger(__name__)



#
# class TelegramInvoiceService:
#     """Service pentru trimitere Invoice prin Telegram."""
#
#     def __init__(self, bot: Bot):
#         self.bot = bot
#
#     async def send_invoice_document(
#             self,
#             invoice: Invoice,
#             pdf_path: str,
#             telegram_id: int,
#             client_name: Optional[str] = None
#     ) -> bool:
#         """
#         Trimite PDF prin Telegram.
#
#         Args:
#             invoice: Invoice object
#             pdf_path: Path către PDF
#             telegram_id: Telegram ID destinatar
#             client_name: Nume client pentru mesaj
#
#         Returns:
#             True dacă s-a trimis cu succes
#         """
#         try:
#             # Verifică că fișierul există
#             if not Path(pdf_path).exists():
#                 print(f"PDF file not found: {pdf_path}")
#                 return False
#
#             # Pregătește mesajul
#             if invoice.is_quote:
#                 message = f"""
# 🎯 *Ofertă PCE*
#
# Bună ziua{' ' + client_name if client_name else ''}!
#
# Vă trimitem oferta solicitată:
# 📄 *{invoice.invoice_number}*
#
# 💰 *Total:* {float(invoice.total_amount):,.0f} MDL
# 📅 *Valabilă până:* {invoice.valid_until.strftime('%d.%m.%Y') if invoice.valid_until else 'N/A'}
#
# Pentru a transforma oferta în comandă, răspundeți la acest mesaj sau contactați-ne.
#
# 📞 Tel: +373 22 123 456
# 💬 Telegram: @pce_support
# """
#             else:  # Invoice
#                 message = f"""
# 🧾 *Factură PCE*
#
# Bună ziua{' ' + client_name if client_name else ''}!
#
# Vă trimitem factura pentru comanda dumneavoastră:
# 📄 *{invoice.invoice_number}*
#
# 💰 *Total:* {float(invoice.total_amount):,.0f} MDL
# 📅 *Data:* {invoice.created_at.strftime('%d.%m.%Y')}
#
# Vă mulțumim pentru încredere!
#
# Pentru întrebări:
# 📞 Tel: +373 22 123 456
# 💬 Telegram: @pce_support
# """
#
#             # Trimite documentul
#             document = FSInputFile(pdf_path)
#             await self.bot.send_document(
#                 chat_id=telegram_id,
#                 document=document,
#                 caption=message,
#                 parse_mode="Markdown"
#             )
#
#             return True
#
#         except Exception as e:
#             print(f"Error sending Telegram document: {e}")
#             return False
#
#     async def send_quote_with_actions(
#             self,
#             invoice: Invoice,
#             pdf_path: str,
#             telegram_id: int,
#             client_name: Optional[str] = None
#     ) -> bool:
#         """
#         Trimite ofertă cu butoane de acțiune.
#
#         Args:
#             invoice: Invoice object (tip quote)
#             pdf_path: Path către PDF
#             telegram_id: Telegram ID destinatar
#             client_name: Nume client
#
#         Returns:
#             True dacă s-a trimis cu succes
#         """
#         try:
#             if invoice.invoice_type != InvoiceType.QUOTE:
#                 raise ValueError("This method is only for quotes")
#
#             # Keyboard cu acțiuni
#             keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                 [
#                     InlineKeyboardButton(
#                         text="✅ Accept oferta",
#                         callback_data=f"quote_accept_{invoice.id}"
#                     ),
#                     InlineKeyboardButton(
#                         text="❌ Refuz oferta",
#                         callback_data=f"quote_reject_{invoice.id}"
#                     )
#                 ],
#                 [
#                     InlineKeyboardButton(
#                         text="💬 Am întrebări",
#                         callback_data=f"quote_question_{invoice.id}"
#                     )
#                 ]
#             ])
#
#             # Mesaj
#             message = f"""
# 🎯 *Ofertă Specială PCE*
#
# Bună ziua{' ' + client_name if client_name else ''}!
#
# V-am pregătit o ofertă personalizată:
#
# 📄 *Ofertă:* {invoice.invoice_number}
# 💰 *Valoare:* {float(invoice.total_amount):,.0f} MDL (TVA inclus)
# 📅 *Valabilă până:* {invoice.valid_until.strftime('%d.%m.%Y') if invoice.valid_until else 'N/A'}
#
# {f'📝 *Note:* {invoice.notes}' if invoice.notes else ''}
#
# Detaliile complete le găsiți în documentul atașat.
#
# *Ce doriți să faceți cu această ofertă?*
# """
#
#             # Trimite cu document și butoane
#             document = FSInputFile(pdf_path)
#             await self.bot.send_document(
#                 chat_id=telegram_id,
#                 document=document,
#                 caption=message,
#                 parse_mode="Markdown",
#                 reply_markup=keyboard
#             )
#
#             return True
#
#         except Exception as e:
#             print(f"Error sending quote with actions: {e}")
#             return False
#
#     async def send_invoice_reminder(
#             self,
#             invoice: Invoice,
#             telegram_id: int,
#             client_name: Optional[str] = None,
#             days_until_expire: Optional[int] = None
#     ) -> bool:
#         """
#         Trimite reminder pentru oferte care expiră curând.
#
#         Args:
#             invoice: Invoice object
#             telegram_id: Telegram ID
#             client_name: Nume client
#             days_until_expire: Zile până la expirare
#
#         Returns:
#             True dacă s-a trimis cu succes
#         """
#         try:
#             message = f"""
# ⏰ *Reminder: Ofertă care expiră curând*
#
# Bună ziua{' ' + client_name if client_name else ''}!
#
# Vă reamintim că oferta noastră:
# 📄 *{invoice.invoice_number}*
# 💰 *Valoare:* {float(invoice.total_amount):,.0f} MDL
#
# {f'⚠️ *Expiră în {days_until_expire} {"zi" if days_until_expire == 1 else "zile"}!*' if days_until_expire else ''}
#
# Nu ratați această oportunitate!
# Pentru a comanda, contactați-ne urgent:
#
# 📞 Tel: +373 22 123 456
# 💬 Telegram: @pce_support
# """
#
#             # Keyboard pentru acțiune rapidă
#             keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                 [
#                     InlineKeyboardButton(
#                         text="🛒 Transform în comandă",
#                         callback_data=f"quote_convert_{invoice.id}"
#                     )
#                 ],
#                 [
#                     InlineKeyboardButton(
#                         text="💬 Contact rapid",
#                         url="https://t.me/pce_support"
#                     )
#                 ]
#             ])
#
#             await self.bot.send_message(
#                 chat_id=telegram_id,
#                 text=message,
#                 parse_mode="Markdown",
#                 reply_markup=keyboard
#             )
#
#             return True
#
#         except Exception as e:
#             print(f"Error sending reminder: {e}")
#             return False
#
#     async def handle_quote_callback(
#             self,
#             callback_data: str,
#             telegram_id: int,
#             db: AsyncSession
#     ) -> str:
#         """
#         Procesează callback-uri pentru oferte.
#
#         Args:
#             callback_data: String callback de la buton
#             telegram_id: ID Telegram user
#             db: Database session
#
#         Returns:
#             Mesaj de răspuns
#         """
#         parts = callback_data.split('_')
#         if len(parts) < 3:
#             return "❌ Comandă invalidă"
#
#         action = parts[1]
#         invoice_id = int(parts[2])
#
#         # Obține invoice
#         from sqlalchemy import select
#         result = await db.execute(
#             select(Invoice).where(Invoice.id == invoice_id)
#         )
#         invoice = result.scalar_one_or_none()
#
#         if not invoice:
#             return "❌ Oferta nu a fost găsită"
#
#         # Procesează acțiunea
#         if action == "accept":
#             # TODO: Creează comandă din ofertă
#             return f"""
# ✅ *Excelent!*
#
# Am înregistrat acceptul dumneavoastră pentru oferta {invoice.invoice_number}.
#
# Un reprezentant vă va contacta în curând pentru finalizarea comenzii.
#
# Vă mulțumim pentru încredere! 🎉
# """
#
#         elif action == "reject":
#             return f"""
# 😔 *Ne pare rău că oferta nu v-a convenit*
#
# Dacă doriți o ofertă personalizată sau aveți alte cerințe, nu ezitați să ne contactați:
#
# 💬 @pce_support
# 📞 +373 22 123 456
#
# Vă stăm la dispoziție!
# """
#
#         elif action == "question":
#             return f"""
# 💬 *Aveți întrebări despre oferta {invoice.invoice_number}?*
#
# Contactați-ne direct:
# 👤 Manager vânzări: @pce_sales
# 📞 Tel: +373 22 123 456
#
# Sau scrieți întrebarea dvs. ca răspuns la acest mesaj și vă vom răspunde cât mai curând!
# """
#
#         elif action == "convert":
#             # TODO: Implementare conversie directă
#             return f"""
# 🛒 *Conversie rapidă în comandă*
#
# Pentru a transforma oferta {invoice.invoice_number} în comandă, contactați:
#
# 👤 @pce_sales
# 📞 +373 22 123 456
#
# Menționați numărul ofertei pentru procesare rapidă!
# """
#
#         return "❌ Acțiune necunoscută"
#


class TelegramInvoiceService:
    """Service pentru trimitere documente prin Telegram."""

    def __init__(self, bot):
        self.bot = bot

    async def send_quote_with_actions(
            self,
            invoice,
            pdf_path: str,
            telegram_id: int,
            recipient_name: str
    ) -> bool:
        """
        Trimite ofertă cu butoane de acțiune.
        În development doar logăm.
        """
        logger.info(f"[TelegramService] Would send quote to Telegram ID {telegram_id}")
        logger.info(f"[TelegramService] Invoice: {invoice.invoice_number}")
        logger.info(f"[TelegramService] PDF: {pdf_path}")
        logger.info(f"[TelegramService] Recipient: {recipient_name}")

        # În development returnăm success
        return True

    async def send_invoice_document(
            self,
            invoice,
            pdf_path: str,
            telegram_id: int,
            recipient_name: str
    ) -> bool:
        """
        Trimite factură prin Telegram.
        În development doar logăm.
        """
        logger.info(f"[TelegramService] Would send invoice to Telegram ID {telegram_id}")
        logger.info(f"[TelegramService] Invoice: {invoice.invoice_number}")
        logger.info(f"[TelegramService] PDF: {pdf_path}")
        logger.info(f"[TelegramService] Recipient: {recipient_name}")

        # În development returnăm success
        return True


