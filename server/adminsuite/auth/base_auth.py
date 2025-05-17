from starlette_admin.auth import (
    AdminConfig,
    AuthProvider as StarletteAuthProvider
)
from models import StaffRole
from server.utils import decode_access_token
from typing import TYPE_CHECKING, Optional
from starlette.routing import Route
from starlette_admin.auth import AdminUser
from starlette_admin.exceptions import FormValidationError, LoginFailed
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.status import (
    HTTP_303_SEE_OTHER,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

if TYPE_CHECKING:
    print("TYPE_CHECKING")
    from starlette_admin.base import BaseAdmin

from starlette_admin.helpers import wrap_endpoint_with_kwargs


class MyAuthProvider(StarletteAuthProvider):

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        # print("MyAuthProvider => get_admin_user")

        current_user = request.session['username']
        return AdminUser(username=current_user)

    def get_admin_config(self, request: Request) -> AdminConfig:
        print("MyAuthProvider => get_admin_config")

        custom_app_title = "NONE"

        token = request.session.get("token")
        decoded_token = decode_access_token(token)

        if decoded_token['role'] == StaffRole.super_admin.value:
            custom_app_title = "Admin Dashboard"
        elif decoded_token['role'] == StaffRole.manager.value:
            custom_app_title = "Manager Dashboard"
        elif decoded_token['role'] == StaffRole.supervisor.value:
            custom_app_title = "Supervisor Dashboard"

        return AdminConfig(app_title=custom_app_title)

