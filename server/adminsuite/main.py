from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware



from database import engine, cfg_token
from .baseadmin import Admin, DropDown
from .auth import AdminAuthProvider
from models import Category
from .views.catalog.admin import AdminCategoryView
from .views.catalog.manager import ManagerCategoryView
from .views.catalog.supervisor import SupervisorCategoryView

from .admin_dashboard import add_admin_view
from .manager_dashboard import add_manager_view
from .supervisor_dashboard import add_supervisor_view


SECRET_KEY = cfg_token()['secret_key']



def add_dashboard(app):
    print()

    """ START Dashboard for admin """

    admin_panel = Admin(engine=engine, title="ADMIN Dashboard",
                        base_url="/admin", route_name="admin",
                        templates_dir="server/adminsuite/templates",
                        statics_dir="server/adminsuite/statics",
                        auth_provider=AdminAuthProvider(),
                        middlewares=[Middleware(SessionMiddleware, secret_key=SECRET_KEY)])


    add_admin_view(admin_panel)
    add_manager_view(admin_panel)
    add_supervisor_view(admin_panel)


    #
    #
    # admin_panel.add_view(
    #     DropDown(
    #         label="CATALOG",
    #         icon="fa fa-database",
    #         views=[
    #             AdminCategoryView(
    #                 model=Category,
    #                 identity="admin-categorii",
    #                 icon="fa-regular fa-folder"
    #             ),
    #         ],
    #         always_open=False,
    #     ),
    # )
    #
    # admin_panel.add_view(
    #     DropDown(
    #         label="CATALOG",
    #         icon="fa fa-database",
    #         views=[
    #             ManagerCategoryView(
    #                 model=Category,
    #                 identity="manager-categorii",
    #                 icon="fa-regular fa-folder"
    #             ),
    #         ],
    #         always_open=False,
    #     ),
    # )
    #
    # admin_panel.add_view(
    #     DropDown(
    #         label="CATALOG",
    #         icon="fa fa-database",
    #         views=[
    #             SupervisorCategoryView(
    #                 model=Category,
    #                 identity="supervisor-categorii",
    #                 icon="fa-regular fa-folder"
    #             ),
    #         ],
    #         always_open=False,
    #     ),
    # )

    """ END Dashboard for admin """



    admin_panel.mount_to(app)
    assert app.url_path_for("admin:index") == "/admin/"

    print("******* add_dashboard finished *******")