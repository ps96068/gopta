from starlette_admin import HasOne
from starlette_admin.contrib.sqla import ModelView


from models import RequestTypeEnum
from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, IntegerField,
    DateTimeField, RelationField,
    EnumField,
    BooleanField,
)



class UserRequestView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("user_id"),
        # RelationField("product_id"),
        # RelationField("order_id"),
        EnumField(
            'request_type',
            enum=RequestTypeEnum,
            form_template="forms/enum.html",
            select2=False
        ),
        "request_details",
        DateTimeField("created_at"),
        HasOne("client", identity="utilizatori"),
        HasOne("product", identity="produse"),
        HasOne("order", identity="comenzi"),
    ]

    exclude_fields_from_list = []