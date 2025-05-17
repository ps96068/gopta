from typing import Any

from starlette.requests import Request
# from starlette_admin.fields import BaseField
from server.adminsuite.fields import BaseField
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqla import ModelView as StarletteModelView



class ModelView(StarletteModelView):
    """
    Customized ModelView
    """
