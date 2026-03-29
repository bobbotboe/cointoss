from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'cointoss.db'}"
    ny_open_data_app_token: str = ""  # Optional — increases rate limits on data.ny.gov

    model_config = {"env_prefix": "COINTOSS_", "env_file": ".env"}


settings = Settings()
