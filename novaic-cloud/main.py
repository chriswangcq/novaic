"""
NovAIC Cloud Service - Main Entry Point

Provides:
- User authentication
- Subscription management
- LLM API proxy
- Usage tracking
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api import auth_router, user_router, subscription_router, llm_router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 NovAIC Cloud Service starting on {settings.host}:{settings.port}")
    
    # TODO: Initialize database connection pool
    # TODO: Initialize Anthropic client
    
    yield
    
    # Shutdown
    print("👋 NovAIC Cloud Service shutting down")
    # TODO: Close database connections


app = FastAPI(
    title="NovAIC Cloud Service",
    description="Authentication, subscription, and LLM proxy service for NovAIC",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(subscription_router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(llm_router, prefix="/api/llm", tags=["LLM"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "NovAIC Cloud Service",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/api/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )

