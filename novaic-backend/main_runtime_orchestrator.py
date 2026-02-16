"""
NovAIC Backend component: Runtime Orchestrator service.

This process serves `/internal/*` APIs as a standalone service.
Gateway can proxy internal runtime/subagent/message requests here.
"""

import argparse
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import ServiceConfig
from gateway.api.internal.helpers import set_runtime_orchestrator_process
from gateway.api.internal import router as internal_router
from gateway.db import close_database, init_database, run_migration


def parse_args():
    parser = argparse.ArgumentParser(description="NovAIC Runtime Orchestrator")
    parser.add_argument("command", nargs="?", default="runtime-orchestrator")
    return parser.parse_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(ServiceConfig.DATA_DIR).mkdir(parents=True, exist_ok=True)
    db = init_database(
        data_dir=ServiceConfig.DATA_DIR,
        db_file=ServiceConfig.RUNTIME_ORCHESTRATOR_DB_FILE,
    )
    run_migration(db)
    yield
    close_database()


app = FastAPI(
    title="NovAIC Runtime Orchestrator",
    description="Standalone internal runtime orchestration APIs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(internal_router)
# Runtime Orchestrator serves /internal APIs directly, never proxy to itself.
set_runtime_orchestrator_process(True)


@app.get("/api/health")
def health():
    return {"service": "runtime-orchestrator", "status": "ok"}


def main():
    _ = parse_args()
    if not ServiceConfig.DATA_DIR:
        print("[Runtime Orchestrator] ERROR: paths.data_dir is required in config/services.json")
        sys.exit(1)
    uvicorn.run(
        app,
        host=ServiceConfig.RUNTIME_ORCHESTRATOR_HOST,
        port=ServiceConfig.RUNTIME_ORCHESTRATOR_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
