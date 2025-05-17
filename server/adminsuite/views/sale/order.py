from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, RelationField,
    HasMany, DateTimeField,
    EnumField,
    IntegerField,
)
from models import OrderStatus



class OrderView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        "user_id",
        EnumField(
            'status',
            enum=OrderStatus,
            form_template="forms/enum.html",
            select2=False
        ),
        # "total_amount",
        IntegerField("total_amount", exclude_from_edit=True, exclude_from_create=True),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("clients", identity="utilizatori"),
        HasMany("items", identity="itemuri_comanda"),
        HasMany("requests", identity="cereri_utilizator"),
    ]
