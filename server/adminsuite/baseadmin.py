from typing import Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route
from starlette_admin.contrib.sqla.admin import _serve_file
from starlette_admin.contrib.sqla import Admin as StarletteAdmin
from starlette_admin.views import DropDown as StarletteDropDown


class Admin(StarletteAdmin):

    def mount_to(self, app: Starlette) -> None:
        print("Admin(StarletteAdmin): mount_to(self, app: Starlette)")
        print(f"Admin(StarletteAdmin): mount_to(self, app: Starlette => self.title={self.title})")
        print(f"Admin(StarletteAdmin): mount_to(self, app: Starlette => app: Starlette={app.__dict__})")

        try:
            """Automatically add route to serve sqlalchemy_file files"""
            __import__("sqlalchemy_file")
            self.routes.append(
                Route(
                    "/api/file/{storage}/{file_id}",
                    _serve_file,
                    methods=["GET"],
                    name="api:file",
                )
            )
        except ImportError:  # pragma: no cover
            pass
        super().mount_to(app)

    def init_auth(self) -> None:
        print("Admin(StarletteAdmin): init_auth(self)")
        if self.auth_provider is not None:
            self.auth_provider.setup_admin(self)

    def custom_render_js(self, request: Request) -> Optional[str]:

        print(f"request.base_url = {request.base_url}")

        return request.url_for("static", path="js/custom_render.js")
        # return request.url_for("server", path="adminsuite/statics/js/custom_render.js")


class DropDown(StarletteDropDown):
    pass

