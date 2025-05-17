from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, IntegerField,
    HasMany, RelationField,
    EnumField, DateTimeField
)


class OrderItemView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("order_id"),
        # RelationField("product_id"),
        IntegerField("quantity"),
        "price_per_unit",
        # "total_price",
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("order", identity="comenzi"),
        HasOne("product", identity="produse"),
    ]