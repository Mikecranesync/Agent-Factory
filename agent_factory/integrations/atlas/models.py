"""
Atlas CMMS Data Models
Pydantic models for Atlas CMMS API requests/responses
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WorkOrderCreate(BaseModel):
    """Request model for creating a work order"""
    title: str = Field(..., description="Work order title")
    description: Optional[str] = Field(None, description="Detailed description")
    priority: str = Field("MEDIUM", description="Priority: LOW, MEDIUM, HIGH, NONE")
    asset_id: Optional[int] = Field(None, alias="assetId", description="Asset ID")
    location_id: Optional[int] = Field(None, alias="locationId", description="Location ID")
    assigned_to_id: Optional[int] = Field(None, alias="assignedToId", description="User ID to assign")
    due_date: Optional[datetime] = Field(None, alias="dueDate", description="Due date")
    category_id: Optional[int] = Field(None, alias="categoryId")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "Fix Pump #3",
                "description": "Pump making unusual noise",
                "priority": "HIGH",
                "assetId": 123,
                "locationId": 45
            }
        }


class WorkOrderUpdate(BaseModel):
    """Request model for updating a work order"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # OPEN, IN_PROGRESS, ON_HOLD, COMPLETE
    priority: Optional[str] = None
    assigned_to_id: Optional[int] = Field(None, alias="assignedToId")
    due_date: Optional[datetime] = Field(None, alias="dueDate")

    class Config:
        populate_by_name = True


class WorkOrder(BaseModel):
    """Work order response model"""
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    due_date: Optional[datetime] = Field(None, alias="dueDate")
    asset: Optional[dict] = None
    location: Optional[dict] = None
    assigned_to: Optional[dict] = Field(None, alias="assignedTo")
    created_by: Optional[dict] = Field(None, alias="createdBy")

    class Config:
        populate_by_name = True


class AssetSearchRequest(BaseModel):
    """Request model for searching assets"""
    filter_fields: List[str] = Field(default=["name", "description"], alias="filterFields")
    criteria: List[dict] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class Asset(BaseModel):
    """Asset response model"""
    id: int
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = Field(None, alias="serialNumber")
    location: Optional[dict] = None
    status: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True


class AssetSummary(BaseModel):
    """Simplified asset for disambiguation"""
    id: int
    name: str
    location: Optional[str] = None
    description: Optional[str] = None


class UserCreate(BaseModel):
    """Request model for creating a user"""
    email: str
    password: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    tier: str = Field(default="beta", description="Rivet subscription tier")

    class Config:
        populate_by_name = True


class User(BaseModel):
    """User response model"""
    id: int
    email: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    role: Optional[dict] = None
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True


class AuthRequest(BaseModel):
    """Authentication request"""
    email: str
    password: str
    type: str = Field(default="EMAIL")


class AuthResponse(BaseModel):
    """Authentication response with JWT token"""
    token: str
    user: Optional[dict] = None
