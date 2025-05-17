from typing import Any, Dict
from dataclasses import dataclass
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import (
    BaseField as StarletteBaseField,
    RelationField as StarletteRelationField,
    HasOne as StarletteHasOne,
    HasMany as StarletteHasMany,
    EmailField as StarletteEmailField,
    EnumField as StarletteEnumField,
    PhoneField as StarlettePhoneField,
    URLField as StarletteURLField,
    TinyMCEEditorField as StarletteTinyMCEEditorField,
    BooleanField as StarletteBooleanField,
    TextAreaField as StarletteTextAreaField,
    ImageField as StarletteImageField,
    DateTimeField as StarletteDateTimeField,
    IntegerField as StarletteIntegerField,
    StringField as StarletteStringField,
    NumberField as StarletteNumberField,


    UploadFile as StarletteUploadFile,
    FileField as StarletteFileField,
    DateField as StarletteDateField,

)


class BaseField(StarletteBaseField):
    """
        Custom Starlette BaseField
    """

    #
    # async def serialize_value(
    #     self, request: Request, value: Any, action: RequestAction
    # ) -> Any:
    #     """Formats a value for sending to the frontend based on the current request action.
    #
    #     !!! important
    #
    #         Make sure this value is JSON Serializable for RequestAction.LIST and RequestAction.API
    #
    #     Args:
    #         request: The current request object.
    #         value: The value to format.
    #         action: The current request action.
    #
    #     Returns:
    #         Any: The formatted value.
    #     """
    #
    #     print(f"serialize_value => value: {value}")
    #
    #     return value



class NumberField(StarletteNumberField):
    """
        Custom Starlette NumberField
    """


# @dataclass
class RelationField(StarletteRelationField):
    """
        Custom Starlette RelationField
    """

class HasOne(StarletteHasOne):
    """
        Custom Starlette HasOne
    """




class HasMany(StarletteHasMany):
    """
        Custom Starlette HasMany
    """

    #
    # async def parse_form_data(
    #     self, request: Request, form_data: FormData, action: RequestAction
    # ) -> Any:
    #     print("HasMany => parse_form_data")
    #
    #     if self.multiple:
    #         return form_data.getlist(self.id)
    #     return form_data.get(self.id)
    #
    # async def serialize_value(
    #         self, request: Request, value: Any, action: RequestAction
    # ) -> dict:
    #     print("HasMany -> serialize_value")
    #
    #     return value


class EmailField(StarletteEmailField):
    """
        Custom Starlette EmailField
    """

class EnumField(StarletteEnumField):
    """
        Custom Starlette EnumField
    """


class BooleanField(StarletteBooleanField):
    """
        Custom Starlette BooleanField
    """

class TextAreaField(StarletteTextAreaField):
    """
        Custom Starlette TextAreaField
    """

class TinyMCEEditorField(StarletteTinyMCEEditorField):
    """
        Custom Starlette TinyMCEEditorField
    """

class URLField(StarletteURLField):
    """
        Custom Starlette URLField
    """

class PhoneField(StarlettePhoneField):
    """
        Custom Starlette PhoneField
    """

@dataclass
class ImageField(StarletteImageField):
    """
        Custom Starlette ImageField
    """

    async def serialize_value(
            self, request: Request, value: Any, action: RequestAction
    ) -> dict:
        print("ImagField -> serialize_value")


        print(f"ImagField -> serialize_value -> request={request}")
        print(f"ImagField -> serialize_value -> request.__dict__={request.__dict__}")
        print(f"ImagField -> serialize_value -> value={value}")
        print(f"ImagField -> serialize_value -> action={action}")
        print(f"ImagField -> serialize_value")

        scheme = request.scope['scheme']
        server = f"{request.scope['server'][0]}:{request.scope['server'][1]}"

        sanitized_value = value.replace('\\', '/')

        image_url = f"{scheme}://{server}/{sanitized_value}"

        print(f"ImagField -> serialize_value => image_url = {image_url}")

        # result: Dict = {'url': "http://127.0.0.1:8000/static/shop/blog1/default.png"}
        result: Dict = {'url': image_url}
        return result


class DateTimeField(StarletteDateTimeField):
    """
        Custom Starlette DateTimeField
    """

class IntegerField(StarletteIntegerField):
    """
        Custom Starlette IntegerField
    """

class StringField(StarletteStringField):
    """
        Custom Starlette StringField
    """