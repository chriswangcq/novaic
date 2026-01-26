"""
Subscription API
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .auth import get_current_user
from config import settings

router = APIRouter()


# ==================== Schemas ====================

class Plan(BaseModel):
    id: str
    name: str
    price: int  # Price in cents
    quota: int  # Monthly token quota
    features: List[str]


class Subscription(BaseModel):
    id: str
    plan: str
    status: str  # active, cancelled, expired
    quota: int
    used: int
    starts_at: str
    expires_at: str


# ==================== Data ====================

PLANS = [
    Plan(
        id="free",
        name="Free",
        price=0,
        quota=settings.free_quota,
        features=["10 requests per day", "Basic features"]
    ),
    Plan(
        id="pro",
        name="Pro",
        price=9900,  # ¥99
        quota=settings.pro_quota,
        features=["Unlimited requests", "3 workspaces", "Priority support"]
    ),
    Plan(
        id="pro_cloud",
        name="Pro + Cloud",
        price=14900,  # ¥149
        quota=settings.pro_quota * 2,
        features=["Everything in Pro", "Cloud sync", "Multi-device"]
    )
]


# ==================== Endpoints ====================

@router.get("/plans", response_model=List[Plan])
async def get_plans():
    """Get available subscription plans"""
    return PLANS


@router.get("/status", response_model=Subscription)
async def get_subscription_status(
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Get current subscription status"""
    
    # TODO: Fetch from database
    return Subscription(
        id="sub_123",
        plan="free",
        status="active",
        quota=settings.free_quota,
        used=1500,
        starts_at="2026-01-01T00:00:00Z",
        expires_at="2026-02-01T00:00:00Z"
    )


@router.post("/create")
async def create_subscription(
    plan_id: str,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Create or upgrade subscription.
    
    In production, this would integrate with payment provider.
    """
    
    # Validate plan
    plan = next((p for p in PLANS if p.id == plan_id), None)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # TODO: Create payment session
    # TODO: Update subscription in database
    
    return {
        "status": "ok",
        "message": f"Subscription to {plan.name} created",
        "plan": plan_id
    }


@router.post("/cancel")
async def cancel_subscription(
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Cancel current subscription"""
    
    # TODO: Update subscription status in database
    
    return {
        "status": "ok",
        "message": "Subscription will be cancelled at the end of billing period"
    }


async def check_quota(user_id: str) -> dict:
    """
    Check if user has remaining quota.
    Returns quota info or raises HTTPException if exceeded.
    """
    
    # TODO: Fetch actual quota from database
    subscription = Subscription(
        id="sub_123",
        plan="free",
        status="active",
        quota=settings.free_quota,
        used=1500,
        starts_at="2026-01-01T00:00:00Z",
        expires_at="2026-02-01T00:00:00Z"
    )
    
    if subscription.used >= subscription.quota:
        raise HTTPException(
            status_code=403,
            detail="Monthly quota exceeded. Please upgrade your plan."
        )
    
    return {
        "remaining": subscription.quota - subscription.used,
        "plan": subscription.plan
    }

