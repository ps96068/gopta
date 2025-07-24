# models/enum/product_price.py

from __future__ import annotations
import enum





class PriceType(enum.Enum):
    """Tipuri de preț disponibile pentru clienți."""
    ANONIM = "anonim"
    USER = "user"
    INSTALATOR = "instalator"
    PRO = "pro"