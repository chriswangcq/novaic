"""
File Service - 独立运行入口
可单独启动为 HTTP 服务，监听独立端口。

用法:
  python -m file_service.main
  python -m file_service.main --port 9100 --base-dir /path/to/data
"""

import argparse
import logging
import os

import uvicorn
from common.config import ServiceConfig

from .storage import FileStorage
from .routes import create_router

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app(base_dir: str = None, url_prefix: str = "/api/files"):
    """创建 FastAPI 应用"""
    from fastapi import FastAPI

    if base_dir is None:
        base_dir = ServiceConfig.DATA_DIR
    files_dir = os.path.join(base_dir, "files")
    os.makedirs(files_dir, exist_ok=True)

    storage = FileStorage(base_dir=files_dir, url_prefix=url_prefix)
    router = create_router(storage)

    app = FastAPI(title="NovaIC File Service", version="1.0.0")
    
    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "file-service"}
    
    app.include_router(router)
    app.state.storage = storage

    logger.info(f"[FileService] Started, base_dir={files_dir}")

    return app


def main():
    parser = argparse.ArgumentParser(description="NovaIC File Service")
    parser.add_argument("--port", type=int, default=ServiceConfig.FILE_SERVICE_PORT, help="Port to listen")
    parser.add_argument("--host", type=str, default=ServiceConfig.FILE_SERVICE_HOST, help="Host to bind")
    parser.add_argument("--base-dir", type=str, default=ServiceConfig.DATA_DIR, help="Base data directory")
    args = parser.parse_args()

    base_dir = args.base_dir
    app = create_app(base_dir=base_dir)

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
