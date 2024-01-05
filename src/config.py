from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Authentication
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 6000

    # Database
    database_url: str = "sqlite:///moon-api.sqlite3"
    media_dir: str = (Path.cwd() / "data").absolute().__str__()

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
