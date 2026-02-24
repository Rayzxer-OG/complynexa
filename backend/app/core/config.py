"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Compliance Tracker"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/compliance_tracker"
    database_echo: bool = False  # Set True to log SQL statements

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Uploads (local storage for uploaded documents)
    upload_dir: str = "uploads"

    # AWS (for Textract; loaded from .env and passed to boto3)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    # S3 bucket for multi-page PDF extraction (async Textract). Required for PDFs with more than one page.
    aws_s3_bucket: str = ""

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # OpenAI (for LLM compliance field extraction)
    openai_api_key: str = ""

    # SMTP (for reminder emails)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    # Recipient for reminder emails
    smtp_to: str = ""


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
