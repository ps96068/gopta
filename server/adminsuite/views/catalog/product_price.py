

from models import PriceType

from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, IntegerField,
    RelationField, EnumField
)

class ProductPriceView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("product_id", exclude_from_list=True),
        EnumField(
            'price_type',
            enum=PriceType,
            form_template="forms/enum.html",
            select2=False
        ),
        "price",
        HasOne("product_price_author"),
        HasOne("product", identity="produse"),
    ]
    exclude_fields_from_list = []