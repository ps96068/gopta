# models/catalog/__init__.py
"""
Catalog module pentru PCE-start Foundation.

Acest modul conține toate modelele legate de catalogul de produse:
- Category: Categorii globale de produse
- Product: Produse aparținând vendorilor
- ProductImage: Imagini produse (max 4 per produs)
- ProductPrice: Prețuri pe 4 nivele (anonim, user, instalator, pro)

În PCE-start (MVP), toate produsele aparțin System Vendor (id=1).
Categoriile sunt globale și pot fi create doar de Staff.
"""

from .category import Category
from .product import Product
from .product_image import ProductImage
from .product_price import ProductPrice

__all__ = [
    'Category',
    'Product',
    'ProductImage',
    'ProductPrice',
]