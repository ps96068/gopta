from starlette_admin.auth import AdminConfig
from starlette_admin.exceptions import LoginFailed
from starlette.requests import Request
from starlette.responses import Response


from .base_auth import MyAuthProvider as AuthProvider
from .errors import AccessFailed
from models import StaffRole
from server.crud import AdminSuiteCRUD
from server.utils.user import (create_access_token,
                               decode_access_token,
                               verify_user_password,
                               check_validity_token)


class AdminAuthProvider(AuthProvider):

    async def login(
            self,
            username: str,
            password: str,
            remember_me: bool,
            request: Request,
            response: Response,
    ) -> Response:

        print("AdminAuthProvider(AuthProvider) => login()")

        user = await AdminSuiteCRUD.find_one_or_none(username=username)

        print(f"AdminAuthProvider(AuthProvider) => login() user: {user}")

        if user and verify_user_password(password, user.password_hash):
            if user.is_active and user.role in [StaffRole.super_admin, StaffRole.manager, StaffRole.supervisor]:
                print(f"AdminAuthProvider(AuthProvider) => login() => request: {request}")
                access_token = create_access_token({"sub": user.username, "role": user.role.value})
                request.session["token"] = access_token  # Salvează tokenul în sesiune
                request.session.update({"username": username, })

                return response

            raise AccessFailed("Access denied")
        raise LoginFailed("Invalid username or password")


        # if user and verify_user_password(password, user.password_hash):
        #     if user.is_active and user.role in [StaffRole.super_admin]:
        #         print(f"AdminAuthProvider(AuthProvider) => login() => request: {request}")
        #         access_token = create_access_token({"sub": user.username, "role": user.role.value})
        #         request.session["token"] = access_token  # Salvează tokenul în sesiune
        #         request.session.update({"username": username, })
        #
        #         return response
        #
        #     raise AccessFailed("Access denied")
        # raise LoginFailed("Invalid username or password")


    async def logout(self, request: Request, response: Response) -> Response:
        print("AdminAuthProvider(AuthProvider) => logout()")
        request.session.clear()
        print(f"AdminAuthProvider(AuthProvider) => logout() => response = {response.__dict__}")
        return response


    async def is_authenticated(self, request: Request) -> bool:
        """Check if the current user is authenticated."""

        print("AdminAuthProvider(AuthProvider) => is_authenticated()")
        print(f"AdminAuthProvider(AuthProvider) => is_authenticated() => request.session: {request.session}")
        token = request.session.get("token")
        print(f"AdminAuthProvider(AuthProvider) => is_authenticated() => token: {token}")

        if token:
            try:
                decoded_token = decode_access_token(token)

                print(f"AdminAuthProvider(AuthProvider) => is_authenticated() => decoded_token: {decoded_token}")
                print(f"AdminAuthProvider(AuthProvider) => is_authenticated() => decoded_token: {type(decoded_token)}")

                validity = check_validity_token(decoded_token)

                if validity:
                    return True
                else:
                    return False

                # if decoded_token["sub"]:
                #     return True
            except Exception:
                pass
        else:
            return False





