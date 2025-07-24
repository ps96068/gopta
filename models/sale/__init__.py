# models/sale/__init__.py
"""
Sale module pentru PCE-start Foundation.

Acest modul conține toate modelele legate de vânzări:
- Order: Comenzi plasate de clienți (B2C/B2B)
- OrderItem: Produsele din comandă cu prețuri snapshot
- Invoice: Chitanțe generate automat pentru comenzi

În PCE-start (MVP), toate comenzile aparțin System Vendor (vendor_id=1).
În multi-vendor, fiecare OrderItem poate avea vendor și status propriu.
"""

from models.sale.order import Order
from models.sale.order_item import OrderItem
from models.sale.cart import Cart
from models.sale.cart_item import CartItem
from models.sale.invoice import Invoice




__all__ = [
    # Order
    'Order',
    'OrderItem',


    # Cart
    'Cart',
    'CartItem',


    # Invoice
    'Invoice',
]