"""
NovAIC Backend 组件: MCP Gateway - MCP only.

Backend 组件（Gateway、MCP Gateway）均由 Tauri 统一拉起。
本进程为 MCP Gateway：MCP 服务聚合层（MCPManager、AggregateMCP、Runtime/Agent 共享层）。

架构原则：MCP Gateway 不直接导入 gateway/ 模块，所有数据访问通过 Gateway API。

Usage:
    novaic-backend mcp-gateway [--port PORT] [--data-dir PATH]
    or: python main_mcp.py

Requires:
    NOVAIC_DATA_DIR - 数据目录
    GATEWAY_URL - Gateway URL（MCP servers 调 Gateway internal API）
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

# Set no_proxy for local services
os.environ.setdefault("no_proxy", "localhost,127.0.0.1,::1")
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1,::1")

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# NOVAIC_DATA_DIR is required
if not os.environ.get("NOVAIC_DATA_DIR"):
    print("[MCP Gateway] ERROR: NOVAIC_DATA_DIR environment variable is required")
    print("[MCP Gateway] Set it to the same value as Gateway (e.g. from Tauri app)")
    sys.exit(1)

# Set default GATEWAY_URL if not provided
if not os.environ.get("GATEWAY_URL"):
    os.environ["GATEWAY_URL"] = "http://localhost:8000"

NOVAIC_DATA_DIR = os.environ["NOVAIC_DATA_DIR"]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-gateway")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_gateway.manager import MCPManager, set_mcp_manager, get_mcp_manager
from mcp_gateway.api import router as mcp_api_router

# Port for this MCP Gateway (default 19998; Gateway uses 8000)
MCP_PORT = int(os.environ.get("NOVAIC_MCP_PORT", "19998"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCPManager (no local database - use Gateway API)."""
    mcp_manager = MCPManager(app)
    set_mcp_manager(mcp_manager)
    logger.info("[MCP Gateway] MCPManager initialized")
    logger.info(f"[MCP Gateway] Using Gateway API at: {os.environ.get('GATEWAY_URL')}")
    
    yield
    
    mgr = get_mcp_manager()
    if mgr:
        await mgr.close_all()
        set_mcp_manager(None)
        logger.info("[MCP Gateway] MCPManager closed")


app = FastAPI(
    title="NovAIC MCP Gateway",
    description="MCP aggregation and runtime/agent MCP servers only",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_api_router)


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "mcp-gateway"}


def main():
    # So AggregateMCP._register_runtime_servers uses this port for gateway_base
    os.environ["NOVAIC_PORT"] = str(MCP_PORT)
    if not os.environ.get("NOVAIC_MCP_GATEWAY_URL"):
        os.environ["NOVAIC_MCP_GATEWAY_URL"] = f"http://127.0.0.1:{MCP_PORT}"
    logger.info("MCP Gateway starting on http://127.0.0.1:%s", MCP_PORT)
    uvicorn.run(app, host="127.0.0.1", port=MCP_PORT, log_level="info")


if __name__ == "__main__":
    main()
