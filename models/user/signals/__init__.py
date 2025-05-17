
_user_listeners_registered = False



def register_all_user_listeners():

    global _user_listeners_registered

    # Verificăm dacă listener-ii au fost deja înregistrați
    if _user_listeners_registered:
        print("Listener-ii SQLAlchemy pentru User sunt deja înregistrați. Se sare reînregistrarea.")
        return True

    # Importă modulele listener-ilor pentru a-i înregistra
    from . import client_signals
    from . import staff_signals

    # Marchează listener-ii ca fiind înregistrați
    _user_listeners_registered = True
    print("Listener-ii SQLAlchemy pentru User au fost înregistrați cu succes.")
    return True

def disable_all_user_listeners():

    global _user_listeners_registered

    if not _user_listeners_registered:
        print("User Listener-ii nu sunt înregistrați. Nimic de dezactivat.")
        return False

    from sqlalchemy import event
    from models.user import (Client, Staff)
    # from .client_signals import  *
    # from .staff_signals import *


    # Eliminăm toți listener-ii pentru Client



    # Disable all signals for Staff



    _user_listeners_registered = False
    print("Listener-ii SQLAlchemy pentru User au fost dezactivați.")
    return True


def enable_all_user_listeners():

    global _user_listeners_registered

    if _user_listeners_registered:
        print("Listener-ii SQLAlchemy pentru User sunt deja activi. Se sare reactivarea.")
        return False

    # Reînregistrăm toți listener-ii pentru User
    return register_all_user_listeners()

def get_user_listeners_status():

    return {
        "registered": _user_listeners_registered,
        "status": "active" if _user_listeners_registered else "inactive"
    }




# Integram automat listener-ii la importul pachetului
register_all_user_listeners()

# Exportă funcțiile publice
__all__ = [
    'register_all_user_listeners',
    'disable_all_user_listeners',
    'enable_all_user_listeners',
    'get_user_listeners_status'
]
