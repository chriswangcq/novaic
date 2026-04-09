"""FastAPI app factory for Entangled Service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import ServiceConfig
from .db.access import close_database, init_database
from .middleware.auth import configure_auth
from .store.entity_store import init_entity_store

logger = logging.getLogger(__name__)


def create_app(config: ServiceConfig) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Entangled Service starting on %s:%s", config.host, config.port)

        # 1. Database
        db = init_database(config.db_path)
        logger.info("Database initialized: %s", config.db_path)

        # 2. Sync version persistence table
        _ensure_sync_versions_table(db)

        # 3. EntityStore
        store = init_entity_store(db=db)
        logger.info("EntityStore ready (0 entities — waiting for schema registration)")

        # 4. Auth
        configure_auth(jwt_secret=config.jwt_secret, service_token=config.service_token)

        # 5. Sync engine (with version persistence)
        from .api.ws import init_sync_engine
        from .store.sync_persistence import load_all_sync_versions, make_version_bump_handler

        registry = init_sync_engine(on_version_bump=make_version_bump_handler(db))
        load_all_sync_versions(db, registry)
        logger.info("Sync engine initialized")

        logger.info("Entangled Service ready")
        yield

        close_database()
        logger.info("Entangled Service shutdown")

    app = FastAPI(
        title="Entangled Service",
        description="Standalone entity engine — CRUD, sync, and real-time push",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Routes
    from .api.health import router as health_router
    from .api.schema import router as schema_router
    from .api.crud import router as crud_router
    from .api.ws import ws_sync_handler

    app.include_router(health_router)
    app.include_router(schema_router)
    app.include_router(crud_router)
    app.add_websocket_route("/v1/sync", ws_sync_handler)

    return app


def _ensure_sync_versions_table(db):
    """Create the entangled_sync_versions table if it doesn't exist."""
    with db.transaction("global"):
        db.execute("""
            CREATE TABLE IF NOT EXISTS entangled_sync_versions (
                state_key TEXT PRIMARY KEY,
                version INTEGER NOT NULL DEFAULT 0
            )
        """)
