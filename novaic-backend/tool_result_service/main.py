"""
Tool Result Service - 入口
"""

import argparse
import logging

import uvicorn
from common.config import ServiceConfig

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app():
    from fastapi import FastAPI

    from .handlers import router

    app = FastAPI(title="NovaIC Tool Result Service", version="1.0.0")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "tool-result-service"}

    app.include_router(router)
    logger.info("[ToolResultService] Started")
    return app


def main():
    parser = argparse.ArgumentParser(description="NovaIC Tool Result Service")
    parser.add_argument("--port", type=int, default=ServiceConfig.TOOL_RESULT_SERVICE_PORT)
    parser.add_argument("--host", type=str, default=ServiceConfig.TOOL_RESULT_SERVICE_HOST)
    parser.add_argument("--data-dir", default=ServiceConfig.DATA_DIR, help="Data directory")
    args = parser.parse_args()

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
