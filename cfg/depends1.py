""" cfg/depends.py"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from .loader import cfg_db


class Base(DeclarativeBase):
    pass


db_url = cfg_db()
print(f"db_url = {db_url}")

engine = create_async_engine(
    db_url,
    pool_size=7,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=True
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
