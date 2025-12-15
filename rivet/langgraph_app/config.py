"""
Configuration for Rivet application

Loads settings from environment variables.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # PostgreSQL
    POSTGRES_HOST: str = Field(default="postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="rivet", description="Database name")
    POSTGRES_USER: str = Field(default="rivet", description="Database user")
    POSTGRES_PASSWORD: str = Field(default="change_me", description="Database password")

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0", description="Redis connection URL")

    # Ollama
    OLLAMA_BASE_URL: str = Field(default="http://ollama:11434", description="Ollama API endpoint")
    OLLAMA_LLM_MODEL: str = Field(default="deepseek-r1:1.5b", description="LLM model for extraction")
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text", description="Embedding model")

    # Processing
    BATCH_SIZE: int = Field(default=10, description="Atoms per batch")
    MAX_RETRIES: int = Field(default=3, description="Max retries for failed jobs")
    TIMEOUT_SECONDS: int = Field(default=300, description="Job timeout")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def POSTGRES_DSN(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


# Singleton settings instance
settings = Settings()
