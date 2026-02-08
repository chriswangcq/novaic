"""
Queue Service - 独立的任务队列服务

提供 Task Queue 和 Saga 的 HTTP API。
使用独立数据库 queue.db，与 Gateway 完全解耦。

端口：19997
数据库：$NOVAIC_DATA_DIR/queue.db
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加父目录到 Python 路径（确保可以导入 common 和 queue_service）
BACKEND_DIR = Path(__file__).parent.parent.absolute()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ==================== Environment Variables ====================
print("[Queue Service] === Environment Variables ===")
print(f"[Queue Service] NOVAIC_DATA_DIR: {os.environ.get('NOVAIC_DATA_DIR', 'NOT SET')}")
print(f"[Queue Service] Current working directory: {os.getcwd()}")
print(f"[Queue Service] Executable path: {sys.executable}")
print("[Queue Service] ===============================")

# Validate NOVAIC_DATA_DIR
if not os.environ.get("NOVAIC_DATA_DIR"):
    print("[Queue Service] ERROR: NOVAIC_DATA_DIR environment variable is required")
    print("[Queue Service] Please start Queue Service through the NovAIC app")
    sys.exit(1)

NOVAIC_DATA_DIR = os.environ["NOVAIC_DATA_DIR"]
print(f"[Queue Service] Data directory: {NOVAIC_DATA_DIR}")

# ==================== Logging Setup ====================
LOG_DIR = os.path.join(NOVAIC_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"queue-service-{datetime.utcnow().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("Queue Service Starting")
logger.info(f"Data directory: {NOVAIC_DATA_DIR}")
logger.info(f"Log file: {LOG_FILE}")
logger.info("=" * 60)

# ==================== FastAPI App ====================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Queue Service",
    description="独立的任务队列服务 - Task Queue + Saga",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Database Initialization ====================
from common.db import Database
from queue_service.db import init_schema

# 初始化独立数据库
DB_PATH = Path(NOVAIC_DATA_DIR) / "queue.db"
logger.info(f"[Queue Service] Database path: {DB_PATH}")

db = Database(DB_PATH)
db.connect(init_schema_func=init_schema)

logger.info("[Queue Service] Database initialized")

# ==================== Task Queue & Saga Setup ====================
from queue_service.queue_db import TaskQueue
from queue_service.saga_repo import SagaRepository, SagaOrchestrator
from queue_service.routes import (
    create_task_queue_router,
    create_recovery_router,
)

# 创建 TaskQueue
task_queue = TaskQueue(db)
logger.info("[Queue Service] TaskQueue created")

# 创建 SagaRepository
saga_repo = SagaRepository(db, task_queue)
logger.info("[Queue Service] SagaRepository created")

# 创建 SagaOrchestrator（用于测试和同步执行）
saga_orchestrator = SagaOrchestrator(task_queue, db)
logger.info("[Queue Service] SagaOrchestrator created")

# ==================== API Routes ====================

# Task Queue & Saga API
tq_router = create_task_queue_router(task_queue, saga_orchestrator)
app.include_router(tq_router, prefix="/api/queue")

# Recovery API
recovery_router = create_recovery_router(task_queue, saga_orchestrator)
app.include_router(recovery_router, prefix="/api/queue/recover")

logger.info("[Queue Service] API routes registered")

# ==================== Health Check ====================

@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "queue-service",
        "version": "1.0.0",
        "database": str(DB_PATH),
    }

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "Queue Service",
        "version": "1.0.0",
        "description": "独立的任务队列服务 - Task Queue + Saga",
        "database": str(DB_PATH),
        "endpoints": {
            "health": "/health",
            "tasks": "/api/queue/tasks/*",
            "sagas": "/api/queue/sagas/*",
            "recovery": "/api/queue/recover/*",
        }
    }

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("[Queue Service] Startup complete")
    logger.info(f"[Queue Service] Database: {DB_PATH}")
    logger.info("[Queue Service] Ready to accept requests")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("[Queue Service] Shutting down...")
    db.close()
    logger.info("[Queue Service] Shutdown complete")

# ==================== Main Entry ====================

if __name__ == "__main__":
    import uvicorn
    
    PORT = int(os.environ.get("QUEUE_SERVICE_PORT", "19997"))
    
    logger.info(f"[Queue Service] Starting server on port {PORT}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True,
    )
