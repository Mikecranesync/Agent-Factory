"""User management endpoints.

Handles:
- User provisioning from Stripe
- User lookup
- Telegram linking
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
import logging
from uuid import uuid4

from agent_factory.rivet_pro.database import RIVETProDatabase

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class UserProvisionRequest(BaseModel):
    """Request to provision a new user."""
    email: Optional[EmailStr] = None
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    stripe_customer_id: Optional[str] = None  # Optional for MVP
    subscription_tier: Literal["free", "beta", "basic", "pro", "enterprise"] = "beta"


class UserProvisionResponse(BaseModel):
    """Response after provisioning a user."""
    user_id: str
    atlas_user_id: Optional[str] = None
    telegram_link: str
    tier: str


class UserResponse(BaseModel):
    """User details response."""
    user_id: str
    email: str
    tier: str
    stripe_customer_id: Optional[str] = None
    telegram_id: Optional[str] = None
    atlas_user_id: Optional[str] = None
    created_at: Optional[str] = None


class TelegramLinkRequest(BaseModel):
    """Request to link Telegram account."""
    user_id: str
    telegram_user_id: int
    telegram_username: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/users/provision", response_model=UserProvisionResponse)
async def provision_user(request: UserProvisionRequest):
    """
    Provision a new user.
    
    MVP Flow (no Stripe):
    - Called when user starts Telegram bot
    - Everyone gets "beta" tier with full access
    
    Future Flow (with Stripe):
    - Called by Stripe webhook after payment
    - Tier based on subscription
    
    Flow:
    1. Create user in our database
    2. Create user in Atlas CMMS (optional)
    3. Return user info
    """
    logger.info(f"Provisioning user: {request.email} ({request.subscription_tier})")

    # Create user in database
    db = RIVETProDatabase()
    try:
        user = db.create_user(
            email=request.email,
            stripe_customer_id=request.stripe_customer_id,
            tier=request.subscription_tier
        )
        user_id = user['id']  # Use database-generated UUID
    finally:
        db.close()

    # ==========================================================================
    # TODO: Create user in Atlas CMMS (WS-1)
    # ==========================================================================
    # from agent_factory.integrations.atlas import AtlasClient
    # atlas = AtlasClient()
    # atlas_user = await atlas.create_user(
    #     email=request.email,
    #     role="technician",
    #     metadata={"stripe_id": request.stripe_customer_id}
    # )
    # atlas_user_id = atlas_user["id"]
    atlas_user_id = None  # Placeholder

    # Generate Telegram deep link
    telegram_link = f"https://t.me/RivetCEO_bot?start={user_id}"

    logger.info(f"User provisioned: {user_id}")

    return UserProvisionResponse(
        user_id=user_id,
        atlas_user_id=atlas_user_id,
        telegram_link=telegram_link,
        tier=request.subscription_tier
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user details by ID.
    """
    db = RIVETProDatabase()
    try:
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        return UserResponse(
            user_id=user['id'],
            email=user['email'] or "",
            tier=user['tier'],
            stripe_customer_id=user['stripe_customer_id'],
            telegram_id=str(user['telegram_id']) if user['telegram_id'] else None,
            atlas_user_id=user['atlas_user_id'],
            created_at=user['created_at'].isoformat() if user['created_at'] else None
        )
    finally:
        db.close()


@router.get("/users/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    """
    Get user details by email.
    """
    db = RIVETProDatabase()
    try:
        user = db.get_user_by_email(email)
        if not user:
            raise HTTPException(404, "User not found")

        return UserResponse(
            user_id=user['id'],
            email=user['email'] or "",
            tier=user['tier'],
            stripe_customer_id=user['stripe_customer_id'],
            telegram_id=str(user['telegram_id']) if user['telegram_id'] else None,
            atlas_user_id=user['atlas_user_id'],
            created_at=user['created_at'].isoformat() if user['created_at'] else None
        )
    finally:
        db.close()


@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram(telegram_id: int):
    """
    Get user details by Telegram user ID.

    Used by the Telegram bot to look up users.
    """
    db = RIVETProDatabase()
    try:
        user = db.get_user_by_telegram_id(telegram_id)
        if not user:
            raise HTTPException(404, "User not found")

        return UserResponse(
            user_id=user['id'],
            email=user['email'] or "",
            tier=user['tier'],
            stripe_customer_id=user['stripe_customer_id'],
            telegram_id=str(user['telegram_id']),
            atlas_user_id=user['atlas_user_id'],
            created_at=user['created_at'].isoformat() if user['created_at'] else None
        )
    finally:
        db.close()


@router.post("/users/from-telegram", response_model=UserProvisionResponse)
async def provision_from_telegram(telegram_user_id: int, telegram_username: Optional[str] = None):
    """
    Provision a new user from Telegram bot /start command.
    
    This is the MVP signup flow - no payment required.
    User gets full "beta" access.
    
    Called by the Telegram bot when a new user sends /start.
    """
    logger.info(f"Provisioning user from Telegram: {telegram_user_id} (@{telegram_username})")

    db = RIVETProDatabase()
    try:
        # Check if user already exists
        existing = db.get_user_by_telegram_id(telegram_user_id)
        if existing:
            return UserProvisionResponse(
                user_id=existing['id'],
                atlas_user_id=existing['atlas_user_id'],
                telegram_link=f"https://t.me/RivetCEO_bot",
                tier=existing['tier']
            )

        # Create new user
        user = db.create_user(
            telegram_id=telegram_user_id,
            telegram_username=telegram_username,
            tier="beta"
        )
        user_id = user['id']
    finally:
        db.close()

    return UserProvisionResponse(
        user_id=user_id,
        atlas_user_id=None,
        telegram_link=f"https://t.me/RivetCEO_bot",
        tier="beta"  # Everyone gets full access during beta
    )


@router.post("/users/link-telegram")
async def link_telegram_account(request: TelegramLinkRequest):
    """
    Link a Telegram account to an existing user.
    
    Called when a user starts the Telegram bot with their user ID
    from the deep link.
    """
    logger.info(f"Linking Telegram {request.telegram_user_id} to user {request.user_id}")

    db = RIVETProDatabase()
    try:
        db.update_user_telegram(
            user_id=request.user_id,
            telegram_id=request.telegram_user_id,
            telegram_username=request.telegram_username
        )
    finally:
        db.close()

    return {"status": "linked", "user_id": request.user_id}


@router.put("/users/{user_id}/tier")
async def update_user_tier(user_id: str, tier: Literal["basic", "pro", "enterprise"]):
    """
    Update a user's subscription tier.
    
    Called by Stripe webhook when subscription changes.
    """
    logger.info(f"Updating user {user_id} to tier {tier}")

    db = RIVETProDatabase()
    try:
        user = db.update_user_tier(user_id, tier)

        # TODO: Also update in Atlas if user has atlas_user_id
        # if user.get('atlas_user_id'):
        #     try:
        #         async with AtlasClient() as atlas:
        #             await atlas.update_user_tier(user['atlas_user_id'], tier)
        #     except Exception as e:
        #         logger.error(f"Failed to update Atlas tier: {e}")
        #         # Continue - Atlas sync is best-effort
    finally:
        db.close()

    return {"status": "updated", "user_id": user_id, "tier": tier}
