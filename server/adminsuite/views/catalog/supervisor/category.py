from typing import Dict, Any
from pathlib import Path

import aiofiles
from starlette.requests import Request
from models import StaffRole
from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    IntegerField, HasMany, HasOne, ImageField,
    StringField, TextAreaField, DateTimeField,
    BooleanField
)
from server.utils import decode_access_token

DEFAULT_IMAGE_PATH = "static/shop/category/default.png"
container_base_path = Path("./static/shop/category/")
container_base_path.mkdir(parents=True, exist_ok=True)


class SupervisorCategoryView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("name"),
        TextAreaField("description", exclude_from_list=True),
        ImageField("image_path", label="Add image"),
        BooleanField("is_active", label="Active"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("category_author"),
        HasMany("products", identity="produse"),
        HasMany("interactions", identity="interactiuni_utilizator"),
    ]

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        print("Validating category data")
        errors: Dict[str, str] = dict()

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


    def is_accessible(self, request: Request) -> bool:
        print("++++++++++++++++++ MY is_accessible")
        print(f"++++++++++++++++++ MY is_accessible ==> request.username={request.session.get('username')}")
        token = request.session.get("token")
        decoded_token = decode_access_token(token)
        user = request.session.get('username')
        print(f"++++++++++++++++++ MY is_accessible ==> type(user)={type(user)}")
        print(f"++++++++++++++++++ MY is_accessible ==> decoded_token={decoded_token}")
        print(f"++++++++++++++++++ MY is_accessible ==> decoded_token['role']={decoded_token['role']}")

        if decoded_token['role'] == StaffRole.supervisor.value:
            return True
        return False



    async def create(self, request: Request, data: Dict[str, Any]) -> Any:

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


        return await super().create(request, data)
