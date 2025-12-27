"""Manual management endpoints for RIVET backend.

Handles:
- Manual upload and indexing
- Manual search (by query, manufacturer, component family)
- Manual gap tracking
- Manual listing
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import logging
from pathlib import Path
import tempfile

from agent_factory.rivet_pro.database import RIVETProDatabase
from agent_factory.knowledge.manual_indexer import ManualIndexer
from agent_factory.knowledge.manual_search import ManualSearchService
from agent_factory.observability.langsmith_config import trace_endpoint

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class ManualUploadResponse(BaseModel):
    """Response after uploading a manual."""
    manual_id: str
    title: str
    manufacturer: str
    component_family: str
    page_count: int
    indexed: bool


class ManualSearchRequest(BaseModel):
    """Request to search manuals."""
    query: str
    manufacturer: Optional[str] = None
    component_family: Optional[str] = None
    top_k: int = 5


class ManualSearchResult(BaseModel):
    """Individual manual search result."""
    manual_id: str
    title: str
    manufacturer: str
    component_family: str
    snippet: str
    score: float


class ManualSearchResponse(BaseModel):
    """Response from manual search."""
    query: str
    results: List[ManualSearchResult]
    total_found: int


class ManualSummary(BaseModel):
    """Manual summary for listing."""
    manual_id: str
    title: str
    manufacturer: str
    component_family: str
    indexed_at: Optional[str] = None


class ManualGap(BaseModel):
    """Missing manual gap record."""
    manufacturer: str
    component_family: str
    request_count: int
    model_pattern: Optional[str] = None
    first_requested_at: Optional[str] = None
    last_requested_at: Optional[str] = None


class ManualGapsResponse(BaseModel):
    """Response from manual gaps endpoint."""
    gaps: List[ManualGap]
    total_gaps: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/upload", response_model=ManualUploadResponse)
@trace_endpoint
async def upload_manual(
    file: UploadFile = File(...),
    title: str = Form(...),
    manufacturer: str = Form(...),
    component_family: str = Form(...),
    document_type: str = Form("user_manual")
):
    """
    Upload and index a manual PDF.

    Args:
        file: PDF file upload
        title: Manual title
        manufacturer: Manufacturer name
        component_family: Component family (VFD, PLC, etc.)
        document_type: Document type (user_manual, installation_guide, etc.)

    Returns:
        ManualUploadResponse with manual_id and indexing status
    """
    logger.info(f"Uploading manual: {title} ({manufacturer})")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Index manual
        indexer = ManualIndexer()
        manual_id = indexer.index_manual(
            file_path=temp_path,
            title=title,
            manufacturer=manufacturer,
            component_family=component_family,
            document_type=document_type
        )

        # Get manual details
        db = RIVETProDatabase()
        manual_details = db.search_manuals()
        manual = next((m for m in manual_details if str(m['id']) == manual_id), None)

        if not manual:
            raise HTTPException(status_code=500, detail="Failed to retrieve indexed manual")

        return ManualUploadResponse(
            manual_id=manual_id,
            title=title,
            manufacturer=manufacturer,
            component_family=component_family,
            page_count=manual.get('page_count', 0),
            indexed=True
        )

    except Exception as e:
        logger.error(f"Manual upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp file
        try:
            Path(temp_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {e}")


@router.post("/search", response_model=ManualSearchResponse)
@trace_endpoint
async def search_manuals(request: ManualSearchRequest):
    """
    Search equipment manuals.

    Args:
        request: Search parameters (query, filters, top_k)

    Returns:
        ManualSearchResponse with matching results
    """
    logger.info(f"Searching manuals: query='{request.query}'")

    service = ManualSearchService()
    results = service.search(
        query=request.query,
        manufacturer=request.manufacturer,
        component_family=request.component_family,
        top_k=request.top_k
    )

    return ManualSearchResponse(
        query=request.query,
        results=[
            ManualSearchResult(
                manual_id=r['manual_id'],
                title=r['title'],
                manufacturer=r['manufacturer'],
                component_family=r['component_family'],
                snippet=r['snippet'],
                score=r['score']
            )
            for r in results
        ],
        total_found=len(results)
    )


@router.get("/gaps", response_model=ManualGapsResponse)
@trace_endpoint
async def get_manual_gaps(limit: int = 10):
    """
    Get top requested missing manuals.

    Args:
        limit: Max number of gaps to return

    Returns:
        ManualGapsResponse with gap records
    """
    logger.info(f"Fetching manual gaps (limit={limit})")

    service = ManualSearchService()
    gaps = service.get_manual_gaps(limit=limit)

    return ManualGapsResponse(
        gaps=[
            ManualGap(
                manufacturer=g['manufacturer'],
                component_family=g['component_family'],
                request_count=g['request_count'],
                model_pattern=g.get('model_pattern'),
                first_requested_at=g.get('first_requested_at'),
                last_requested_at=g.get('last_requested_at')
            )
            for g in gaps
        ],
        total_gaps=len(gaps)
    )


@router.get("/list", response_model=List[ManualSummary])
@trace_endpoint
async def list_manuals(
    manufacturer: Optional[str] = None,
    component_family: Optional[str] = None
):
    """
    List all indexed manuals.

    Args:
        manufacturer: Filter by manufacturer
        component_family: Filter by component family

    Returns:
        List of ManualSummary objects
    """
    logger.info(f"Listing manuals: mfr={manufacturer}, family={component_family}")

    service = ManualSearchService()
    manuals = service.list_all_manuals(
        manufacturer=manufacturer,
        component_family=component_family
    )

    return [
        ManualSummary(
            manual_id=m['manual_id'],
            title=m['title'],
            manufacturer=m['manufacturer'],
            component_family=m['component_family'],
            indexed_at=m.get('indexed_at')
        )
        for m in manuals
    ]


@router.get("/{manual_id}")
@trace_endpoint
async def get_manual_details(manual_id: str):
    """
    Get details for a specific manual.

    Args:
        manual_id: Manual UUID

    Returns:
        Manual details
    """
    logger.info(f"Fetching manual details: {manual_id}")

    service = ManualSearchService()
    details = service.get_manual_details(manual_id)

    if not details:
        raise HTTPException(status_code=404, detail=f"Manual not found: {manual_id}")

    return details
