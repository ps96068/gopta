from __future__ import annotations

import os
from sqlalchemy import event, select, update
from sqlalchemy.orm.attributes import get_history

from models.catalog.product_image import ProductImage


def receive_before_insert(mapper, connection, target):
    """ "listen for the 'before_insert' event" """

    print("ProductImage - receive_before_insert")

    print(f"ProductImage - receive_before_insert => mapper = {mapper}")
    print(f"ProductImage - receive_before_insert => connection = {connection}")
    print(f"ProductImage - receive_before_insert => target = {target}")
    print(f"ProductImage - receive_before_insert => target.post_id = {target.product_id}")
    print(f"ProductImage - receive_before_insert => target.image = {target.image}")


    if target.product_id:
        # product_id = str(target.product_id)
        product_id = f"product-{target.product_id}"
    else:
        product_id = 'undefined'

    print(f"ProductImage - receive_before_insert => post_id = {product_id}")


    # set_current_storage(
    #     path="./static/shop/product",
    #     storage_id=product_id
    # )



    print("ProductImage - Inapoi in <receive_before_insert> din <set_current_storage>")



event.listen(ProductImage, "before_insert", receive_before_insert)