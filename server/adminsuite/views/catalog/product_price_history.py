
from models import PriceType

from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, StringField, IntegerField,
    HasMany, URLField, TextAreaField,
    DateTimeField, RelationField, BooleanField,
    EnumField
)


class ProductPriceHistoryView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        EnumField(
            'price_type',
            enum=PriceType,
            form_template="forms/enum.html",
            select2=False
        ),
        "old_price",
        "new_price",
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("product", identity="produse"),
        HasOne("modified_by_author"),

    ]