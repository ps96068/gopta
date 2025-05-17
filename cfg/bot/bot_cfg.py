from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='', extra='ignore')

    bot_token: str = ...

    @field_validator('bot_token', mode='after', check_fields=True)
    def validate_bot_token(cls, v: str) -> str:
        if len(v) == 0:
            raise ValueError("Bot token must be specified.")
        return v
