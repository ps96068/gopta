from typing import Dict, Any
from sqlalchemy import select, func, false, true, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select
from starlette.requests import Request
from starlette_admin import CollectionField
from starlette_admin.exceptions import FormValidationError
from email_validator import validate_email, EmailNotValidError

from server.utils import decode_access_token, check_validity_token, get_hashed_password

from database import db_url, cfg_token, async_session_maker
from server.adminsuite.views.baseview import ModelView
from models import Client, ClientStatus, Company
from server.adminsuite.fields import (
    HasOne, IntegerField, StringField,
    HasMany, RelationField, NumberField,
    EnumField, BooleanField,
    EmailField, DateTimeField, PhoneField
)

status = [
    ClientStatus.user,
    ClientStatus.anonim,
    ClientStatus.company,
]


class ClientView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        IntegerField("telegram_id"),
        StringField("username"),
        PhoneField("phone_number"),
        # RelationField("company_id"),
        StringField("password_hash"),
        EmailField("email"),
        BooleanField("is_active"),
        EnumField(
            'status',
            enum=ClientStatus,
            form_template="forms/enum.html",
            select2=False
        ),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("last_visit", exclude_from_create=True),

        HasOne(
            "company",
            identity="companii",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),
        HasMany(
            "activities",
            identity="activitati_utilizator",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),
        HasMany(
            "interactions",
            identity="interactiuni_utilizator",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),
        HasMany(
            "requests",
            identity="cereri_utilizator",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),
        HasMany(
            "orders",
            identity="comenzi",
            exclude_from_list=True,
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True
        ),

    ]



