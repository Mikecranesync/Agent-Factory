"""
Configuration for Rivet KB Factory
Loads environment variables and provides centralized settings
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    Required environment variables:
    - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    - REDIS_URL
    - OLLAMA_BASE_URL
    """

    # Postgres configuration
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "rivet"
    POSTGRES_USER: str = "rivet"
    POSTGRES_PASSWORD: str = "change_me"

    # Redis configuration
    REDIS_URL: str = "redis://redis:6379/0"

    # Ollama configuration
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_LLM_MODEL: str = "mistral:latest"  # or deepseek-coder
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # Worker configuration
    WORKER_POLL_INTERVAL: int = 5  # seconds
    MAX_RETRIES: int = 3

    # Scheduler configuration
    SCHEDULER_INTERVAL: int = 3600  # 1 hour

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def POSTGRES_DSN(self) -> str:
        """PostgreSQL connection string"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


# Global settings instance
settings = Settings()
