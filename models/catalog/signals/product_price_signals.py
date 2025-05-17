from __future__ import annotations

import asyncio
from sqlalchemy import event, select, update, func, insert
from sqlalchemy.orm.attributes import get_history

from models.catalog.product_price_history import ProductPriceHistory
from models.catalog.product_price import ProductPrice


# models/catalog/signals/product_price_signals.py



def log_price_change(mapper, conn, target):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Dacă nu există o buclă de evenimente, creați una nouă
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Creați o sarcină asincronă fără a o aștepta
    loop.create_task(async_log_price_change(mapper, conn, target))




async def async_log_price_change(mapper, conn, target):
    hist_usd = get_history(target, "price_usd")
    hist_mdl = get_history(target, "price_mdl")

    if not hist_usd.has_changes() and not hist_mdl.has_changes():
        return   # skip if no price fields changed

    await conn.execute(
        insert(ProductPriceHistory).values(
            product_id=target.product_id,
            price_type=target.price_type,
            old_usd=hist_usd.deleted[0] if hist_usd.deleted else target.price_usd,
            new_usd=target.price_usd,
            old_mdl=hist_mdl.deleted[0] if hist_mdl.deleted else target.price_mdl,
            new_mdl=target.price_mdl,
            rate_used=target.rate_used,
            changed_by=target.author_id,
            changed_at=func.now(),
        )
    )



event.listen(ProductPrice, "after_insert", log_price_change)
event.listen(ProductPrice, "after_update", log_price_change)

