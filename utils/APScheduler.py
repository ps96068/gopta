from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import update, and_
from cfg import async_session_maker
from models.blog.post import Post  # ajustează importul la structura ta

scheduler = AsyncIOScheduler(timezone="Europe/Chisinau")

@scheduler.scheduled_job("interval", minutes=5, id="activate_scheduled_posts")
async def activate_scheduled_posts():
    async with async_session_maker() as session:
        stmt = (
            update(Post)
            .where(
                and_(
                    Post.is_active.is_(False),
                    Post.publish_date <= datetime.now(timezone.utc)
                )
            )
            .values(is_active=True)
        )
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount:
            print(f"[scheduler] Activated {result.rowcount} post(s)")

def start_scheduler():
    scheduler.start()