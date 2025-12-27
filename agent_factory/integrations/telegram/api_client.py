"""API client for Telegram bot to call backend work order API."""

import os
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime


class RivetAPIClient:
    """
    Client for Telegram bot to interact with WS-1 backend API.

    Handles:
    - Work order creation from voice/text messages
    - Asset search for equipment disambiguation
    - Work order status updates
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: Base URL of backend API (defaults to env var or localhost)
        """
        self.base_url = base_url or os.getenv("RIVET_API_URL", "http://localhost:8000")
        self.timeout = 30.0  # seconds

    async def create_work_order(
        self,
        title: str,
        asset_id: str,
        description: Optional[str] = None,
        priority: str = "MEDIUM",
        created_by: str = "telegram_user",
        source: str = "telegram_voice",
        equipment_type: Optional[str] = None,
        fault_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a work order via API.

        Args:
            title: Work order title (e.g., "Motor overheating")
            asset_id: Asset/equipment ID
            description: Detailed description
            priority: LOW, MEDIUM, HIGH, CRITICAL
            created_by: User ID (Telegram user ID)
            source: telegram_voice, telegram_text, etc.
            equipment_type: Optional equipment type from intent
            fault_codes: Optional fault codes from intent

        Returns:
            Work order response dict with 'id', 'status', etc.

        Example:
            >>> client = RivetAPIClient()
            >>> wo = await client.create_work_order(
            ...     title="Motor M1 overheating",
            ...     asset_id="MOTOR-001",
            ...     priority="HIGH",
            ...     created_by="telegram_12345"
            ... )
            >>> print(wo['id'])
            "WO-1234567890"
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/work-orders",
                json={
                    "title": title,
                    "description": description,
                    "asset_id": asset_id,
                    "priority": priority,
                    "created_by": created_by,
                    "source": source,
                    "equipment_type": equipment_type,
                    "fault_codes": fault_codes or []
                }
            )

            response.raise_for_status()
            return response.json()

    async def search_assets(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search assets by name/location/ID.

        Used for equipment disambiguation when user says "the pump"
        and we need to ask which one.

        Args:
            query: Search query (equipment name, type, location)
            limit: Max results to return

        Returns:
            List of asset dicts with 'id', 'name', 'location', 'type'

        Example:
            >>> assets = await client.search_assets("pump")
            >>> for asset in assets:
            ...     print(f"{asset['name']} ({asset['location']})")
            "Cooling Water Pump (Building A)"
            "Process Pump (Building B)"
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/assets",
                params={"q": query, "limit": limit}
            )

            response.raise_for_status()
            return response.json()

    async def get_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """
        Get work order details by ID.

        Args:
            work_order_id: Work order ID

        Returns:
            Work order dict
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/work-orders/{work_order_id}"
            )

            response.raise_for_status()
            return response.json()

    async def list_user_work_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        List work orders for a user.

        Args:
            user_id: Telegram user ID
            status: Optional filter (OPEN, IN_PROGRESS, etc.)
            page: Page number
            per_page: Results per page

        Returns:
            Dict with 'work_orders' list, 'total', 'page', 'per_page'
        """
        params = {
            "user_id": user_id,
            "page": page,
            "per_page": per_page
        }

        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/work-orders",
                params=params
            )

            response.raise_for_status()
            return response.json()

    async def complete_work_order(
        self,
        work_order_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark work order as completed.

        Args:
            work_order_id: Work order ID
            notes: Optional completion notes

        Returns:
            Response dict with status
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/work-orders/{work_order_id}/complete",
                params={"notes": notes} if notes else {}
            )

            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """
        Check if API is reachable.

        Returns:
            True if API is up, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
