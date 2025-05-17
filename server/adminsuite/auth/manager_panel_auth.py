from starlette_admin.exceptions import LoginFailed
from starlette.requests import Request
from starlette.responses import Response


from .base_auth import MyAuthProvider as AuthProvider
from .errors import AccessFailed
from server.models import StaffRole
from server.crud import AdminSuiteCRUD
from server.utils.user import (create_access_token,
                               decode_access_token,
                               verify_user_password,
                               check_validity_token)


class ManagerAuthProvider(AuthProvider):
    pass