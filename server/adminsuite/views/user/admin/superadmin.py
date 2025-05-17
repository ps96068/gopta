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


class SuperAdminView(ModelView):
    fields = [
        IntegerField(
            name="id",
            exclude_from_create=True
        ),
        StringField(name="telegram_id"),
        StringField(name="username"),
        StringField(name="password_hash", label="Password", exclude_from_list=True, exclude_from_detail=True),
        PhoneField(name="phone_number"),
        EmailField(name="email"),
        BooleanField(name="is_active"),
        EnumField(
            name='role',
            enum=StaffRole,
            form_template="forms/enum.html",
            select2=False,
            exclude_from_list=True,
            exclude_from_create=True,
        ),
        DateTimeField(name="create_date", exclude_from_create=True),
        DateTimeField(name="last_visit", exclude_from_create=True),
    ]


    def get_list_query(self) -> Select:

        return super().get_list_query().where(
            self.model.role.in_(
                [
                    StaffRole.super_admin,
                ]
            )
        )

    def get_count_query(self) -> Select:

        return super().get_count_query().where(
            self.model.role.in_(
                [
                    StaffRole.super_admin,
                ]
            )
        )


    # async def _check_telegram_id_data(self, telegram_id) -> Select:
    #     rez = await AdminSuiteCRUD.find_one_or_none(telegram_id=telegram_id)
    #     if rez:
    #         return True
    #     return False
    #
    # async def _check_email_data(self, email) -> Select:
    #     rez = await AdminSuiteCRUD.find_one_or_none(email=email)
    #     if rez:
    #         return True
    #     return False

    # async def _check_form_data(self, **data):
    #     rez = await AdminSuiteCRUD.find_one_or_none(**data)
    #     if rez:
    #         return True
    #     return False


    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        print("My Validadting user data")

        print(f"My Validadting user data request={request['state']['action']}")
        print(f"My Validadting user data request._form={request._form}")
        print(f"My Validadting user data request._form.get('password_hash')={request._form.get('password_hash')}")

        current_data: Dict = dict()

        # action_type = await self.handle_action(request, pks=request['path_params']['pk'], name='edit')

        # print(f"My Validadting user data action_type={action_type}")

        # tg: bool = await self._check_telegram_id_data(telegram_id=data["telegram_id"])
        # email: bool = await self._check_email_data(email=data["email"])

        errors: Dict[str, str] = dict()

        if request['state']['action'] == RequestAction.CREATE:
            print("cream")

            if (
                    not data["telegram_id"] or
                    len(data["telegram_id"]) < 3
            ):
                errors["telegram_id"] = "Invalid Telegram ID !"
            elif await self._check_form_data(telegram_id=data["telegram_id"]):
                errors["telegram_id"] = "Telegram ID exists!"
            if (
                    not data["username"] or
                    len(data["username"]) < 4
            ):
                errors["username"] = "Invalid Username. Must be at least 4 characters !"
            elif await self._check_form_data(username=data["username"]):
                errors["username"] = "Username exists!"
            if (
                    not data["phone_number"] or
                    not re.fullmatch(r"^\+?[0-9]{8,13}$", data["phone_number"])
            ):
                errors["phone_number"] = "Invalid phone number !"
            elif await self._check_form_data(phone_number=data["phone_number"]):
                errors["phone_number"] = "Phone number exists!"
            if (
                    not data["password_hash"] or
                    len(data["password_hash"]) < 6
            ):
                errors["password_hash"] = "Invalid Password. Must be at least 6 characters, min 1 number, min 1 uppercase !"
            if (
                    not data["email"] or
                    not re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", data["email"])
            ):
                errors["email"] = "Invalid email adress !"
            elif await self._check_form_data(email=data["email"]):
                errors["email"] = "Email adress exists!"
            if len(errors) > 0:
                raise FormValidationError(errors)

        elif request['state']['action'] == RequestAction.EDIT:
            print("editam")
            current_user = data.get("username", None)
            # print(f"current_user={current_user}")
            current_user_data = await AdminSuiteCRUD.find_one_or_none(username=current_user)
            if not current_user_data:
                raise FormValidationError("Invalid user data")

            # current_user_id = current_user_data.id

            # -------- telegram_id -----------
            telegram_id_from_db = current_user_data.telegram_id
            new_telegram_id = data.get("telegram_id", None)
            # print(f"telegram_id_from_db={telegram_id_from_db} \n new_telegram_id={new_telegram_id}")
            if new_telegram_id != telegram_id_from_db:
                if new_telegram_id is not None:
                    if len(new_telegram_id) < 3:
                        errors["telegram_id"] = "Invalid Telegram ID !"
                    if await self._check_form_data(telegram_id=new_telegram_id):
                        errors["telegram_id"] = "Telegram ID exists!"

            # -------- username -----------
            username_from_db = current_user_data.username
            new_username = data.get("username", None)
            if new_username != username_from_db:
                if new_username is not None:
                    if len(new_username) < 4:
                        errors["username"] = "Invalid Username. Must be at least 4 characters !"
                    if await self._check_form_data(username=new_username):
                        errors["username"] = "Username exists!"

            # -------- phone_number -----------
            phone_number_from_db = current_user_data.phone_number
            new_phone_number = data.get("phone_number", None)
            if new_phone_number != phone_number_from_db:
                if new_phone_number is not None:
                    if not re.fullmatch(r"^\+?[0-9]{8,13}$", new_phone_number):
                        errors["phone_number"] = "Invalid phone number !"
                    if await self._check_form_data(phone_number=new_phone_number):
                        errors["phone_number"] = "Phone number exists!"

            # -------- password_hash -----------
            password_hash_from_db = current_user_data.password_hash
            new_password_from_form = data.get("password_hash", None)

            print(f"** password_hash_from_db={password_hash_from_db} \n** new_password_from_form={new_password_from_form}")

            if new_password_from_form is None or len(new_password_from_form) < 6:
                errors["password_hash"] = "Invalid Password. Must be at least 6 characters, min 1 number, min 1 uppercase !"

            if new_password_from_form != password_hash_from_db:
                new_hash = get_hashed_password(new_password_from_form)
                data["password_hash"] = new_hash



            # if new_password is not None and new_password.strip() != "":
            #     if len(new_password) < 6:
            #         errors["password_hash"] = "Invalid Password. Must be at least 6 characters, min 1 number, min 1 uppercase !"
            #     new_password_hash = get_hashed_password(new_password)
            #     if new_password_hash != old_password_hash:
            #         if await self._check_form_data(password_hash=new_password_hash):
            #             errors["password_hash"] = "Password exists!"



            # -------- email -----------
            email_from_db = current_user_data.email
            new_email = data.get("email", None)
            if new_email != email_from_db:
                if new_email is not None:
                    if not re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", new_email):
                        errors["email"] = "Invalid email adress !"
                    if await self._check_form_data(email=new_email):
                        errors["email"] = "Email adress exists!"

            if len(errors) > 0:
                raise FormValidationError(errors)



        return await super().validate(request, data)

    def is_accessible(self, request: Request) -> bool:
        token = request.session.get("token")
        decoded_token = decode_access_token(token)
        user = request.session.get('username')

        if decoded_token['role'] == StaffRole.super_admin.value:
            return True
        return False

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        print("before_create")
        # setattr(obj, 'password_hash', get_hashed_password(data["password_hash"]))
        setattr(obj, 'role', StaffRole.super_admin.value)

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        print("create")
        data["password_hash"] = get_hashed_password(data["password_hash"])
        return await super().create(request, data)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        print("superadmin edit")
        # data["password_hash"] = get_hashed_password(data["password_hash"])
        return await super().edit(request, pk, data)

