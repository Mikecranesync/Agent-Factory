"""Work order management endpoints.

Handles:
- Work order creation from voice/text
- Work order queries
- Work order updates
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Literal, Optional, List
import logging
from datetime import datetime

from agent_factory.integrations.atlas import (
    AtlasClient,
    WorkOrderCreate as AtlasWorkOrderCreate,
    WorkOrderUpdate as AtlasWorkOrderUpdate,
    AssetSummary as AtlasAssetSummary
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class WorkOrderCreate(BaseModel):
    """Request to create a work order."""
    title: str
    description: Optional[str] = None
    asset_id: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    created_by: str  # User ID (Telegram or internal)
    source: Literal["telegram_voice", "telegram_text", "web", "api"] = "api"
    
    # Optional: from intent parsing
    equipment_type: Optional[str] = None
    fault_codes: Optional[List[str]] = None


class WorkOrderResponse(BaseModel):
    """Work order details response."""
    id: str
    title: str
    description: Optional[str] = None
    status: Literal["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]
    priority: str
    asset_id: str
    asset_name: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None


class WorkOrderUpdate(BaseModel):
    """Request to update a work order."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["OPEN", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"]] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None
    notes: Optional[str] = None


class WorkOrderListResponse(BaseModel):
    """List of work orders."""
    work_orders: List[WorkOrderResponse]
    total: int
    page: int
    per_page: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(request: WorkOrderCreate):
    """
    Create a new work order.

    This is the core endpoint called by:
    - Telegram voice handler (after transcription + intent parsing)
    - Telegram text handler
    - Web interface
    - Direct API calls

    The work order is created in Atlas CMMS.
    """
    logger.info(f"Creating work order: {request.title} for asset {request.asset_id}")

    try:
        async with AtlasClient() as atlas:
            # Create Atlas work order
            atlas_wo = await atlas.create_work_order(
                AtlasWorkOrderCreate(
                    title=request.title,
                    description=request.description or f"Created via {request.source}",
                    asset_id=int(request.asset_id),
                    priority=request.priority
                )
            )

            # TODO: Log to LangSmith for observability
            # from agent_factory.observability import log_work_order_created
            # log_work_order_created(atlas_wo.id, request.source, request.created_by)

            return WorkOrderResponse(
                id=str(atlas_wo.id),
                title=atlas_wo.title,
                description=atlas_wo.description,
                status=atlas_wo.status,
                priority=atlas_wo.priority,
                asset_id=request.asset_id,
                asset_name=atlas_wo.asset.get("name") if atlas_wo.asset else None,
                created_by=request.created_by,
                created_at=atlas_wo.created_at.isoformat(),
                updated_at=atlas_wo.updated_at.isoformat() if atlas_wo.updated_at else None
            )

    except Exception as e:
        logger.error(f"Failed to create work order in Atlas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create work order: {str(e)}"
        )


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(work_order_id: str):
    """
    Get a work order by ID.
    """
    try:
        async with AtlasClient() as atlas:
            atlas_wo = await atlas.get_work_order(int(work_order_id))

            return WorkOrderResponse(
                id=str(atlas_wo.id),
                title=atlas_wo.title,
                description=atlas_wo.description,
                status=atlas_wo.status,
                priority=atlas_wo.priority,
                asset_id=str(atlas_wo.asset.get("id")) if atlas_wo.asset else "unknown",
                asset_name=atlas_wo.asset.get("name") if atlas_wo.asset else None,
                created_by=atlas_wo.created_by.get("email") if atlas_wo.created_by else "unknown",
                created_at=atlas_wo.created_at.isoformat(),
                updated_at=atlas_wo.updated_at.isoformat() if atlas_wo.updated_at else None
            )

    except Exception as e:
        logger.error(f"Failed to fetch work order {work_order_id}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Work order not found: {work_order_id}"
        )


