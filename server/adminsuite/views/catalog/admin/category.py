from typing import Dict, Any
from pathlib import Path
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from database import async_session_maker
import aiofiles
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.exceptions import FormValidationError

from models import StaffRole, Category
from server.crud import AdminSuiteCRUD
from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    IntegerField, HasMany, HasOne, ImageField,
    StringField, TextAreaField, DateTimeField,
    BooleanField, TinyMCEEditorField
)
from server.utils import decode_access_token

DEFAULT_IMAGE_PATH = "static/shop/category/default.png"
container_base_path = Path("./static/shop/category/")
container_base_path.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

class AdminCategoryViewCRUD:
    model = Category


    @classmethod
    async def find_one_or_none(cls, **filter_by):
        print("find_one_or_none")

        print(f"find_one_or_none => **filter_by => {filter_by}")

        try:

            async with async_session_maker() as session:

                query = select(cls.model).filter_by(**filter_by)
                response = await session.execute(query)
                result = response.scalar_one_or_none()

                return result

        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
        except Exception as e:
            logger.error(f"Error in find_one_or_none() function: {str(e)}")
            raise e

    @classmethod
    async def _check_form_data(self, **data):
        rez = await self.find_one_or_none(**data)
        if rez:
            return True
        return False


class AdminCategoryView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("name"),
        # TextAreaField("description", exclude_from_list=True),
        TinyMCEEditorField("description", exclude_from_list=True),
        ImageField("image_path", label="Add image"),
        BooleanField("is_active", label="Active"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True, exclude_from_edit=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True, exclude_from_edit=True),
        # HasOne("category_author", exclude_from_list=True, exclude_from_create=True),
        HasOne("category_author", identity='staff', exclude_from_create=True, exclude_from_edit=True),
        # HasMany("products", identity="produse"),
        # HasMany("interactions", identity="interactiuni_utilizator"),
    ]

    # async def _check_form_data(self, **data):
    #     rez = await AdminSuiteCRUD.find_one_or_none(**data)
    #     if rez:
    #         return True
    #     return False

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        print("Validating category data")
        errors: Dict[str, str] = dict()

        if request['state']['action'] == RequestAction.CREATE:
            print("Validating category data => CREATE")

            if data['name'] is None or len(data['name']) < 3:
                errors['name'] = 'Invalid category Name. Must be at least 4 characters !'
            elif await AdminCategoryViewCRUD._check_form_data(name=data['name']):
                errors['name'] = 'Category with this name already exists !'
            if data['description'] is None or len(data['description']) < 10:
                errors['description'] = 'Invalid category Description. Must be at least 10 characters !'



            if len(errors) > 0:
                raise FormValidationError(errors)

        elif request['state']['action'] == RequestAction.EDIT:
            print("Validating category data => EDIT")

            current_category = data.get("name", None)
            current_category_data = await AdminCategoryViewCRUD.find_one_or_none(name=current_category)

            if not current_category_data:
                raise FormValidationError("Invalid user data")

            print(f"Validating category data => EDIT => current_category_data.id = {current_category_data.id}")





            if len(errors) > 0:
                raise FormValidationError(errors)



        # _2day_from_today = date.today() + timedelta(days=2)
        # if data["title"] is None or len(data["title"]) < 3:
        #     errors["title"] = "Ensure this value has at least 03 characters"
        # if data["text"] is None or len(data["text"]) < 10:
        #     errors["text"] = "Ensure this value has at least 10 characters"
        # if data["date"] is None or data["date"] < _2day_from_today:
        #     errors["date"] = "We need at least one day to verify your post"
        # if len(errors) > 0:
        #     raise FormValidationError(errors)



        return await super().validate(request, data)


    # def is_accessible(self, request: Request) -> bool:
    #     print("++++++++++++++++++ MY is_accessible")
    #     # print(f"++++++++++++++++++ MY is_accessible ==> request.username={request.session.get('username')}")
    #     token = request.session.get("token")
    #     decoded_token = decode_access_token(token)
    #     user = request.session.get('username')
    #     # print(f"++++++++++++++++++ MY is_accessible ==> type(user)={type(user)}")
    #     # print(f"++++++++++++++++++ MY is_accessible ==> decoded_token={decoded_token}")
    #     # print(f"++++++++++++++++++ MY is_accessible ==> decoded_token['role']={decoded_token['role']}")
    #
    #     if decoded_token['role'] == StaffRole.super_admin.value:
    #         return True
    #     return False

    async def image_create(self, data: Dict[str, Any]):
        if data['image_path'][0] is not None:
            img = data['image_path'][0]
            category_name = data['name'].replace(" ", "_")

            file_extension = Path(img.filename).suffix
            new_file_name = f"{category_name}{file_extension}"
            file_path = container_base_path / new_file_name

            # Salvăm fișierul pe disc
            async with aiofiles.open(file_path, 'wb') as buffer:
                content = await img.read()
                await buffer.write(content)

            data['image_path'] = (str(file_path), data['image_path'][1])
            print(f"create dupa Add post image => data = {data}")

        else:
            data['image_path'] = (DEFAULT_IMAGE_PATH, None)


    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        print("before_create")

        user = request.session.get('username')
        req_user = await AdminSuiteCRUD.find_one_or_none(username=user)
        setattr(obj, 'author_id', req_user.id)




    async def create(self, request: Request, data: Dict[str, Any]) -> Any:

        await self.image_create(data)

        # print(f"+-+-+-+-+ create dupa Add post image => data = {data}")

        # user = request.session.get('username')

        # print(f"+-+-+-+-+ create dupa Add post image => user = {user}")

        # req_user = await AdminSuiteCRUD.find_one_or_none(username=user)

        # data['author_id'] = req_user.id

        # print(f"+-+-+-+-+ create dupa Add post image => req_user = {req_user}")
        # print(f"+-+-+-+-+ create dupa Add post image => req_user = {req_user.id}")

        # if data['image_path'][0] is not None:
        #     img = data['image_path'][0]
        #     category_name = data['name'].replace(" ", "_")
        #
        #     file_extension = Path(img.filename).suffix
        #     new_file_name = f"{category_name}{file_extension}"
        #     file_path = container_base_path / new_file_name
        #
        #     # Salvăm fișierul pe disc
        #     async with aiofiles.open(file_path, 'wb') as buffer:
        #         content = await img.read()
        #         await buffer.write(content)
        #
        #     data['image_path'] = (str(file_path), data['image_path'][1])
        #     print(f"create dupa Add post image => data = {data}")
        #
        # else:
        #     data['image_path'] = (DEFAULT_IMAGE_PATH, None)



        return await super().create(request, data)


    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        print("before_edit")

        user = request.session.get('username')
        req_user = await AdminSuiteCRUD.find_one_or_none(username=user)
        setattr(obj, 'last_modified_by', req_user.id)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        print("edit")

        await self.image_create(data)

        return await super().edit(request, pk, data)
