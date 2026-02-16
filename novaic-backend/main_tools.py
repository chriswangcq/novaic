"""
NovAIC Backend 组件: Tools Server

提供纯 HTTP API 的工具服务。
直接通过 HTTP API 提供工具调用。

Usage:
    novaic-backend tools-server [--port PORT] [--data-dir PATH]
    or: python main_tools.py

Requires:
    NOVAIC_DATA_DIR - 数据目录
    GATEWAY_URL - Gateway URL（工具调用 Gateway internal API）
"""

import os
import sys
import logging
import argparse
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common.config import ServiceConfig


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="NovAIC Tools Server")
    parser.add_argument("command", nargs="?", default="tools-server")
    return parser.parse_args()


def setup_environment(args):
    """Validate strict config requirements."""
    _ = args
    if not ServiceConfig.DATA_DIR:
        print("[Tools Server] ERROR: paths.data_dir is required in config/services.json")
        sys.exit(1)
    Path(ServiceConfig.DATA_DIR).mkdir(parents=True, exist_ok=True)


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tools-server")

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tools_server.api import router, internal_router
from tools_server.runtime_manager import init_runtime_manager, shutdown_runtime_manager

# Port for Tools Server (default 19998)
TOOLS_PORT = ServiceConfig.TOOLS_SERVER_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup RuntimeManager."""
    gateway_url = ServiceConfig.GATEWAY_URL
    
    # Initialize with gateway_url for persistence
    manager = init_runtime_manager(gateway_url=gateway_url)
    logger.info("[Tools Server] RuntimeManager initialized")
    logger.info(f"[Tools Server] Using Gateway API at: {gateway_url}")
    logger.info(f"[Tools Server] Data directory: {ServiceConfig.DATA_DIR}")
    
    # Restore active runtimes from Gateway DB
    try:
        restored = await manager.restore_from_gateway()
        if restored > 0:
            logger.info(f"[Tools Server] Restored {restored} runtime(s) from Gateway")
        else:
            logger.info("[Tools Server] No runtimes to restore")
    except Exception as e:
        logger.warning(f"[Tools Server] Failed to restore runtimes: {e}")
    
    yield
    
    await shutdown_runtime_manager()
    logger.info("[Tools Server] RuntimeManager closed")


app = FastAPI(
    title="NovAIC Tools Server",
    description="HTTP API for tool execution (no FastMCP)",
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

# Include routers
app.include_router(router)
app.include_router(internal_router)


def main():
    """主入口函数"""
    args = parse_args()
    setup_environment(args)
    
    port = ServiceConfig.TOOLS_SERVER_PORT
    
    logger.info(f"[Tools Server] Starting on http://127.0.0.1:{port}")
    logger.info(f"[Tools Server] Gateway URL: {ServiceConfig.GATEWAY_URL}")
    logger.info(f"[Tools Server] Data directory: {ServiceConfig.DATA_DIR}")
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    main()
