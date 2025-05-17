import re
from typing import Dict, Any
from sqlalchemy import select, func, false, true, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from starlette.requests import Request
from starlette_admin import CollectionField
from starlette_admin.exceptions import FormValidationError
from starlette_admin._types import RequestAction
from starlette_admin.fields import BaseField
from starlette_admin.helpers import extract_fields

from server.crud import AdminSuiteCRUD
from server.utils import decode_access_token, check_validity_token, get_hashed_password, verify_user_password

from database import db_url, cfg_token, async_session_maker
# from server.adminsuite.views.baseview import ModelView
from server.adminsuite.views.baseadminview import ModelAdminView as ModelView
from models import Staff, StaffRole
from server.adminsuite.fields import (
    HasOne, IntegerField, StringField,
    HasMany, RelationField, NumberField,
    EnumField, BooleanField,
    EmailField, DateTimeField, PhoneField
)


class StaffView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("telegram_id"),
        StringField("username"),
        PhoneField("phone_number"),
        StringField("password_hash"),
        EmailField("email"),
        BooleanField("is_active"),
        BooleanField(
            "hide",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),
        EnumField(
            'role',
            enum=StaffRole,
            # form_template="forms/enum.html",
            select2=False
            # choices=[(StaffRole.super_admin, StaffRole.super_admin), (StaffRole.manager), (StaffRole.supervisor)]
        ),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
    ]

    # def is_accessible(self, request: Request) -> bool:
    #     token = request.session.get("token")
    #     decoded_token = decode_access_token(token)
    #     user = request.session.get('username')
    #
    #     if decoded_token['role'] == StaffRole.super_admin.value or decoded_token['role'] == StaffRole.manager.value or decoded_token['role'] == StaffRole.supervisor.value:
    #         return False
    #     return True