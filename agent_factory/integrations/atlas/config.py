"""
Atlas CMMS Configuration
Connection settings and credentials for Atlas CMMS API
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class AtlasConfig(BaseSettings):
    """Atlas CMMS connection configuration"""

    # API Base URL
    base_url: str = Field(
        default="http://localhost:8080",
        description="Atlas CMMS API base URL"
    )

    # Admin Credentials (for provisioning)
    admin_email: str = Field(
        ...,
        description="Atlas admin email for API access"
    )
    admin_password: str = Field(
        ...,
        description="Atlas admin password"
    )

    # JWT Token (cached)
    jwt_token: str | None = Field(
        default=None,
        description="Cached JWT token"
    )

    # Timeout settings
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )

    # Retry settings
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )

    class Config:
        env_file = ".env"
        env_prefix = "ATLAS_"
        case_sensitive = False
        extra = "ignore"


def get_atlas_config() -> AtlasConfig:
    """
    Load Atlas configuration from environment variables

    Required env vars:
    - ATLAS_BASE_URL: http://72.60.175.144:8080 (or localhost:8080 for dev)
    - ATLAS_ADMIN_EMAIL: admin@example.com
    - ATLAS_ADMIN_PASSWORD: admin_password

    Returns:
        AtlasConfig: Configuration object
    """
    return AtlasConfig()


# Example .env configuration:
"""
# Atlas CMMS Configuration
ATLAS_BASE_URL=http://72.60.175.144:8080
ATLAS_ADMIN_EMAIL=admin@rivet.com
ATLAS_ADMIN_PASSWORD=secure_admin_password
"""
