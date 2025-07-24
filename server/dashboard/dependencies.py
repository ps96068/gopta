# server/dashboard/dependencies.py
"""
Dependencies pentru Dashboard: auth, permissions, etc.
"""
from typing import Optional, List, Union
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request, Form, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import selectinload

from cfg import get_db, SECRET_KEY, ALGORITHM
from models import Staff, StaffRole, VendorStaff, VendorRole, AuthUserType
from server.context_processors import global_context_processor
from services.models.staff_services import StaffService

# OAuth2 scheme pentru dashboard
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/dashboard/auth/login",
    auto_error=False
)

# Union type pentru user
DashboardUser = Union[Staff, VendorStaff]


# async def get_current_staff_optional(
#         request: Request,
#         token: Optional[str] = Depends(oauth2_scheme),
#         db: AsyncSession = Depends(get_db)
# ) -> Optional[Staff]:
#     """
#     Obține staff curent din token JWT (optional).
#     """
#     if not token:
#         # Check session cookie as fallback
#         token = request.cookies.get("dashboard_token")
#
#     if not token:
#         return None
#
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         staff_id: int = payload.get("sub")
#         if staff_id is None:
#             return None
#         staff_id = int(staff_id)
#     except (InvalidTokenError, ValueError):
#         return None
#
#     # Get staff from DB
#     result = await db.execute(
#         select(Staff).where(Staff.id == staff_id)
#     )
#     staff = result.scalar_one_or_none()
#
#     if not staff or not staff.is_active:
#         return None
#
#     return staff
#
#
# async def get_current_staff(
#         request: Request,
#         staff: Optional[Staff] = Depends(get_current_staff_optional)
# ) -> Staff:
#     """
#     Obține staff curent (required).
#     Redirect la login dacă nu e autentificat.
#     """
#     if not staff:
#         # Pentru request-uri AJAX, returnează 401
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Authentication required"
#             )
#
#         # Pentru browser, redirect la login
#         login_url = f"/dashboard/auth/login?next={request.url.path}"
#         raise HTTPException(
#             status_code=status.HTTP_307_TEMPORARY_REDIRECT,
#             headers={"Location": login_url}
#         )
#     return staff
#
#
# def require_role(allowed_roles: List[str]):
#     """
#     Dependency factory pentru verificare rol.
#
#     Usage:
#         @router.get("/", dependencies=[Depends(require_role(["super_admin", "manager"]))])
#     """
#
#     async def role_checker(
#             staff: Staff = Depends(get_current_staff)
#     ):
#         if staff.role.value not in allowed_roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"Rol insuficient. Necesită unul din: {', '.join(allowed_roles)}"
#             )
#         return staff
#
#     return role_checker
#
#
# def check_permission(
#         action: str,
#         resource: str,
#         staff: Staff
# ) -> bool:
#     """
#     Verifică permisiune specifică pentru o acțiune.
#
#     Args:
#         action: "create", "read", "update", "delete"
#         resource: "staff", "order", "product", etc.
#         staff: Staff object
#
#     Returns:
#         True dacă are permisiune, False altfel
#     """
#     role = staff.role
#
#     # Super Admin poate face orice
#     if role == StaffRole.SUPER_ADMIN:
#         return True
#
#     # Manager cu permisiuni granulare
#     if role == StaffRole.MANAGER:
#         # Nu poate gestiona staff niciodată
#         if resource == "staff":
#             return False
#
#         # Pentru clienți - verifică permisiunea specifică
#         if resource == "client":
#             # Read întotdeauna permis
#             if action == "read":
#                 return True
#             # Create/Update/Delete doar dacă are permisiune
#             return staff.can_manage_clients
#
#         # Pentru produse
#         if resource == "product":
#             if action == "read":
#                 return True
#             return staff.can_manage_products
#
#         # Pentru comenzi
#         if resource == "order":
#             if action == "read":
#                 return True
#             return staff.can_manage_orders
#
#         # Alte resurse - permite tot
#         return True
#
#     # Supervisor - doar read pentru orice
#     if role == StaffRole.SUPERVISOR:
#         return action == "read"
#
#     return False
#
#
# class PermissionChecker:
#     """
#     Dependency class pentru verificare permisiuni.
#
#     Usage:
#         @router.post(
#             "/products",
#             dependencies=[Depends(PermissionChecker("create", "product"))]
#         )
#     """
#
#     def __init__(self, action: str, resource: str):
#         self.action = action
#         self.resource = resource
#
#     async def __call__(
#             self,
#             staff: Staff = Depends(get_current_staff)
#     ):
#         if not check_permission(self.action, self.resource, staff):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"Nu aveți permisiune pentru: {self.action} {self.resource}"
#             )
#         return staff
#
#
# # Helpers pentru templates
# def can_create(staff: Staff, resource: str) -> bool:
#     """Helper pentru template: verifică dacă poate crea."""
#     if not staff:  # ADAUGĂ ASTA
#         return False
#     return check_permission("create", resource, staff)
#
#
# def can_update(staff: Staff, resource: str) -> bool:
#     """Helper pentru template: verifică dacă poate actualiza."""
#     if not staff:  # ADAUGĂ ASTA
#         return False
#     return check_permission("update", resource, staff)
#
#
# def can_delete(staff: Staff, resource: str) -> bool:
#     """Helper pentru template: verifică dacă poate șterge."""
#     if not staff:  # ADAUGĂ ASTA
#         return False
#     return check_permission("delete", resource, staff)
#
#
# def can_read(staff: Staff, resource: str) -> bool:
#     """Helper pentru template: verifică dacă poate citi."""
#     if not staff:  # ADAUGĂ ASTA
#         return False
#     return check_permission("read", resource, staff)
#
#
# # Context processor pentru templates
# async def get_template_context(
#         request: Request,
#         staff: Staff
# ) -> dict:
#     """
#     Context de bază pentru toate template-urile.
#     """
#     from .config import MODELS_CONFIG, MENU_STRUCTURE
#
#     return {
#         "request": request,
#         "staff": staff,
#         "role": staff.role.value,
#         "is_super_admin": staff.role == StaffRole.SUPER_ADMIN,
#         "is_manager": staff.role == StaffRole.MANAGER,
#         "is_supervisor": staff.role == StaffRole.SUPERVISOR,
#         "can_create": can_create,
#         "can_update": can_update,
#         "can_delete": can_delete,
#         "can_read": can_read,
#         "menu_structure": MENU_STRUCTURE,
#         "models_config": MODELS_CONFIG,
#         "current_year": datetime.now().year,
#         "dashboard_title": "PCE Admin Dashboard",
#         "get_flashed_messages": lambda **kwargs: []
#     }
#
#
# # Form dependencies
# async def pagination_params(
#         page: int = 1,
#         per_page: int = 20,
#         sort_by: Optional[str] = None,
#         sort_desc: bool = True
# ) -> dict:
#     """
#     Parametri comuni pentru paginare.
#     """
#     return {
#         "page": max(1, page),
#         "per_page": min(100, max(1, per_page)),
#         "sort_by": sort_by,
#         "sort_desc": sort_desc,
#         "offset": (max(1, page) - 1) * min(100, max(1, per_page))
#     }
#
#
# # Mobile detection
# def is_mobile_request(request: Request) -> bool:
#     """
#     Detectează dacă request-ul vine de pe mobil.
#     """
#     user_agent = request.headers.get("user-agent", "").lower()
#     mobile_agents = ["android", "iphone", "mobile", "blackberry", "windows phone"]
#     return any(agent in user_agent for agent in mobile_agents)




# Multi-Vendor Dashboard additional Dependencies

async def get_current_user_optional(
        request: Request,
        token: Optional[str] = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> Optional[Union[Staff, VendorStaff]]:
    """
    Obține utilizator curent din token JWT (optional).
    Returnează Staff sau VendorStaff bazat pe user_type din token.
    """
    if not token:
        # Check session cookie as fallback
        token = request.cookies.get("dashboard_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        user_type: str = payload.get("user_type")

        if not user_id or not user_type:
            return None

        # Get user bazat pe tip
        if user_type == AuthUserType.STAFF.value:
            result = await db.execute(
                select(Staff).where(Staff.id == user_id)
            )
            user = result.scalar_one_or_none()
        elif user_type == AuthUserType.VENDOR.value:
            result = await db.execute(
                select(VendorStaff)
                .options(selectinload(VendorStaff.company))  # Eager load company
                .where(VendorStaff.id == user_id)
            )
            user = result.scalar_one_or_none()
        else:
            return None

        if not user or not user.is_active:
            return None

        return user

    except (InvalidTokenError, ValueError):
        return None


async def get_current_user(
        request: Request,
        user: Optional[Union[Staff, VendorStaff]] = Depends(get_current_user_optional)
) -> Union[Staff, VendorStaff]:
    """
    Obține utilizator curent (required).
    Redirect la login dacă nu e autentificat.
    """
    if not user:
        # Pentru request-uri AJAX, returnează 401
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Pentru browser, redirect la login
        login_url = f"/dashboard/auth/login?next={request.url.path}"
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": login_url}
        )
    return user


# Dependency pentru Staff only
async def get_current_staff(
        request: Request,
        user: Union[Staff, VendorStaff] = Depends(get_current_user)
) -> Staff:
    """Verifică că utilizatorul este Staff."""
    if not isinstance(user, Staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces permis doar pentru Staff"
        )
    return user


# Dependency pentru VendorStaff only
async def get_current_vendor_staff(
        request: Request,
        user: Union[Staff, VendorStaff] = Depends(get_current_user)
) -> VendorStaff:
    """ Verifică că utilizatorul este VendorStaff ȘI că compania este activă. """
    if not isinstance(user, VendorStaff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces permis doar pentru Vendor"
        )

    # VERIFICARE CRITICĂ: Compania trebuie să rămână activă în timpul sesiunii
    if hasattr(user, 'company') and user.company and not user.company.is_active:
        print(f"🚫 SESIUNE INVALIDĂ: Compania {user.company.name} a fost dezactivată")
        print(f"   User: {user.email}")

        # Force logout prin redirect la login cu mesaj
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/dashboard/auth/login?error=company_deactivated"}
        )


    return user


