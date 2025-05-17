from __future__ import annotations

import os
from datetime import datetime
import shutil
import aiofiles
from pathlib import Path
from sqlalchemy import ForeignKey, String, Index, Boolean, Integer, UniqueConstraint, Column, event, select, update
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates, object_session, Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
# from libcloud.storage.drivers.local import LocalStorageDriver
# from sqlalchemy_file import FileField, ImageField
# from sqlalchemy_file.storage import StorageManager
# from sqlalchemy_imageattach.entity import Image, image_attachment
from fastapi import HTTPException

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped


from cfg import Base
from models.base import CreatedAtMixin, UpdatedAtMixin
from models.blog.post import Post
from models.user.staff import Staff

# from models.fields import PostImageField, MyFileField
# from cfg import async_session_maker





# container_base_path = "./static/shop/blog"

# container_base_path1 = Path("./static/shop/blog1/")
# container_base_path1.mkdir(parents=True, exist_ok=True)

# Definim calea implicită pentru imagine
DEFAULT_IMAGE_PATH = os.path.join("static", "blog", "post_default.png")


# models/blog/post_image.py

class PostImage(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "post_images"
    __table_args__ = (
        UniqueConstraint("post_id", "is_primary", name="uix_post_image_primary"),
        Index("ix_post_images_post", "post_id"),
        Index("ix_post_images_author", "author_id"),
    )

    # ---------- Coloane ----------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_path: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default=DEFAULT_IMAGE_PATH,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ---------- Relații ----------
    img_author: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[author_id],
        back_populates="img_author",
    )
    post: Mapped["Post"] = relationship(
        "Post",
        foreign_keys=[post_id],
        back_populates="images",
    )

    # ---------- Validatori ----------
    @validates("image_path")
    def _validate_image_path(self, key: str, value: str) -> str:
        if not value or not value.strip():
            return DEFAULT_IMAGE_PATH
        # Dacă nu există fișierul, revenim la implicit
        if not os.path.exists(os.path.join(os.getcwd(), value)):
            return DEFAULT_IMAGE_PATH
        return value

    def __repr__(self) -> str:
        return f"<PostImage(id={self.id}, post_id={self.post_id}, primary={self.is_primary})>"


# Eveniment pentru adăugare sau editare - asigurare că există o singură imagine primary
# @event.listens_for(PostImage, "before_insert")
# @event.listens_for(PostImage, "before_update")
# def ensure_single_primary(mapper, connection, target):
#     if target.is_primary:  # Doar dacă target.is_primary este True
#         # Actualizează toate celelalte înregistrări cu is_primary=False
#         connection.execute(
#             update(PostImage)
#             .where(PostImage.post_id == target.post_id)
#             .where(PostImage.is_primary == True)
#             .where(PostImage.id != target.id)  # Exclude înregistrarea curentă
#             .values(is_primary=False)
#         )
#         print(f"Ensured single primary for post_id={target.post_id}")

# Eveniment pentru setarea imaginii implicite
# @event.listens_for(PostImage, "before_insert")
# @event.listens_for(PostImage, "before_update")
# def set_default_image_if_missing(mapper, connection, target):
#     if not target.image_path or not os.path.exists(os.path.join(os.getcwd(), target.image_path)):
#         target.image_path = DEFAULT_IMAGE_PATH
#         print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")


# Eveniment pentru ștergerea fișierului după eliminare
# @event.listens_for(PostImage, "after_delete")
# def delete_image_file(mapper, connection, target):
#     # Verificăm dacă fișierul asociat trebuie șters
#     if target.image_path and os.path.abspath(target.image_path) != os.path.abspath(DEFAULT_IMAGE_PATH):
#         file_path = os.path.join(os.getcwd(), target.image_path)  # Cale absolută
#         if os.path.exists(file_path):
#             try:
#                 os.remove(file_path)
#                 print(f"File deleted: {file_path}")
#             except Exception as e:
#                 print(f"Error deleting file: {file_path}, {e}")
#         else:
#             print(f"File does not exist: {file_path}")
#     else:
#         print("Default image not deleted.")
#
#     # Dacă imaginea ștearsă este primary, găsim imaginea precedentă
#     if target.is_primary:
#         stmt = (
#             select(PostImage)
#             .where(PostImage.post_id == target.post_id)  # Același post_id
#             .where(PostImage.id < target.id)  # Imaginea precedentă
#             .order_by(PostImage.id.desc())  # În ordine descrescătoare după id
#             .limit(1)  # Selectăm doar o înregistrare
#         )
#         result = connection.execute(stmt).first()  # Executăm query-ul
#
#         if result:  # Dacă găsim o imagine precedentă
#             prv_image = result[0]  # Extragem obiectul PostImage
#             prev_image_id = prv_image.id  # Extragem id-ul
#             update_stmt = (
#                 update(PostImage)
#                 .where(PostImage.id == prev_image_id)  # Actualizăm doar imaginea precedentă
#                 .values(is_primary=True)
#             )
#             connection.execute(update_stmt)
#             print(f"Image with ID {prev_image_id} set to primary.")
