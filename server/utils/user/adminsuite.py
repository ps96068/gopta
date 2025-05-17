import logging

from starlette.authentication import BaseUser

from server.crud.adminsuite import AdminSuiteCRUD
from .password_and_hash import verify_password



logger = logging.getLogger(__name__)



async def adminsuite_auth(username: str, password: str):
    print(f"adminsuite_auth")

    user = await AdminSuiteCRUD.find_one_or_none(username=username)

    if user:
        # if user.is_active and user.role == StaffRole.super_admin:
        if user.is_active and user.is_admin:

            if verify_password(password, user.password_hash):
                print("user.is_active and user.is_admin")
                return user
    else:
        return None



# User class pentru autentificare
class AdminUser(BaseUser):
    def __init__(self, username: str, roles: list):
        self.username = username
        self.roles = roles

    @property
    def is_authenticated(self) -> bool:
        return True