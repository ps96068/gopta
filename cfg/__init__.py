# cfg/__init__.py

from .depends import Base, get_db, engine, async_session_maker, db_url, get_db_context, close_db_connections
from .loader import cfg_db, cfg_bot, cfg_srv
from .mixins import CreatedAtMixin, UpdatedAtMixin, IsActiveMixin


ENV = cfg_srv()
SECRET_KEY: str = ENV["secret_key"]
ALGORITHM: str = ENV["algorithm"]


