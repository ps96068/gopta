from server.adminsuite.baseadmin import DropDown
from .views.blog.manager import *
from .views.catalog.manager import *
from .views.marketing.manager import *
from .views.sale.manager import *
from .views.user.manager import *

from models import Category


def add_manager_view(admin_panel):

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
                ManagerCategoryView(
                    model=Category,
                    identity="manager-categorii",
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


