# models/enum/staff.py

import enum


class StaffRole(enum.Enum):
    """
    Roluri disponibile pentru Staff.

    Permisiuni:
    - SUPER_ADMIN: Acces total
    - MANAGER: Nu poate gestiona Staff/Marketing, poate crea/edita vendori
    - SUPERVISOR: Doar vizualizare (read-only)
    """
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"

