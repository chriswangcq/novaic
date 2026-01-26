"""
User API
"""

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import Optional

from .auth import get_current_user

router = APIRouter()


# ==================== Schemas ====================

class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str]
    plan: str
    created_at: str


class UsageStats(BaseModel):
    tokens_used: int
    tokens_quota: int
    requests_today: int
    last_request: Optional[str]


# ==================== Endpoints ====================

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile"""
    
    # TODO: Fetch from database
    return UserProfile(
        id=current_user["user_id"],
        email=current_user["email"],
        name="User",
        plan="free",
        created_at="2026-01-10T00:00:00Z"
    )


@router.get("/usage", response_model=UsageStats)
async def get_usage(
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Get usage statistics for current user"""
    
    # TODO: Fetch from database
    return UsageStats(
        tokens_used=1500,
        tokens_quota=10000,
        requests_today=5,
        last_request="2026-01-10T12:00:00Z"
    )


@router.put("/profile")
async def update_profile(
    name: Optional[str] = None,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    
    # TODO: Update in database
    return {"status": "ok", "message": "Profile updated"}

