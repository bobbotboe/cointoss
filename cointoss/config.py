import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'cointoss.db'}"
    ny_open_data_app_token: str = ""  # Optional — increases rate limits on data.ny.gov
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    llm_model: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": "COINTOSS_", "env_file": ".env"}


settings = Settings()
