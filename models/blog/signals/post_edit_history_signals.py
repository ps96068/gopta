from __future__ import annotations

import logging

from sqlalchemy.orm.attributes import get_history

logger = logging.getLogger(__name__)

import os
from sqlalchemy import event, insert
from datetime import datetime, timezone

from models.blog.post import Post
from models.blog.post_edit_history import PostEditHistory, ModificationTypeEnum





# models/blog/signals/post_edit_history_signals.py

def add_edit_history(mapper, connection, target: Post):
    print("POST listeners: add_edit_history")

    # Obținem textul anterior modificării
    hist = get_history(target, "content")
    old_content = hist.deleted[0] if hist.deleted else None

    history_row = {
        "post_id":          target.id,
        "changed_by":       target.modified_by,
        "modification_type": ModificationTypeEnum.edited.value,
        "old_content":      old_content,
        # created_at va veni din CreatedAtMixin (func.now())
    }

    connection.execute(
        insert(PostEditHistory.__table__),
        [history_row]
    )

# Înregistrare listener (propagate=True pentru a prinde și subclasele)
event.listen(Post, "before_update", add_edit_history, propagate=True)

