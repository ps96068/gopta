
_catalog_listeners_registered = False


def register_all_catalog_listeners():

    global _catalog_listeners_registered

    # Verificăm dacă listener-ii au fost deja înregistrați
    if _catalog_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Catalog sunt deja înregistrați. Se sare reînregistrarea.")
        return True

    # Importă modulele listener-ilor pentru a-i înregistra
    from . import category_signals
    from . import product_signals
    from . import product_image_signals
    from . import product_price_signals
    from . import product_price_history_signals

    # Marchează listener-ii ca fiind înregistrați
    _catalog_listeners_registered = True
    print("Listener-ii SQLAlchemy pentru Catalog au fost înregistrați cu succes.")
    return True

def disable_all_catalog_listeners():

    global _catalog_listeners_registered

    if not _catalog_listeners_registered:
        print("Listener-ii nu sunt înregistrați. Nimic de dezactivat.")
        return False

    from sqlalchemy import event
    from models.catalog import (Category, Product, ProductImage,
                                ProductPrice, ProductPriceHistory, PriceType)
    from .category_signals import  (set_default_image_if_missing,
                                    handle_image_update,
                                    delete_category_image)
    # from .product_signals import *
    from .product_image_signals import enforce_single_primary
    from .product_price_signals import log_price_change
    # from .product_price_history_signals import *

    # Eliminăm toți listener-ii pentru Post



    # Disable all signals for Category
    event.remove(Category, "before_insert", set_default_image_if_missing)
    event.remove(Category, "before_update", handle_image_update)
    event.remove(Category, "after_delete", delete_category_image)


    # Disable all signals for Product

    # Disable all signals for ProductImage
    event.remove(ProductImage, "before_insert", enforce_single_primary)
    event.remove(ProductImage, "before_update", enforce_single_primary)

    # Disable all signals for ProductPrice
    event.remove(ProductPrice, "after_insert", log_price_change)
    event.remove(ProductPrice, "after_update", log_price_change)

    # Disable all signals for ProductPriceHistory


    _catalog_listeners_registered = False
    print("Listener-ii SQLAlchemy pentru Catalog au fost dezactivați.")
    return True

def enable_all_catalog_listeners():

    global _catalog_listeners_registered

    if _catalog_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Catalog sunt deja activi. Se sare reactivarea.")
        return False

    # Reînregistrăm toți listener-ii pentru Catalog
    return register_all_catalog_listeners()

def get_catalog_listeners_status():

    return {
        "registered": _catalog_listeners_registered,
        "status": "active" if _catalog_listeners_registered else "inactive"
    }




# Integram automat listener-ii la importul pachetului
register_all_catalog_listeners()

# Exportă funcțiile publice
__all__ = [
    'register_all_catalog_listeners',
    'disable_all_catalog_listeners',
    'enable_all_catalog_listeners',
    'get_catalog_listeners_status',
]