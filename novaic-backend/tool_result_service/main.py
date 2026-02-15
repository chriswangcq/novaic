"""
Tool Result Service - 入口
"""

import argparse
import logging
import os

import uvicorn

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
    parser.add_argument("--port", type=int, default=int(os.getenv("TOOL_RESULT_SERVICE_PORT", "19994")))
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--data-dir", help="Data directory (sets NOVAIC_DATA_DIR)")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
