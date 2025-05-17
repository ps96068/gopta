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

from server.models import StaffRole, Category
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
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        # HasOne("category_author", exclude_from_list=True, exclude_from_create=True),
        HasOne("category_author", identity='staff', exclude_from_create=True),
        # HasMany("products", identity="produse"),
        # HasMany("interactions", identity="interactiuni_utilizator"),
    ]

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

        return await super().validate(request, data)



