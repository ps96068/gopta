# cfg/database/db_cfg.py

"""
PostgreSQL 16 - https://console.aiven.io/account  => basinfocontact@gmail.com
"""

from pydantic import field_validator, model_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from typing_extensions import Self
from typing import Optional




class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='', extra='ignore')

    use_sqlite_db: bool
    use_postgres_db: bool
    postgres_host: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_port: Optional[int] = None

    @field_validator('use_sqlite_db', check_fields=True)
    def validate_use_sqlite_db(cls, v: bool) -> bool:
        # print(f"self.use_postgres_db : {use_postgres_db}")
        if isinstance(v, bool):
            # print("validate_use_postgres_db")
            return v
        # print("raise validate fields")
        raise ValueError("Use db flug must have value - use_sqlite_db.")


    @field_validator('use_postgres_db', check_fields=True)
    def validate_use_postgres_db(cls, v: bool, info: ValidationInfo) -> bool:
        if isinstance(v, bool):
            # print("validate_use_postgres_db")
            return v
        # print("raise validate_use_postgres_db")
        raise ValueError("Use db flug must have value - use_postgres_db.")

    @model_validator(mode='after')
    def validate_db_use(self) -> Self:
        if self.use_sqlite_db == self.use_postgres_db:
            raise ValueError("At least one db must be specified.")
        return self



    @property
    def db_url(self) -> Optional[str]:

        if None in [self.postgres_host, self.postgres_db, self.postgres_user, self.postgres_password, self.postgres_port]:
            raise ValueError("Incomplete PostgreSQL configuration.")
        else:
            return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


