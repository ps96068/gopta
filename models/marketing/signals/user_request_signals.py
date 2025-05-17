from __future__ import annotations

from sqlalchemy import event

from models import UserRequest, RequestTypeEnum



# models/marketing/signals/user_request_signals.py

# async def validate_before_insert(mapper, connection, target):
#     if target.request_type == RequestTypeEnum.product and not target.product_id:
#         raise ValueError("Pentru request_type='product', product_id trebuie să fie setat.")
#     if target.request_type == RequestTypeEnum.order and not target.order_id:
#         raise ValueError("Pentru request_type='order', order_id trebuie să fie setat.")
#     if target.request_type == RequestTypeEnum.general and (target.product_id or target.order_id):
#         raise ValueError("Pentru request_type='general', product_id și order_id trebuie să fie NULL.")
#
#
# event.listen(UserRequest, "before_insert", validate_before_insert)

