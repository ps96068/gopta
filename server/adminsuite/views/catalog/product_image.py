from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, IntegerField,
    RelationField, BooleanField,
    DateTimeField
)


class ProductImageView(ModelView):

    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("product_id", exclude_from_list=True),
        # "image",
        BooleanField("is_primary"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("product", identity="produse"),
        HasOne("product_image_author"),
    ]
