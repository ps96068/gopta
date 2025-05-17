

from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, DateTimeField,
    HasMany,
    EnumField,
    BooleanField, IntegerField,
    ImageField,
    # ImagField,
    ImageField, RelationField,

)




class PostEditHistoryView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        DateTimeField("changed_at", exclude_from_list=True, exclude_from_create=True),
        HasOne("post", identity="postari"),
        HasOne("staff")
    ]