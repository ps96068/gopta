# models/enum/invoice.py

import enum


class InvoiceType(str, enum.Enum):
    """Tipuri de invoice."""
    QUOTE = "quote"      # Ofertă din Cart
    INVOICE = "invoice"  # Factură din Order