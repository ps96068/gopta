from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict




# ex TokenSettings
class SrvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='', extra='ignore')

    admin_tg_id: str
    admin_user: str
    admin_email: str
    admin_phone: str
    admin_password: str
    manager_tg_id: str
    manager_user: str
    manager_email: str
    manager_phone: str
    manager_password: str
    supervisor_tg_id: str
    supervisor_user: str
    supervisor_email: str
    supervisor_phone: str
    supervisor_password: str
    secret_key: str
    secret_key1: str
    secret_key2: str
    algorithm: str
    access_token_expire_minutes: int

    # @field_validator('company', mode='after', check_fields=True)
    # def validate_company(cls, v: str) -> str:
    #     if len(v) == 0:
    #         raise ValueError("company name must be specified.")
    #     return v

    @field_validator('admin_tg_id', mode='after', check_fields=True)
    def validate_admin_id(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Admin telegram ID must be specified.")
        return v

    @field_validator('admin_user', mode='after', check_fields=True)
    def validate_admin_user(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Admin user must be specified.")
        return v

    @field_validator('admin_email', mode='after', check_fields=True)
    def validate_admin_email(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Admin email must be specified.")
        return v

    @field_validator('admin_phone', mode='after', check_fields=True)
    def validate_admin_phone(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Admin phone must be specified.")
        return v

    @field_validator('admin_password', mode='after', check_fields=True)
    def validate_admin_password(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Admin password must be specified.")
        return v

    @field_validator('secret_key', mode='after', check_fields=True)
    def validate_secret_key(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("secret_key must be specified.")
        return v

    @field_validator('secret_key1', mode='after', check_fields=True)
    def validate_secret_key1(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("secret_key1 must be specified.")
        return v

    @field_validator('secret_key2', mode='after', check_fields=True)
    def validate_secret_key2(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("secret_key2 must be specified.")
        return v

    @field_validator('algorithm', mode='after', check_fields=True)
    def validate_algorithm(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("algorithm must be specified.")
        return v

    @field_validator('access_token_expire_minutes', mode='after', check_fields=True)
    def validate_access_token_expire_minutes(cls, v: str) -> str:
        if not v:
            raise ValueError("access_token_expire_minutes must be specified.")
        return v
