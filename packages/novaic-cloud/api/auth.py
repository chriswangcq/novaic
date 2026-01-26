"""
Authentication API
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

from config import settings

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Schemas ====================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: str


# ==================== Helper Functions ====================

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=settings.jwt_expire_days)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


# ==================== Dependencies ====================

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to get current user from JWT token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization[7:]
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== Endpoints ====================

@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    - Creates user account
    - Sets up free subscription
    - Returns user info
    """
    # TODO: Check if email already exists in database
    # TODO: Create user in database
    # TODO: Create free subscription
    
    # Placeholder response
    return UserResponse(
        id="user_" + str(hash(request.email))[:8],
        email=request.email,
        name=request.name,
        plan="free"
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login and get access token.
    
    - Validates credentials
    - Returns JWT token
    """
    # TODO: Verify user exists and password matches
    # For now, accept any login
    
    user_id = "user_" + str(hash(request.email))[:8]
    token = create_access_token(user_id, request.email)
    
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_days * 24 * 3600
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token"""
    token = create_access_token(
        current_user["user_id"],
        current_user["email"]
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_days * 24 * 3600
    )


@router.post("/logout")
async def logout():
    """Logout (client should discard token)"""
    return {"status": "ok", "message": "Logged out"}
