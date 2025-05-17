from __future__ import annotations

from sqlalchemy import event

from models.marketing.user_activity import UserActivity

# models/marketing/signals/user_activity_signals.py
# def calculate_session_duration(mapper, connection, target):
#     if target.session_end:
#         delta = target.session_end - target.session_start
#         target.session_duration = int(delta.total_seconds())
#
#
#
#
# event.listen(UserActivity, "before_update", calculate_session_duration)
#
