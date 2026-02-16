"""
Contract integration tests for Gateway -> Runtime Orchestrator /internal proxying.

These tests validate the real request chain:
Gateway /internal proxy router -> Runtime Orchestrator internal handlers.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from common.db import Database
from gateway.api.internal import router as internal_router
from gateway.api.internal_proxy import router as internal_proxy_router
from gateway.db import access as db_access
from gateway.db.schema import init_schema_sync

REAL_HTTPX_ASYNC_CLIENT = httpx.AsyncClient


@pytest.fixture
def orchestrator_app():
    """Runtime Orchestrator-style app serving local /internal handlers."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    prev_process_flag = os.environ.get("NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS")
    os.environ["NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS"] = "true"

    try:
        db = Database(db_path)
        db.connect(init_schema_func=init_schema_sync)
        orig_db = db_access._database
        db_access._database = db

        app = FastAPI()
        app.include_router(internal_router)
        yield app
    finally:
        if prev_process_flag is None:
            os.environ.pop("NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS", None)
        else:
            os.environ["NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS"] = prev_process_flag

        db_access._database = orig_db
        try:
            db_path.unlink()
        except Exception:
            pass


@pytest.fixture
def gateway_proxy_app():
    """Gateway-style app exposing only /internal proxy router."""
    app = FastAPI()
    app.include_router(internal_proxy_router)
    return app


def _orchestrator_async_client_factory(orchestrator_app):
    """Build a patched internal_async_client factory bound to orchestrator ASGI app."""

    def _factory(*args, **kwargs):
        return REAL_HTTPX_ASYNC_CLIENT(
            transport=ASGITransport(app=orchestrator_app),
            base_url="http://orchestrator-test",
        )

    return _factory


@pytest.mark.asyncio
class TestGatewayInternalProxyIntegration:
    async def test_runtimes_list_through_gateway_proxy(
        self, gateway_proxy_app, orchestrator_app
    ):
        """GET /internal/runtimes/list is served through orchestrator chain."""
        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://orchestrator-test",
            ),
            patch(
                "gateway.api.internal_proxy.internal_async_client",
                side_effect=_orchestrator_async_client_factory(orchestrator_app),
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=gateway_proxy_app),
                base_url="http://gateway-test",
            ) as client:
                resp = await client.get("/internal/runtimes/list")

        assert resp.status_code == 200
        data = resp.json()
        assert "runtimes" in data
        assert isinstance(data["runtimes"], list)

    async def test_runtimes_batch_empty_through_gateway_proxy(
        self, gateway_proxy_app, orchestrator_app
    ):
        """POST /internal/runtimes/batch preserves JSON envelope via proxy."""
        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://orchestrator-test",
            ),
            patch(
                "gateway.api.internal_proxy.internal_async_client",
                side_effect=_orchestrator_async_client_factory(orchestrator_app),
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=gateway_proxy_app),
                base_url="http://gateway-test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/batch",
                    json={"runtime_ids": []},
                )

        assert resp.status_code == 200
        assert resp.json() == {"runtimes": []}

    async def test_qemu_status_missing_runtime_404_through_gateway_proxy(
        self, gateway_proxy_app, orchestrator_app
    ):
        """GET /internal/rt/{runtime_id}/qemu/status returns orchestrator 404."""
        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://orchestrator-test",
            ),
            patch(
                "gateway.api.internal_proxy.internal_async_client",
                side_effect=_orchestrator_async_client_factory(orchestrator_app),
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=gateway_proxy_app),
                base_url="http://gateway-test",
            ) as client:
                resp = await client.get("/internal/rt/rt-nonexistent-xyz/qemu/status")

        assert resp.status_code == 404
        detail = (resp.json() or {}).get("detail", "")
        assert "not found" in str(detail).lower()
