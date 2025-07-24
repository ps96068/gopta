""" cfg/depends.py"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncio
from contextlib import asynccontextmanager

from .loader import cfg_db


class Base(DeclarativeBase):
    pass


db_url = cfg_db()
print(f"db_url = {db_url}")

# Configurație optimizată pentru pool
engine = create_async_engine(
    db_url,
    # Redus pool_size pentru a evita epuizarea conexiunilor
    pool_size=5,  # Redus de la 7
    max_overflow=5,  # Redus de la 10
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,  # Dezactivează echo pentru producție
    # Adaugă pentru debugging
    connect_args={
        "server_settings": {"jit": "off"},
        "command_timeout": 60,
    }
)

# Session maker cu configurație optimizată
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,  # Evită flush-uri automate
    autocommit=False
)


# Generator optimizat pentru sesiuni
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Funcție helper pentru cleanup
async def close_db_connections():
    """Închide toate conexiunile la DB."""
    await engine.dispose()


# Context manager pentru operații DB în afara request-urilor
@asynccontextmanager
async def get_db_context():
    """Context manager pentru operații DB standalone."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Funcție helper pentru cleanup
async def close_db_connections():
    """Închide toate conexiunile la DB."""
    await engine.dispose()