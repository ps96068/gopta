from starlette.requests import Request
from typing import Dict, Any
import aiofiles
from pathlib import Path

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


container_base_path = Path("./static/shop/blog/")
container_base_path.mkdir(parents=True, exist_ok=True)


class PostImageView(ModelView):
    fields = [
        IntegerField("id", exclude_from_create=True),
        # "post_id",
        # HasOne("post_id", identity="postari"),
        # "image",
        # "image_path",
        # ImagField("image_path"),
        ImageField("image_path", label="Add image"),
        # FileField("image"),
        # UploadFile("image_path"),
        # ImageField(name="image_path"),
        # FileField(name="image_path"),
        BooleanField("is_primary", label="Is Primary"),
        DateTimeField("create_date", exclude_from_list=True, exclude_from_create=True),
        DateTimeField("modified_date", exclude_from_list=True, exclude_from_create=True),
        HasOne("img_author"),
        HasOne("post", identity="postari"),
    ]