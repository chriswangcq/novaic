"""
NovAIC Backend 组件: MCP Gateway - MCP only.

Backend 四组件（Gateway、MCP Gateway、Master、Worker）均由 Tauri 统一拉起。
本进程为 MCP Gateway：仅 MCP（MCPManager、AggregateMCP、Runtime/Agent 共享层），与 Gateway、Master、Worker 并列。

Usage:
    novaic-backend mcp-gateway [--port PORT] [--data-dir PATH]
    or: python mcp_main.py

Requires:
    NOVAIC_DATA_DIR - 与 Gateway 共用
    NOVAIC_GATEWAY_URL - Gateway URL（RuntimeMCP 调 Gateway internal API）
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

# NOVAIC_DATA_DIR is required (same as Backend)
if not os.environ.get("NOVAIC_DATA_DIR"):
    print("[MCP Gateway] ERROR: NOVAIC_DATA_DIR environment variable is required")
    print("[MCP Gateway] Set it to the same value as Backend (e.g. from Tauri app)")
    sys.exit(1)

NOVAIC_DATA_DIR = os.environ["NOVAIC_DATA_DIR"]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-gateway")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_servers.manager import MCPManager, set_mcp_manager, get_mcp_manager
from api.internal_mcp import router as internal_mcp_router

# Port for this MCP Gateway (default 19998; Backend uses 19999)
MCP_PORT = int(os.environ.get("NOVAIC_MCP_PORT", "19998"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and shutdown MCPManager only."""
    mcp_manager = MCPManager(app)
    set_mcp_manager(mcp_manager)
    logger.info("[MCP Gateway] MCPManager initialized")
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

app.include_router(internal_mcp_router)


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
