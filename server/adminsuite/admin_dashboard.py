from server.adminsuite.baseadmin import DropDown
from .views.blog.admin import *
from .views.catalog.admin import *
from .views.marketing.admin import *
from .views.sale.admin import *
from .views.user.admin import (
    StaffView,
    SuperAdminView,
    ManagerView,
    SupervisorView
)
from models import (
    Staff,
    Category,
)


def add_admin_view(admin_panel):

    admin_panel.add_view(
        DropDown(
            label="ADMIN & STAFF",
            icon="fa fa-receipt",
            views=[
                StaffView(
                    model=Staff,
                    label="Full STAFFs",
                    icon="fa fa-user-secret",
                    name="Staff",
                    identity="staff",

                ),
                SuperAdminView(
                    model=Staff,
                    label="Admins",
                    icon = "fa fa-user-secret",
                    name="Admin",
                    identity="admini"
                ),
                ManagerView(
                    model=Staff,
                    label="Managers",
                    icon="fa fa-users",
                    name="Manager",
                    identity="manageri"
                ),
                SupervisorView(
                    model=Staff,
                    label="Supervisors",
                    icon="fa fa-users",
                    name="Supervisor",
                    identity="supervisori"
                ),
            ],
            always_open=False,
        )
    )

    admin_panel.add_view(
        DropDown(
            label="CLIENTS",
            icon="fa fa-receipt",
            views=[

            ],
            always_open=False,
        )
    )

    admin_panel.add_view(
        DropDown(
            label="BLOG",
            icon="fa fa-newspaper",
            views=[
                # PostView(
                #     model=Post,
                #     identity="postari",
                #     icon="fa-regular fa-newspaper"
                # ),
                # PostImageView(
                #     model=PostImage,
                #     identity="imagini_postare",
                #     icon="fa-regular fa-image"
                # ),
            ],
            always_open=False,
        )
    )

    admin_panel.add_view(
        DropDown(
            label="CATALOG",
            icon="fa fa-database",
            views=[
                AdminCategoryView(
                    model=Category,
                    identity="admin-categorii",
                    icon="fa-regular fa-folder"
                ),
            ],
            always_open=False,
        ),
    )

    admin_panel.add_view(
        DropDown(
            label="SALES",
            icon="fa fa-bullhorn",
            views=[

            ],
            always_open=False,
        )
    )

    admin_panel.add_view(
        DropDown(
            label="MARKETING",
            icon="fa fa-map-marker",
            views=[

            ],
            always_open=False,
        )
    )

