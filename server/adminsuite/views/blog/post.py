from models import Post


from server.adminsuite.views.baseview import ModelView
from server.adminsuite.fields import (
    HasOne, TinyMCEEditorField,
    HasMany, IntegerField,
    EnumField, StringField,
    BooleanField, DateTimeField,
)



class PostView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        StringField("title"),
        TinyMCEEditorField("content", exclude_from_list=True),
        BooleanField("is_active"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("publish_date"),
        DateTimeField("modified_at", exclude_from_list=True, exclude_from_create=True),
        HasOne("post_author",),
        HasMany("images", identity="imagini_postare"),
        HasMany("edit_history", identity="postari_istorie"),
        HasMany("interactions", identity="interactiuni_utilizator"),
    ]