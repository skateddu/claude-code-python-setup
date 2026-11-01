"""Application settings loaded from the environment."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration, validated once when the app is created."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "My App"
    database_url: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "my-app"
    access_token_expire_minutes: int = 30
    allowed_origins: list[str] = ["http://localhost:3000"]
