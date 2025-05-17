
_blog_listeners_registered = False


def register_all_blog_listeners():

    global _blog_listeners_registered

    # Verificăm dacă listener-ii au fost deja înregistrați
    if _blog_listeners_registered:
        print("Listener-ii SQLAlchemy pentru Blog sunt deja inregistrați. Se sare re-inregistrarea.")
        return True

    # Importă modulele listener-ilor pentru a-i înregistra
    from . import post_signals
    from . import post_image_signals
    from . import post_edit_history_signals

    # Marchează listener-ii ca fiind înregistrați
    _blog_listeners_registered = True
    print("Listener-ii SQLAlchemy pentru Blog au fost inregistrati cu succes.")
    return True

def disable_all_blog_listeners():

    global _blog_listeners_registered

    if not _blog_listeners_registered:
        print("Listener-ii nu sunt înregistrați. Nimic de dezactivat.")
        return False

    from sqlalchemy import event
    from models.blog import Post, PostImage, PostEditHistory

    # from .post_signals import *
    from .post_image_signals import (ensure_single_primary,
                                     set_default_image_if_missing,
                                     delete_image_file)
    from .post_edit_history_signals import add_edit_history



    # Eliminăm toți listener-ii pentru Post


    # Disable all signals for PostImage
    event.remove(PostImage, "before_insert", ensure_single_primary)
    event.remove(PostImage, "before_update", ensure_single_primary)

    event.remove(PostImage, "before_insert", set_default_image_if_missing)
    event.remove(PostImage, "before_update", set_default_image_if_missing)

    event.remove(PostImage, "after_delete", delete_image_file)

    # Disable all signals for PostEditHistory
    event.remove(Post, "before_update", add_edit_history)


    _blog_listeners_registered = False
    print("Listener-ii SQLAlchemy au fost dezactivați.")
    return True

def enable_all_blog_listeners():

    global _blog_listeners_registered

    if _blog_listeners_registered:
        print("Listener-ii SQLAlchemy sunt deja activi. Se sare reactivarea.")
        return False

    # Reînregistrăm toți listener-ii pentru Blog
    return register_all_blog_listeners()

def get_blog_listeners_status():

    return {
        "registered": _blog_listeners_registered,
        "status": "active" if _blog_listeners_registered else "inactive"
    }






# Integram automat listener-ii la importul pachetului
register_all_blog_listeners()

# Exportă funcțiile publice
__all__ = [
    'register_all_blog_listeners',
    'disable_all_blog_listeners',
    'enable_all_blog_listeners',
    'get_blog_listeners_status'
]