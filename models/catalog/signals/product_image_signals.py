from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import os
import asyncio
from sqlalchemy import event, select, update
from sqlalchemy.orm.attributes import get_history

from models.catalog.product_image import ProductImage


DEFAULT_IMAGE_PATH = "static/shop/product/prod_default.png"


# models/catalog/signals/product_image_signals.py


def enforce_single_primary(mapper, conn, target):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Dacă nu există o buclă de evenimente, creați una nouă
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Creați o sarcină asincronă fără a o aștepta
    loop.create_task(async_enforce_single_primary(mapper, conn, target))


async def async_enforce_single_primary(mapper, conn, target):
    if target.is_primary:
        await conn.execute(
            update(ProductImage)
            .where(
                ProductImage.product_id == target.product_id,
                ProductImage.is_primary == True,   # noqa
                ProductImage.id != target.id       # exclude self on update
            )
            .values(is_primary=False)
        )
    # fallback image
    if not target.image_path or not os.path.exists(os.path.join(os.getcwd(), target.image_path)):
        target.image_path = DEFAULT_IMAGE_PATH


event.listen(ProductImage, "before_insert", enforce_single_primary)
event.listen(ProductImage, "before_update", enforce_single_primary)

