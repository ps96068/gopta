from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, StringField, IntegerField,
    HasMany, URLField, TextAreaField,
    DateTimeField, RelationField, BooleanField
)


class ProductView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("name"),
        TextAreaField("description", exclude_from_list=True),
        URLField("datasheet_url", exclude_from_list=True),
        BooleanField("is_active"),
        # RelationField("category_id"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("publish_date"),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("product_author"),
        HasOne("category", identity="categorii"),
        HasMany("prices", identity="preturi_produs"),
        HasMany("interactions", identity="interactiuni_utilizator"),
        HasMany("images", identity="imagini_produs"),
        HasMany("requests", identity="cereri_utilizator"),
        HasMany("order_items", identity="itemuri_comanda"),
    ]
    exclude_fields_from_list = []