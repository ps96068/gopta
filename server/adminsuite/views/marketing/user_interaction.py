
from models import InteractionTargetType, InteractionAction
from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, IntegerField,
    HasMany, RelationField,
    EnumField, DateTimeField,
    BooleanField,
)



class UserInteractionView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("user_id"),
        EnumField(
            'action',
            enum=InteractionAction,
            form_template="forms/enum.html",
            select2=False
        ),
        # RelationField("target_id"),
        EnumField(
            'target_type',
            enum=InteractionTargetType,
            form_template="forms/enum.html",
            select2=False
        ),
        DateTimeField("timestamp"),
        HasOne("client", identity="utilizatori"),
        HasOne("product", identity="produse"),
        HasOne("category", identity="categorii"),
    ]
    exclude_fields_from_list = []