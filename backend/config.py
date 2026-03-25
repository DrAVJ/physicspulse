from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://physicsuser:physicspass@localhost:5432/physicspulse"
    openai_api_key: str = ""
    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()