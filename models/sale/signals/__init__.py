
_sale_listeners_registered = False




def register_all_sale_listeners():

    global _sale_listeners_registered

    # Verificăm dacă listener-ii au fost deja înregistrați
    if _sale_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Sale sunt deja înregistrați. Se sare reînregistrarea.")
        return True

    # Importă modulele listener-ilor pentru a-i înregistra
    from . import order_signals
    from . import order_item_signals
    from . import order_status_history_signals


    # Marchează listener-ii ca fiind înregistrați
    _sale_listeners_registered = True
    print("Listener-ii SQLAlchemy pentru Sale au fost înregistrați cu succes.")
    return True

def disable_all_sale_listeners():

    global _sale_listeners_registered

    if not _sale_listeners_registered:
        print("Sale Listener-ii nu sunt înregistrați. Nimic de dezactivat.")
        return False

    from sqlalchemy import event
    from models.sale import (Order, OrderItem, OrderStatusHistory)
    # from .order_signals import  *
    # from .order_item_signals import *
    # from .order_status_history_signals import *


    # Eliminăm toți listener-ii pentru Order


    # Disable all signals for OrderItem
    # event.remove(Category, "before_insert", set_default_image_if_missing)


    # Disable all signals for OrderStatusHistory




    _sale_listeners_registered = False
    print("Listener-ii SQLAlchemy pentru Sale au fost dezactivați.")
    return True


def enable_all_sale_listeners():

    global _sale_listeners_registered

    if _sale_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Sale sunt deja activi. Se sare reactivarea.")
        return False

    # Reînregistrăm toți listener-ii pentru Catalog
    return register_all_sale_listeners()

def get_sale_listeners_status():

    return {
        "registered": _sale_listeners_registered,
        "status": "active" if _sale_listeners_registered else "inactive"
    }




# Integram automat listener-ii la importul pachetului
register_all_sale_listeners()

# Exportă funcțiile publice
__all__ = [
    'register_all_sale_listeners',
    'disable_all_sale_listeners',
    'enable_all_sale_listeners',
    'get_sale_listeners_status'
]
