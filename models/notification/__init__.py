# models/notification/__init__.py
"""
Notification module pentru PCE-start Foundation.

Acest modul conține modelul pentru sistemul de notificări:
- Notification: Notificări trimise către clienți prin Telegram și Email

Sistemul suportă multiple tipuri de notificări (order, blog, product, system, marketing)
cu template-uri predefinite, variabile dinamice și rate limiting.

Clienții pot dezactiva anumite tipuri de notificări și sistemul respectă
limita de 10 notificări/zi distribuite între 8:00-19:00.
"""

from .notification import Notification

__all__ = [
    'Notification',
]