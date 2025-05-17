from server.adminsuite.views.baseview import ModelView
from models import UserActivity
from server.adminsuite.fields import (
    HasOne,RelationField,
    DateTimeField, IntegerField,

)


class UserActivityView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # RelationField("user_id"),
        DateTimeField("session_start"),
        DateTimeField("session_end"),
        # "session_duration",
        # UserActivity.session_duration,
        IntegerField("session_duration", exclude_from_edit=True, exclude_from_create=True),
        HasOne("client", identity="utilizatori"),
    ]
    exclude_fields_from_list = []