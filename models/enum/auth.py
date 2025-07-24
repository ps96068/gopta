# models/enum/auth.py

from enum import Enum


class AuthUserType(str, Enum):
    """Tipuri de utilizatori pentru autentificare."""
    STAFF = "staff"
    VENDOR = "vendor"