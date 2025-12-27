"""
Atlas CMMS API Client
Python client for interacting with Atlas CMMS REST API
"""

import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

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

logger = logging.getLogger(__name__)


class AtlasClient:
    """
    Async HTTP client for Atlas CMMS API

    Handles authentication, token management, and all CRUD operations
    for work orders, assets, and users.

    Example usage:
        ```python
        async with AtlasClient() as client:
            # Create work order
            wo = await client.create_work_order(
                WorkOrderCreate(
                    title="Fix Pump #3",
                    priority="HIGH",
                    asset_id=123
                )
            )

            # Search assets
            assets = await client.search_assets("pump")
        ```
    """

    def __init__(self, config: Optional[AtlasConfig] = None):
        """
        Initialize Atlas client

        Args:
            config: Optional AtlasConfig. If None, loads from environment.
        """
        self.config = config or get_atlas_config()
        self.client: Optional[httpx.AsyncClient] = None
        self._token: Optional[str] = self.config.jwt_token
        self._token_expires: Optional[datetime] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.request_timeout
        )
        await self._ensure_authenticated()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def _ensure_authenticated(self) -> None:
        """
        Ensure we have a valid JWT token
        Automatically refreshes if expired or missing
        """
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return  # Token still valid

        logger.info("Authenticating with Atlas CMMS...")
        auth_request = AuthRequest(
            email=self.config.admin_email,
            password=self.config.admin_password
        )

        response = await self.client.post(
            "/auth/signin",
            json=auth_request.model_dump()
        )
        response.raise_for_status()

        auth_response = AuthResponse(**response.json())
        self._token = auth_response.token
        self._token_expires = datetime.now() + timedelta(hours=23)  # Tokens typically last 24h
        logger.info("Authentication successful")

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response as dict

        Raises:
            httpx.HTTPStatusError: On HTTP errors
        """
        await self._ensure_authenticated()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.request(
                    method,
                    endpoint,
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    # Token expired, retry once after re-auth
                    logger.warning("Token expired, re-authenticating...")
                    self._token = None
                    await self._ensure_authenticated()
                    continue
                raise

            except httpx.RequestError as e:
                if attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")

    # ==================== Work Order Methods ====================

    async def create_work_order(self, data: WorkOrderCreate) -> WorkOrder:
        """
        Create a new work order

        Args:
            data: Work order creation data

        Returns:
            Created work order
        """
        response = await self._request(
            "POST",
            "/work-orders",
            json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return WorkOrder(**response)

    async def get_work_order(self, wo_id: int) -> WorkOrder:
        """
        Get work order by ID

        Args:
            wo_id: Work order ID

        Returns:
            Work order details
        """
        response = await self._request("GET", f"/work-orders/{wo_id}")
        return WorkOrder(**response)

    async def list_work_orders(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 0,
        size: int = 50
    ) -> List[WorkOrder]:
        """
        List work orders with optional filtering

        Args:
            user_id: Filter by assigned user
            status: Filter by status (OPEN, IN_PROGRESS, etc.)
            page: Page number (0-indexed)
            size: Page size

        Returns:
            List of work orders
        """
        criteria = []
        if user_id:
            criteria.append({"field": "assignedTo.id", "operation": "eq", "value": str(user_id)})
        if status:
            criteria.append({"field": "status", "operation": "eq", "value": status})

        response = await self._request(
            "POST",
            "/work-orders/search",
            json={
                "filterFields": [],
                "criteria": criteria,
                "page": page,
                "size": size
            }
        )

        return [WorkOrder(**wo) for wo in response.get("content", [])]

    async def update_work_order(self, wo_id: int, data: WorkOrderUpdate) -> WorkOrder:
        """
        Update work order

        Args:
            wo_id: Work order ID
            data: Update data

        Returns:
            Updated work order
        """
        response = await self._request(
            "PATCH",
            f"/work-orders/{wo_id}",
            json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return WorkOrder(**response)

    async def delete_work_order(self, wo_id: int) -> None:
        """
        Delete work order

        Args:
            wo_id: Work order ID
        """
        await self._request("DELETE", f"/work-orders/{wo_id}")

    # ==================== Asset Methods ====================

    async def get_asset(self, asset_id: int) -> Asset:
        """
        Get asset by ID

        Args:
            asset_id: Asset ID

        Returns:
            Asset details
        """
        response = await self._request("GET", f"/assets/{asset_id}")
        return Asset(**response)

    async def search_assets(self, query: str, limit: int = 10) -> List[AssetSummary]:
        """
        Search assets by name/description

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            List of matching assets (simplified for disambiguation)
        """
        search_request = AssetSearchRequest(
            filter_fields=["name", "description"],
            criteria=[
                {
                    "field": "name",
                    "operation": "contains",
                    "value": query
                }
            ]
        )

        response = await self._request(
            "POST",
            "/assets/search",
            json=search_request.model_dump(by_alias=True)
        )

        assets = [Asset(**asset) for asset in response.get("content", [])[:limit]]

        # Convert to simplified AssetSummary
        return [
            AssetSummary(
                id=asset.id,
                name=asset.name,
                location=asset.location.get("name") if asset.location else None,
                description=asset.description
            )
            for asset in assets
        ]

    # ==================== User Methods ====================

    async def create_user(self, email: str, tier: str, password: Optional[str] = None) -> User:
        """
        Create user in Atlas CMMS

        Args:
            email: User email
            tier: Rivet subscription tier (beta, pro, enterprise)
            password: Password (auto-generated if not provided)

        Returns:
            Created user
        """
        if not password:
            # Generate secure random password
            import secrets
            password = secrets.token_urlsafe(16)

        user_data = UserCreate(
            email=email,
            password=password,
            first_name=email.split("@")[0],  # Extract from email
            last_name=tier.capitalize(),  # Use tier as last name for now
            tier=tier
        )

        response = await self._request(
            "POST",
            "/auth/signup",
            json=user_data.model_dump(by_alias=True)
        )

        # Response format: {"success": true, "message": "...", "user": {...}}
        if response.get("success"):
            return User(**response["user"])
        else:
            raise ValueError(f"User creation failed: {response.get('message')}")

    async def get_user(self, user_id: int) -> User:
        """
        Get user by ID (requires admin permissions)

        Args:
            user_id: User ID

        Returns:
            User details
        """
        response = await self._request("GET", f"/users/{user_id}")
        return User(**response)

    # ==================== Health Check ====================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Atlas CMMS API health

        Returns:
            Health status dict
        """
        try:
            await self._ensure_authenticated()
            return {
                "status": "healthy",
                "authenticated": True,
                "base_url": self.config.base_url
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "authenticated": False,
                "error": str(e)
            }
