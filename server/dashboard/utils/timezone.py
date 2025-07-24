# server/dashboard/utils/timezone.py
"""
Timezone utilities pentru Dashboard.
Ajută la conversia corectă între UTC și timezone local.
"""

from datetime import datetime, timezone
import pytz
from typing import Optional


def get_local_timezone():
    """
    Returnează timezone-ul local configurat pentru aplicație.
    În Moldova este EET/EEST (UTC+2/+3)
    """
    return pytz.timezone('Europe/Chisinau')


def utc_to_local(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convertește datetime din UTC în timezone local.
    """
    if not dt:
        return None

    if dt.tzinfo is None:
        # Dacă nu are timezone, presupunem că e UTC
        dt = pytz.utc.localize(dt)

    local_tz = get_local_timezone()
    return dt.astimezone(local_tz)


def local_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convertește datetime din timezone local în UTC.
    """
    if not dt:
        return None

    local_tz = get_local_timezone()

    if dt.tzinfo is None:
        # Dacă nu are timezone, presupunem că e local
        dt = local_tz.localize(dt)

    return dt.astimezone(pytz.utc)


def datetime_local(dt: Optional[datetime], format: str = "%d.%m.%Y %H:%M") -> str:
    """
    Filter Jinja2 pentru afișarea datetime în timezone local.
    """
    if not dt:
        return ""

    local_dt = utc_to_local(dt)
    return local_dt.strftime(format) if local_dt else ""


def date_only(dt: Optional[datetime], format: str = "%d.%m.%Y") -> str:
    """
    Filter Jinja2 pentru afișarea doar a datei în timezone local.
    """
    if not dt:
        return ""

    local_dt = utc_to_local(dt)
    return local_dt.strftime(format) if local_dt else ""


def is_expired_utc(valid_until: Optional[datetime]) -> bool:
    """
    Verifică dacă o dată de expirare a trecut.
    Compară cu timpul curent UTC.
    Presupune că valid_until este deja în UTC.
    """
    if not valid_until:
        return False

    now_utc = datetime.utcnow()
    return valid_until < now_utc


def get_invoice_status(invoice) -> dict:
    """
    Calculează statusul unui invoice.
    Returnează dict cu status, badge_class și text.
    """
    if invoice.is_quote:
        if invoice.converted_to_order:
            return {
                "status": "converted",
                "badge": "bg-success",
                "text": "Convertită"
            }
        elif invoice.valid_until and is_expired_utc(invoice.valid_until):
            return {
                "status": "expired",
                "badge": "bg-danger",
                "text": "Expirată"
            }
        else:
            return {
                "status": "active",
                "badge": "bg-warning",
                "text": "Activă"
            }
    else:  # is_invoice
        if hasattr(invoice, 'is_cancelled') and invoice.is_cancelled:
            return {
                "status": "cancelled",
                "badge": "bg-danger",
                "text": "Anulată"
            }
        else:
            return {
                "status": "issued",
                "badge": "bg-info",
                "text": "Emisă"
            }


def days_until_expiry(valid_until: Optional[datetime]) -> Optional[int]:
    """
    Calculează câte zile mai sunt până la expirare.
    Returnează None dacă nu e setat valid_until.
    Returnează număr negativ dacă a expirat.
    """
    if not valid_until:
        return None

    now_utc = datetime.utcnow()
    delta = valid_until - now_utc
    return delta.days


def format_time_ago(dt: Optional[datetime]) -> str:
    """
    Formatează timpul relativ (ex: "acum 5 minute", "ieri", etc)
    """
    if not dt:
        return ""

    now_utc = datetime.utcnow()
    delta = now_utc - dt

    if delta.days > 365:
        years = delta.days // 365
        return f"acum {years} an{'i' if years > 1 else ''}"
    elif delta.days > 30:
        months = delta.days // 30
        return f"acum {months} lun{'i' if months > 1 else 'ă'}"
    elif delta.days > 0:
        return f"acum {delta.days} zi{'le' if delta.days > 1 else ''}"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"acum {hours} or{'e' if hours > 1 else 'ă'}"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"acum {minutes} minut{'e' if minutes > 1 else ''}"
    else:
        return "chiar acum"


def time_only(dt: Optional[datetime]) -> str:
    """Filter pentru templates - doar ora."""
    if dt:
        local_dt = utc_to_local(dt)
        return local_dt.strftime('%H:%M')
    return ''


def datetime_iso(dt: Optional[datetime]) -> str:
    """Pentru JavaScript/JSON."""
    if dt:
        local_dt = utc_to_local(dt)
        return local_dt.isoformat()
    return ''


def days_ago(dt: Optional[datetime]) -> int:
    """Calculează câte zile au trecut de la datetime dat."""
    if not dt:
        return 0

    # Asigură-te că ambele sunt UTC
    now = datetime.utcnow()

    # Dacă dt are timezone, convertește la naive UTC
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    delta = now - dt
    return delta.days