# models/user/__init__.py
"""
User module pentru PCE-start Foundation.

Acest modul conține toate modelele legate de utilizatori:
- Client: Utilizatori WebApp (B2C/B2B)
- ClientCompany: Companii client pentru achiziții B2B
- Staff: Utilizatori Dashboard cu roluri administrative
- Vendor: Utilizatori vendor (pregătit pentru multi-vendor)
- VendorCompany: Companii vendor care dețin produse

În PCE-start (MVP), sistemul operează cu un singur vendor implicit (PCE Default).
"""

from models.user.client import Client
from models.user.staff import Staff
from models.user.vendor import Vendor  # Temporar, va fi înlocuit cu VendorCompany și VendorStaff
from models.user.vendor_company import VendorCompany
from models.user.vendor_staff import VendorStaff


__all__ = [
    # Client models
    'Client',

    # Staff models
    'Staff',

    # Vendor models (prepared for multi-vendor)
    'VendorCompany',
    'VendorStaff',
    'Vendor',
]