"""
NovAIC Agent - LLM Agent 服务

只负责：
- LLM 对话
- Tool Calling
- 调用 Executor API 执行操作

不包含执行逻辑，执行由 Executor 服务负责。
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from api.vnc_routes import router as vnc_router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    print(f"🚀 NovAIC Agent starting on {settings.host}:{settings.port}")
    print(f"🤖 Default model: {settings.default_model}")
    print(f"🔗 LLM API: {settings.llm_api_base}")
    print(f"🔧 Executor URL: {settings.executor_url}")
    
    yield
    
    print("👋 NovAIC Agent shutting down")


app = FastAPI(
    title="NovAIC Agent",
    description="LLM Agent - 调用 Executor 执行操作",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Agent 路由
app.include_router(router, prefix="/api")
app.include_router(vnc_router)  # VNC 管理（保留，因为是 VM 特有的）


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "NovAIC Agent",
        "version": "0.2.0",
        "description": "LLM Agent - 对话与工具调用",
        "executor": settings.executor_url
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
