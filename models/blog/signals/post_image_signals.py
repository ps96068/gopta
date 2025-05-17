from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import os
from sqlalchemy import event, select, update
from datetime import datetime, timezone

from models.blog.post_image import PostImage, DEFAULT_IMAGE_PATH




# models/blog/signals/post_image_signals.py


def ensure_single_primary(mapper, connection, target):
    """
    Dacă target.is_primary=True, resetăm celelalte imagini ale postului.
    """
    print("POST_IMAGE listeners: ensure_single_primary")

    if target.is_primary and target.post_id is not None:
        connection.execute(
            update(PostImage)
            .where(
                PostImage.post_id == target.post_id,
                PostImage.is_primary == True,  # noqa
                PostImage.id != target.id,
            )
            .values(is_primary=False)
        )
        logger.info(f"Setează toate celelalte imagini ale postării {target.post_id} ca neprincipale.")



def set_default_image_if_missing(mapper, connection, target):
    """
    Dacă image_path lipsește sau nu există pe disc, setăm imaginea implicită.
    """
    print("POST_IMAGE listeners: set_default_image_if_missing")

    if not target.image_path or not os.path.exists(os.path.join(os.getcwd(), target.image_path)):
        target.image_path = DEFAULT_IMAGE_PATH
        logger.info(f"Imaginea implicită a fost setată pentru postarea {target.post_id}.")


def delete_image_file(mapper, connection, target):
    """
    Șterge fișierul de pe disc la delete și reasignează primary dacă era imaginea principală.
    """
    print("POST_IMAGE listeners: delete_image_file")


    # 1. Ștergem fișierul fizic (dacă nu este cel implicit)
    if target.image_path and os.path.abspath(target.image_path) != os.path.abspath(DEFAULT_IMAGE_PATH):
        file_path = os.path.join(os.getcwd(), target.image_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file: {file_path}, {e}")


    # 2. Dacă ștergerea a fost pe o imagine primary, alegem alta
    if target.is_primary and target.post_id is not None:
        stmt = (
            select(PostImage)
            .where(PostImage.post_id == target.post_id)
            .where(PostImage.id != target.id)
            .order_by(PostImage.created_at.desc())
            .limit(1)
        )
        result = connection.execute(stmt).scalar_one_or_none()
        if result:
            connection.execute(
                update(PostImage)
                .where(PostImage.id == result.id)
                .values(is_primary=True)
            )
            logger.info(f"Image with ID {result.id} set to primary for post_id {target.post_id}.")




event.listen(PostImage, "before_insert", ensure_single_primary)
event.listen(PostImage, "before_update", ensure_single_primary)

event.listen(PostImage, "before_insert", set_default_image_if_missing)
event.listen(PostImage, "before_update", set_default_image_if_missing)

event.listen(PostImage, "after_delete", delete_image_file)