@router.put("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def update_work_order(work_order_id: str, request: WorkOrderUpdate):
    """
    Update a work order.

    Can update status, priority, description, or add notes.
    """
    logger.info(f"Updating work order {work_order_id}")

    try:
        async with AtlasClient() as atlas:
            atlas_wo = await atlas.update_work_order(
                int(work_order_id),
                AtlasWorkOrderUpdate(
                    title=request.title,
                    description=request.description,
                    status=request.status,
                    priority=request.priority
                )
            )

            return WorkOrderResponse(
                id=str(atlas_wo.id),
                title=atlas_wo.title,
                description=atlas_wo.description,
                status=atlas_wo.status,
                priority=atlas_wo.priority,
                asset_id=str(atlas_wo.asset.get("id")) if atlas_wo.asset else "unknown",
                asset_name=atlas_wo.asset.get("name") if atlas_wo.asset else None,
                created_by=atlas_wo.created_by.get("email") if atlas_wo.created_by else "unknown",
                created_at=atlas_wo.created_at.isoformat(),
                updated_at=atlas_wo.updated_at.isoformat() if atlas_wo.updated_at else None
            )

    except Exception as e:
        logger.error(f"Failed to update work order {work_order_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update work order: {str(e)}"
        )


@router.get("/work-orders", response_model=WorkOrderListResponse)
async def list_work_orders(
    user_id: Optional[str] = Query(None, description="Filter by user"),
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    List work orders with optional filters.

    Used by:
    - Telegram bot to show user's work orders
    - Web dashboard
    """
    try:
        async with AtlasClient() as atlas:
            # Atlas uses 0-indexed pages
            work_orders = await atlas.list_work_orders(
                user_id=int(user_id) if user_id else None,
                status=status,
                page=page - 1,
                size=per_page
            )

            return WorkOrderListResponse(
                work_orders=[
                    WorkOrderResponse(
                        id=str(wo.id),
                        title=wo.title,
                        description=wo.description,
                        status=wo.status,
                        priority=wo.priority,
                        asset_id=str(wo.asset.get("id")) if wo.asset else "unknown",
                        asset_name=wo.asset.get("name") if wo.asset else None,
                        created_by=wo.created_by.get("email") if wo.created_by else "unknown",
                        created_at=wo.created_at.isoformat(),
                        updated_at=wo.updated_at.isoformat() if wo.updated_at else None
                    )
                    for wo in work_orders
                ],
                total=len(work_orders),  # Atlas doesn't return total count in this endpoint
                page=page,
                per_page=per_page
            )

    except Exception as e:
        logger.error(f"Failed to list work orders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list work orders: {str(e)}"
        )


@router.post("/work-orders/{work_order_id}/complete")
async def complete_work_order(work_order_id: str, notes: Optional[str] = None):
    """
    Mark a work order as completed.

    Convenience endpoint for the Telegram bot.
    """
    logger.info(f"Completing work order {work_order_id}")

    try:
        async with AtlasClient() as atlas:
            await atlas.update_work_order(
                int(work_order_id),
                AtlasWorkOrderUpdate(
                    status="COMPLETE",
                    description=notes if notes else None
                )
            )

            return {"status": "completed", "work_order_id": work_order_id}

    except Exception as e:
        logger.error(f"Failed to complete work order {work_order_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete work order: {str(e)}"
        )


# =============================================================================
# ASSET ENDPOINTS (Could be separate router)
# =============================================================================

class AssetSummary(BaseModel):
    """Brief asset info for search results."""
    id: str
    name: str
    location: Optional[str] = None
    type: Optional[str] = None


@router.get("/assets", response_model=List[AssetSummary])
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search assets by name, location, or ID.

    Used by intent clarification when user says "the pump" and we need
    to ask which one.
    """
    logger.info(f"Searching assets: {q}")

    try:
        async with AtlasClient() as atlas:
            atlas_assets = await atlas.search_assets(query=q, limit=limit)

            return [
                AssetSummary(
                    id=str(asset.id),
                    name=asset.name,
                    location=asset.location,
                    type=None  # Atlas AssetSummary doesn't have type field
                )
                for asset in atlas_assets
            ]

    except Exception as e:
        logger.error(f"Failed to search assets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search assets: {str(e)}"
        )


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    """
    Get asset details by ID.
    """
    try:
        async with AtlasClient() as atlas:
            asset = await atlas.get_asset(int(asset_id))

            return {
                "id": str(asset.id),
                "name": asset.name,
                "description": asset.description,
                "model": asset.model,
                "serial_number": asset.serial_number,
                "location": asset.location,
                "status": asset.status,
                "created_at": asset.created_at.isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to fetch asset {asset_id}: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Asset not found: {asset_id}"
        )
