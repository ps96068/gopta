# models/enum/vendor.py


from __future__ import annotations
import enum




class VendorRole(str, enum.Enum):
    """Roluri pentru vendor staff."""
    ADMIN = "admin"      # Toate permisiunile inclusiv setări companie
    MANAGER = "manager"  # Doar gestionare produse și comenzi