# Funcție pentru verificări periodice
async def check_vendor_company_status(
        vendor_staff: VendorStaff,
        db: AsyncSession
) -> bool:
    """
    Verifică în timp real dacă compania vendor-ului este încă activă.
    Folosit pentru verificări periodice în sesiune.
    """
    from sqlalchemy import select
    from models import VendorCompany

    result = await db.execute(
        select(VendorCompany.is_active)
        .where(VendorCompany.id == vendor_staff.company_id)
    )
    is_active = result.scalar_one_or_none()

    if not is_active:
        print(f"⚠️  VERIFICARE SESIUNE: Compania ID {vendor_staff.company_id} este dezactivată")
        return False

    return True



def require_role(allowed_roles: List[str]):
    """
    Dependency factory pentru verificare rol.
    Funcționează atât pentru Staff cât și pentru VendorStaff.
    """

    async def role_checker(
            user: Union[Staff, VendorStaff] = Depends(get_current_user)
    ):
        if isinstance(user, Staff):
            if user.role.value not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Rol insuficient. Necesită unul din: {', '.join(allowed_roles)}"
                )
        elif isinstance(user, VendorStaff):
            if user.role.value not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Rol insuficient. Necesită unul din: {', '.join(allowed_roles)}"
                )
        return user

    return role_checker


def check_permission(
        action: str,
        resource: str,
        user: Union[Staff, VendorStaff]
) -> bool:
    """
    Verifică permisiune specifică pentru o acțiune.
    """
    if isinstance(user, Staff):
        return check_staff_permission(action, resource, user)
    elif isinstance(user, VendorStaff):
        return check_vendor_permission(action, resource, user)
    return False


def check_staff_permission(action: str, resource: str, staff: Staff) -> bool:
    """Verifică permisiuni pentru Staff."""
    role = staff.role

    if role == StaffRole.SUPER_ADMIN:
        return True

    if role == StaffRole.MANAGER:

        if resource == "vendor_company":
            if action in ["create", "read", "update"]:
                return True
            if action in ["delete", "activate", "deactivate"]:
                return False

        if resource == "staff":
            return False

        if resource == "client":
            if action == "read":
                return True
            return staff.can_manage_clients

        if resource == "product":
            if action == "read":
                return True
            return staff.can_manage_products

        if resource == "order":
            if action == "read":
                return True
            return staff.can_manage_orders

        return True

    if role == StaffRole.SUPERVISOR:
        return action == "read"

    return False


def check_vendor_permission(action: str, resource: str, vendor_staff: VendorStaff) -> bool:
    """Verifică permisiuni pentru VendorStaff."""
    role = vendor_staff.role

    # Vendor Admin poate face tot pentru compania lui
    if role == VendorRole.ADMIN:
        # Dar nu poate accesa resurse globale
        if resource in ["staff", "client", "vendor_company"]:
            return action == "read"
        return True

    # Vendor Manager - permisiuni limitate
    if role == VendorRole.MANAGER:
        if resource in ["product", "order", "cart"]:
            return True
        return action == "read"

    return False


