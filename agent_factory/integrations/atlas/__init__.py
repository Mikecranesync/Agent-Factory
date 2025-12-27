"""
Atlas CMMS Integration
Python client for Atlas CMMS maintenance management system
"""

from .client import AtlasClient
from .models import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrder,
    AssetSearchRequest,
    Asset,
    AssetSummary,
    UserCreate,
    User,
    AuthRequest,
    AuthResponse
)
from .config import AtlasConfig, get_atlas_config

__all__ = [
    "AtlasClient",
    "WorkOrderCreate",
    "WorkOrderUpdate",
    "WorkOrder",
    "AssetSearchRequest",
    "Asset",
    "AssetSummary",
    "UserCreate",
    "User",
    "AuthRequest",
    "AuthResponse",
    "AtlasConfig",
    "get_atlas_config",
]

__version__ = "0.1.0"
