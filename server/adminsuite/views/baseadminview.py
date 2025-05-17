from typing import Any

from starlette.requests import Request
# from starlette_admin.fields import BaseField
from server.adminsuite.fields import BaseField
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqla import ModelView as StarletteModelView

from server.crud import AdminSuiteCRUD


class ModelAdminView(StarletteModelView):
    """
    Customized ModelView
    """

    async def _check_form_data(self, **data):
        rez = await AdminSuiteCRUD.find_one_or_none(**data)
        if rez:
            return True
        return False