class PermissionChecker:
    """
    Dependency class pentru verificare permisiuni.
    """

    def __init__(self, action: str, resource: str):
        self.action = action
        self.resource = resource

    async def __call__(
            self,
            user: Union[Staff, VendorStaff] = Depends(get_current_user)
    ):
        if not check_permission(self.action, self.resource, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Nu aveți permisiune pentru: {self.action} {self.resource}"
            )
        return user


# Helpers pentru templates - actualizate pentru ambele tipuri de utilizatori
def can_create(user: Optional[Union[Staff, VendorStaff]], resource: str) -> bool:
    """Helper pentru template: verifică dacă poate crea."""
    if not user:
        return False
    return check_permission("create", resource, user)


def can_update(user: Optional[Union[Staff, VendorStaff]], resource: str) -> bool:
    """Helper pentru template: verifică dacă poate actualiza."""
    if not user:
        return False
    return check_permission("update", resource, user)


def can_delete(user: Optional[Union[Staff, VendorStaff]], resource: str) -> bool:
    """Helper pentru template: verifică dacă poate șterge."""
    if not user:
        return False
    return check_permission("delete", resource, user)


def can_read(user: Optional[Union[Staff, VendorStaff]], resource: str) -> bool:
    """Helper pentru template: verifică dacă poate citi."""
    if not user:
        return False
    return check_permission("read", resource, user)


# Context processor pentru templates - actualizat
async def get_template_context(
        request: Request,
        user: Union[Staff, VendorStaff],
        db: Optional[AsyncSession] = None
) -> dict:
    """
    Context de bază pentru toate template-urile.
    """
    context = global_context_processor(request)

    is_vendor = isinstance(user, VendorStaff)
    is_staff = isinstance(user, Staff)

    context.update(
        {
            "request": request,
            "user": user,
            "is_vendor": is_vendor,
            "user_type": "vendor" if is_vendor else "staff",
            "can_create": can_create,
            "can_update": can_update,
            "can_delete": can_delete,
            "can_read": can_read,
            "current_year": datetime.now().year,
            "get_flashed_messages": lambda **kwargs: []
        }
    )

    print(f"context: {context}")

    if is_vendor:
        from .config import VENDOR_MODELS_CONFIG, VENDOR_MENU_STRUCTURE

        # Verifică dacă company este deja încărcată
        company_name = "Vendor"  # Default
        if hasattr(user, 'company') and user.company:
            company_name = user.company.name
        elif db:
            # Dacă avem DB session, încarcă company
            from models import VendorCompany
            result = await db.execute(
                select(VendorCompany).where(VendorCompany.id == user.company_id)
            )
            company = result.scalar_one_or_none()
            if company:
                company_name = company.name
                user.company = company  # Cache pentru utilizări ulterioare

        context.update({
            "dashboard_prefix": "/dashboard/vendor",
            "role": user.role.value,
            "is_vendor_admin": user.role == VendorRole.ADMIN,
            "is_vendor_manager": user.role == VendorRole.MANAGER,
            "menu_structure": VENDOR_MENU_STRUCTURE,
            "models_config": VENDOR_MODELS_CONFIG,
            "dashboard_title": f"{company_name} - Dashboard",
            "company": user.company if hasattr(user, 'company') else None,
            "company_name": company_name
        })
    else:
        from .config import STAFF_MODELS_CONFIG, STAFF_MENU_STRUCTURE

        context.update({
            "dashboard_prefix": "/dashboard/staff",
            "staff": user,
            "role": user.role.value,
            "is_super_admin": user.role == StaffRole.SUPER_ADMIN,
            "is_manager": user.role == StaffRole.MANAGER,
            "is_supervisor": user.role == StaffRole.SUPERVISOR,
            "menu_structure": STAFF_MENU_STRUCTURE,
            "models_config": STAFF_MODELS_CONFIG,
            "dashboard_title": "PCE Admin Dashboard"
        })

    return context


# Alte dependencies existente rămân la fel...
async def pagination_params(
        page: int = 1,
        per_page: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = True
) -> dict:
    """
    Parametri comuni pentru paginare.
    """
    return {
        "page": max(1, page),
        "per_page": min(100, max(1, per_page)),
        "sort_by": sort_by,
        "sort_desc": sort_desc,
        "offset": (max(1, page) - 1) * min(100, max(1, per_page))
    }


def is_mobile_request(request: Request) -> bool:
    """
    Detectează dacă request-ul vine de pe mobil.
    """
    user_agent = request.headers.get("user-agent", "").lower()
    mobile_agents = ["android", "iphone", "mobile", "blackberry", "windows phone"]
    return any(agent in user_agent for agent in mobile_agents)




