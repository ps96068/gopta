import re
from typing import Dict, Any
from sqlalchemy.sql import Select
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from database import cfg_token
from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasMany, PhoneField, IntegerField,
    EmailField, EnumField, StringField,
    DateTimeField, HasOne
)
from models import CompanyStatus
from server.utils import decode_access_token, check_validity_token


class CompanyView(ModelView):
    fields = [
        StringField("name"),
        EnumField(
            'status',
            enum=CompanyStatus,
            form_template="forms/enum.html",
            select2=False
        ),
        StringField("address", exclude_from_list=True),
        EmailField("email"),
        PhoneField("phone_number"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasMany("clients", identity="admini", exclude_from_create=True),
        HasOne("creator"),

    ]