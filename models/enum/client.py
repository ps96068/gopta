# models/enum/client.py

import enum

class UserStatus(enum.Enum):
    """Status-uri disponibile pentru clienți."""
    ANONIM = "anonim"
    USER = "user"
    INSTALATOR = "instalator"
    PRO = "pro"