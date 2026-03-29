from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'cointoss.db'}"
    ny_open_data_app_token: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"


settings = Settings()
