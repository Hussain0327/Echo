from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Echo"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: str = ""

    # LLM - DeepSeek uses OpenAI-compatible API
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # DeepSeek configuration
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # or "deepseek-reasoner" for reasoning tasks

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Authentication
    API_KEY: str = ""  # Set via environment variable for production
    REQUIRE_AUTH: bool = False  # Enable in production

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 20

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # S3 Data Lake Configuration
    S3_BUCKET_NAME: str = ""
    S3_RAW_PREFIX: str = "raw/"
    S3_STAGING_PREFIX: str = "staging/"
    S3_ARCHIVE_PREFIX: str = "archive/"

    # Redshift Configuration
    REDSHIFT_HOST: str = ""
    REDSHIFT_PORT: int = 5439
    REDSHIFT_USER: str = ""
    REDSHIFT_PASSWORD: str = ""
    REDSHIFT_DATABASE: str = ""
    REDSHIFT_SCHEMA: str = "public"
    USE_REDSHIFT: bool = False  # Toggle between PostgreSQL and Redshift

    # CORS
    CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle both comma-separated and JSON array strings
            if v.strip().startswith("["):
                import json

                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
