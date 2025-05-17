from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog.exchange_rate import ExchangeRate
from models.user.staff import Staff, StaffRole
# from tgbot.bot import bot  # instanța Aiogram creată în tgbot/__init__.py

scheduler = AsyncIOScheduler(timezone="Europe/Chisinau")


@scheduler.scheduled_job("cron", hour=11, minute=0, misfire_grace_time=3600)
async def rate_sanity_check():
    """
    La ora 11:00 verifică dacă există curs USD→MDL pentru data curentă.
    Dacă lipsește, trimite mesaj de alertă tuturor staff-ilor cu rol 'super_admin'.
    """
    async with AsyncSession() as session:
        # 1️⃣ Există rând pentru data curentă?
        today = date.today()
        rate_row = await session.get(ExchangeRate, today)

        if rate_row:
            # Cursul este introdus → nimic de făcut
            return

        # 2️⃣ Selectăm toți super adminii cu telegram_id ne-null
        result = await session.scalars(
            select(Staff.telegram_id).where(
                Staff.role == StaffRole.super_admin,
                Staff.telegram_id.is_not(None),
                Staff.is_active == True,   # noqa
            )
        )
        recipients = [tg_id for tg_id in result if tg_id]

        # 3️⃣ Trimitem mesaj
        message = (
            f"⚠️ Cursul USD→MDL pentru {today:%d-%m-%Y} nu a fost adăugat.\n"
            "Te rog să îl introduci în dashboard la secțiunea 'Curs valutar'."
        )
        for tg_id in recipients:
            try:
                # await bot.send_message(tg_id, message)
                print(f"Sent rate alert to {tg_id}: {message}")
            except Exception as e:
                # opțional: log.error(f"Cannot send rate alert to {tg_id}: {e}")
                pass