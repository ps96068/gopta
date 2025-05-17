from server.adminsuite.views.baseview import ModelView

from server.adminsuite.fields import (
    HasOne, IntegerField,
    HasMany, RelationField,
    EnumField, DateTimeField
)

from models import OrderStatus






class OrderStatusHistoryView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        EnumField(
            'old_status',
            enum=OrderStatus,
            form_template="forms/enum.html",
            select2=False
        ),
        EnumField(
            'new_status',
            enum=OrderStatus,
            form_template="forms/enum.html",
            select2=False
        ),
        DateTimeField("changed_at", exclude_from_list=True, exclude_from_create=True),
        HasOne("order", identity="comenzi"),
        HasOne("changed_by_user"),
    ]