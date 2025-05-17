
_marketing_listeners_registered = False




def register_all_marketing_listeners():

    global _marketing_listeners_registered

    # Verificăm dacă listener-ii au fost deja înregistrați
    if _marketing_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Marketing sunt deja înregistrați. Se sare reînregistrarea.")
        return True

    # Importă modulele listener-ilor pentru a-i înregistra
    from . import user_activity_signals
    from . import user_interaction_signals
    from . import user_request_signals


    # Marchează listener-ii ca fiind înregistrați
    _marketing_listeners_registered = True
    print("Listener-ii SQLAlchemy pentru Marketing au fost înregistrați cu succes.")
    return True

def disable_all_marketing_listeners():

    global _marketing_listeners_registered

    if not _marketing_listeners_registered:
        print("Marketing Listener-ii nu sunt înregistrați. Nimic de dezactivat.")
        return False

    from sqlalchemy import event
    from models.marketing import (UserRequest, UserActivity, UserInteraction,)

    # from .user_request_signals import  *
    # from .user_activity_signals import *
    # from .user_interaction_signals import *



    # Eliminăm toți listener-ii pentru UserRequest


    # Disable all signals for UserActivity


    # Disable all signals for UserInteraction




    _marketing_listeners_registered = False
    print("Listener-ii SQLAlchemy pentru Marketing au fost dezactivați.")
    return True


def enable_all_marketing_listeners():

    global _marketing_listeners_registered

    if _marketing_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Marketing sunt deja activi. Se sare reactivarea.")
        return False

    # Reînregistrăm toți listener-ii pentru Catalog
    return register_all_marketing_listeners()

def get_marketing_listeners_status():

    return {
        "registered": _marketing_listeners_registered,
        "status": "active" if _marketing_listeners_registered else "inactive"
    }




# Integram automat listener-ii la importul pachetului
register_all_marketing_listeners()

# Exportă funcțiile publice
__all__ = [
    'register_all_marketing_listeners',
    'disable_all_marketing_listeners',
    'enable_all_marketing_listeners',
    'get_marketing_listeners_status',
]