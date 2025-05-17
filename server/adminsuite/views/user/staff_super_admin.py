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
from server.models import Staff, StaffRole, Company
from server.adminsuite.fields import (
    HasOne, IntegerField, StringField,
    HasMany, RelationField, NumberField,
    EnumField, BooleanField,
    EmailField, DateTimeField, PhoneField
)

role = [
    StaffRole.super_admin,
    StaffRole.manager,
    StaffRole.supervisor,
]


class StaffSuperAdminView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("telegram_id"),
        StringField("username"),
        PhoneField("phone_number"),
        StringField("password_hash"),
        EmailField("email"),
        BooleanField("is_active"),
        EnumField(
            'role',
            enum=StaffRole,
            form_template="forms/enum.html",
            select2=False
        ),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("last_visit", exclude_from_create=True),

        HasMany(name="companies_created", label="Companies Created"),
        HasMany(name="posts", label="Posts"),
        HasMany(name="category", label="Categories Created"),
        HasMany(name="products", label="Products"),
        HasMany(name="product_images", label="Product Images"),
        HasMany(name="product_prices", label="Product Prices"),
        HasMany(name="img_author", label="Post Images"),

    ]