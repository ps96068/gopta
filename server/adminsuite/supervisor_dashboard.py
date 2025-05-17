from server.adminsuite.baseadmin import DropDown
from .views.blog.supervisor import *
from .views.catalog.supervisor import *
from .views.marketing.supervisor import *
from .views.sale.supervisor import *
from .views.user.supervisor import *

from models import Category



def add_supervisor_view(admin_panel):

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
                SupervisorCategoryView(
                    model=Category,
                    identity="supervisor-categorii",
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

