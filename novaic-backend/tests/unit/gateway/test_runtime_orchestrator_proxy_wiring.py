"""
Unit tests for Phase-4 proxy wiring of internal read-only endpoints.

Verifies:
a) When RUNTIME_ORCHESTRATOR_URL is set, endpoints use proxy (forward called).
b) When not set, endpoints raise 500 (strict, no fallback); forward not called.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import httpx
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from common.config import ServiceConfig
from common.db import Database
from gateway.api.internal import router as internal_router
from gateway.db import access as db_access
from gateway.db.schema import init_schema_sync


@pytest.fixture
def minimal_internal_app():
    """Minimal FastAPI app with internal router for proxy wiring tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    try:
        db = Database(db_path)
        db.connect(init_schema_func=init_schema_sync)
        orig = db_access._database
        db_access._database = db
        app = FastAPI()
        app.include_router(internal_router)
        yield app
    finally:
        db_access._database = orig
        try:
            db_path.unlink()
        except Exception:
            pass


@pytest.mark.asyncio
class TestProxyWhenConfigured:
    """When RUNTIME_ORCHESTRATOR_URL is set, endpoints should proxy via forward."""

    async def test_runtimes_get_by_id_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/{runtime_id} proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"runtime_id": "rt-xyz", "agent_id": "a1", "status": "active"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/rt-xyz")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/rt-xyz", params=None, json=None
        )

    async def test_runtimes_main_GET_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/main/{agent_id} proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"runtime": {"runtime_id": "rt-main", "agent_id": "a1"}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/main/agent-123")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/main/agent-123", params=None, json=None
        )

    async def test_runtimes_subagent_GET_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/subagent/{agent_id}/{subagent_id} proxies."""
        canned = {"runtime": {"runtime_id": "rt-sub", "agent_id": "a1", "subagent_id": "sub-1"}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/subagent/agent-a/sub-1")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/subagent/agent-a/sub-1", params=None, json=None
        )

    async def test_runtimes_latest_GET_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/latest/{agent_id}/{subagent_id} proxies."""
        canned = {"runtimes": [{"runtime_id": "rt-1", "agent_id": "a1"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/runtimes/latest/agent-a/sub-1",
                    params={"limit": 30},
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/runtimes/latest/agent-a/sub-1",
            params={"limit": 30},
            json=None,
        )

    async def test_runtimes_list_uses_proxy(self, minimal_internal_app):
        canned = {"runtimes": [{"runtime_id": "rt-proxy-1", "agent_id": "a1"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/list")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/list", params=None, json=None
        )

    async def test_runtimes_active_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/active proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"runtimes": [{"runtime_id": "rt-active-1", "agent_id": "a1"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/active")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/active", params=None, json=None
        )

    async def test_has_active_runtime_uses_proxy(self, minimal_internal_app):
        """GET /agents/{agent_id}/subagents/{subagent_id}/has-active-runtime proxies."""
        canned = {"has_active_runtime": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/agents/agent-a/subagents/sub-1/has-active-runtime"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/agents/agent-a/subagents/sub-1/has-active-runtime",
            params=None,
            json=None,
        )

    async def test_subagents_get_uses_proxy(self, minimal_internal_app):
        """GET /subagents/{agent_id}/{subagent_id} proxies."""
        canned = {
            "subagent_id": "sub-1",
            "agent_id": "agent-a",
            "type": "main",
            "status": "awake",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/agent-a/sub-1")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/subagents/agent-a/sub-1", params=None, json=None
        )

    async def test_subagents_main_uses_proxy(self, minimal_internal_app):
        """GET /subagents/{agent_id}/main proxies."""
        canned = {
            "subagent_id": "main-agent-a",
            "agent_id": "agent-a",
            "type": "main",
            "status": "awake",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/agent-a/main")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/subagents/agent-a/main", params=None, json=None
        )

    async def test_subagents_summary_lock_uses_proxy(self, minimal_internal_app):
        """GET /subagents/{agent_id}/{subagent_id}/summary-lock proxies."""
        canned = {"summary_lock": 0}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/subagents/agent-a/sub-1/summary-lock"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/subagents/agent-a/sub-1/summary-lock",
            params=None,
            json=None,
        )

    async def test_summary_lock_acquire_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/{subagent_id}/summary-lock/acquire proxies."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-1/summary-lock/acquire"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/sub-1/summary-lock/acquire",
            params=None,
            json=None,
        )

    async def test_summary_lock_release_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/{subagent_id}/summary-lock/release proxies."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-1/summary-lock/release"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/sub-1/summary-lock/release",
            params=None,
            json=None,
        )

    async def test_merge_history_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/{subagent_id}/merge-history proxies."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"new_history": "merged summary", "remove_runtime_ids": ["rt-1"]}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-1/merge-history",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/sub-1/merge-history",
            params=None,
            json=payload,
        )

    async def test_agents_drive_uses_proxy(self, minimal_internal_app):
        """GET /agents/{agent_id}/drive proxies."""
        canned = {"agent_id": "agent-a", "personality": {}, "proactiveness": 0.5}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/agents/agent-a/drive")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/agents/agent-a/drive", params=None, json=None
        )

    async def test_agents_info_uses_proxy(self, minimal_internal_app):
        """GET /agents/{agent_id}/info proxies."""
        canned = {"name": "NovAIC Agent", "os": "unknown", "agent_id": "agent-a"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/agents/agent-a/info")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/agents/agent-a/info", params=None, json=None
        )

    async def test_vm_tools_GET_uses_proxy(self, minimal_internal_app):
        """GET /runtimes/{runtime_id}/vm-tools proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {
            "tools": [{"name": "vm_start", "description": "..."}],
            "agent_id": "agent-a",
            "vm_available": True,
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/runtimes/rt-xyz/vm-tools",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/runtimes/rt-xyz/vm-tools", params=None, json=None
        )

    async def test_subagents_hrl_uses_proxy(self, minimal_internal_app):
        """GET /subagents/{agent_id}/{subagent_id}/hrl proxies."""
        canned = {"hrl": ["rt-1", "rt-2"], "length": 2}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/agent-a/sub-1/hrl")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/subagents/agent-a/sub-1/hrl", params=None, json=None
        )

    async def test_hrl_add_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/{subagent_id}/hrl/add proxies."""
        canned = {"success": True, "hrl": ["rt-1", "rt-2"], "length": 2}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"runtime_id": "rt-2"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-1/hrl/add",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/sub-1/hrl/add",
            params=None,
            json=payload,
        )

    async def test_agents_notebook_summary_uses_proxy(self, minimal_internal_app):
        """GET /agents/{agent_id}/notebook-summary proxies."""
        canned = {"success": True, "entries": [], "count": 0}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/agents/agent-a/notebook-summary")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/agents/agent-a/notebook-summary", params=None, json=None
        )

    async def test_subagents_due_wake_uses_proxy(self, minimal_internal_app):
        canned = {"subagents": [{"agent_id": "a1", "subagent_id": "main-a1"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/due-wake")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/subagents/due-wake", params=None, json=None
        )

    async def test_messages_unread_sent_uses_proxy(self, minimal_internal_app):
        canned = {"messages": [{"id": "m1", "type": "USER_MESSAGE"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/messages/unread-sent/agent-test-123"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/messages/unread-sent/agent-test-123",
            params=None,
            json=None,
        )

    async def test_runtimes_batch_uses_proxy(self, minimal_internal_app):
        canned = {"runtimes": [{"runtime_id": "rt-proxy-2", "agent_id": "a2"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"runtime_ids": ["rt-proxy-2"]}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/batch", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/runtimes/batch", params=None, json=payload
        )

    async def test_runtimes_get_or_create_uses_proxy(self, minimal_internal_app):
        canned = {"runtime_id": "rt-xxx", "agent_id": "a1", "just_created": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"agent_id": "a1", "subagent_id": "main"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/get-or-create", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/runtimes/get-or-create", params=None, json=payload
        )

    async def test_runtimes_POST_uses_proxy(self, minimal_internal_app):
        """POST /runtimes proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"runtime_id": "rt-new", "agent_id": "a1", "subagent_id": "main"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"agent_id": "a1", "subagent_id": "main"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/runtimes", params=None, json=payload
        )

    async def test_runtimes_main_uses_proxy(self, minimal_internal_app):
        canned = {"runtime_id": "rt-main", "agent_id": "a1"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"agent_id": "a1"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/main", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/runtimes/main", params=None, json=payload
        )

    async def test_runtimes_context_append_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "appended": True, "context_length": 1}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"message": {"role": "user", "content": "hi"}}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/context/append",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/context/append",
            params=None,
            json=payload,
        )

    async def test_runtimes_send_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "queued": True, "runtime_id": "rt-123"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"message": "hello"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/send",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/send",
            params=None,
            json=payload,
        )

    async def test_runtimes_rest_uses_proxy(self, minimal_internal_app):
        canned = {
            "success": True,
            "state": "need_rest",
            "reason": "test reason",
            "triggers_set": 1,
            "estimated_wake": "2025-02-17T12:00:00",
            "rest_duration_minutes": 30,
            "handoff_notes": "notes",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {
            "reason": "test reason",
            "wake_triggers": [{"type": "user_response"}],
            "handoff_notes": "notes",
        }

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-rest-1/rest",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-rest-1/rest",
            params=None,
            json=payload,
        )

    async def test_runtimes_wake_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok", "success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-wake-1/wake",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-wake-1/wake",
            params=None,
            json=None,
        )

    async def test_runtimes_advance_uses_proxy(self, minimal_internal_app):
        canned = {"round_id": "rnd-xyz", "success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"expected_round_num": 3}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-adv-1/advance",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-adv-1/advance",
            params=None,
            json=payload,
        )

    async def test_runtimes_PATCH_uses_proxy(self, minimal_internal_app):
        """PATCH /runtimes/{runtime_id} proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"phase": "running", "status": "active"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/runtimes/rt-123",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "PATCH", "/internal/runtimes/rt-123", params=None, json=payload
        )

    async def test_runtimes_set_status_uses_proxy(self, minimal_internal_app):
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"expected_status": "active", "new_status": "completed"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/set-status",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/set-status",
            params=None,
            json=payload,
        )

    async def test_runtimes_summarized_uses_proxy(self, minimal_internal_app):
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/summarized",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/summarized",
            params=None,
            json=None,
        )

    async def test_runtimes_need_rest_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "current_value": "1", "message": "OK"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"value": True}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/need-rest",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/need-rest",
            params=None,
            json=payload,
        )

    async def test_runtimes_tool_ports_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "runtime_id": "rt-123"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"ports": {"vmuse": 8080}}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-123/tool-ports",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-123/tool-ports",
            params=None,
            json=payload,
        )

    async def test_runtimes_hot_cold_summary_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "runtime_id": "rt-sum-1"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"hot_summary": "hot", "cold_summary": "cold"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-sum-1/hot-cold-summary",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-sum-1/hot-cold-summary",
            params=None,
            json=payload,
        )

    async def test_runtimes_history_uses_proxy(self, minimal_internal_app):
        canned = {"messages": [{"role": "user", "content": "hi"}], "total": 1}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"limit": 50, "offset": 0}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-hist-1/history",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/runtimes/rt-hist-1/history",
            params=None,
            json=payload,
        )

    async def test_runtimes_delete_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/internal/runtimes/rt-del-1")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "DELETE",
            "/internal/runtimes/rt-del-1",
            params=None,
            json=None,
        )

    async def test_rt_memory_namespaces_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/memory/namespaces proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "namespaces": ["default", "tasks"]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/rt/rt-proxy-1/memory/namespaces")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/rt/rt-proxy-1/memory/namespaces", params=None, json=None
        )

    async def test_rt_memory_recall_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/memory/recall proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"key": "k1", "value": "v1", "namespace": "default"}
        payload = {"key": "k1", "namespace": "default"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/memory/recall",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/memory/recall",
            params=None,
            json=payload,
        )

    async def test_rt_memory_save_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/memory/save proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "key": "k1", "namespace": "default"}
        payload = {"key": "k1", "value": "v1", "namespace": "default"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/memory/save",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/memory/save",
            params=None,
            json=payload,
        )

    async def test_rt_memory_delete_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/memory/delete proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        payload = {"key": "k1", "namespace": "default"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/memory/delete",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/memory/delete",
            params=None,
            json=payload,
        )

    async def test_rt_memory_task_log_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/memory/task/log proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "task_id": "t1"}
        payload = {"action": "create", "details": "test task", "status": "completed"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/memory/task/log",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/memory/task/log",
            params=None,
            json=payload,
        )

    async def test_rt_notebook_delete_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/notebook/delete proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        payload = {"entry_id": "e1"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/notebook/delete",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/notebook/delete",
            params=None,
            json=payload,
        )

    async def test_rt_notebook_write_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/notebook/write proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"entry_id": "nb-1", "success": True}
        payload = {"title": "Note", "content": "text", "entry_type": "observation"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/notebook/write",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/notebook/write",
            params=None,
            json=payload,
        )

    async def test_rt_notebook_update_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/notebook/update proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        payload = {"entry_id": "e1", "content": "updated", "status": "done"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/notebook/update",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/notebook/update",
            params=None,
            json=payload,
        )

    async def test_rt_drive_update_profile_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/drive/update-profile proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        payload = {"key": "preference", "value": "value", "reason": "test"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/drive/update-profile",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/drive/update-profile",
            params=None,
            json=payload,
        )

    async def test_rt_drive_update_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/drive/update proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        payload = {
            "relationship_delta": 0.1,
            "proactiveness_delta": 0.05,
            "reason": "test",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/drive/update",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/drive/update",
            params=None,
            json=payload,
        )

    async def test_rt_memory_task_history_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/memory/task/history proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"tasks": [], "total": 0}
        payload = {"limit": 20}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/memory/task/history",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/memory/task/history",
            params=None,
            json=payload,
        )

    async def test_rt_chat_history_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/chat/history proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"messages": [], "has_more": False}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/chat/history",
                    params={"limit": 50, "summary_length": 200},
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/chat/history",
            params={"limit": 50, "summary_length": 200},
            json=None,
        )

    async def test_rt_chat_event_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/chat/event proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "event_type": "AGENT_REPLY", "message_id": "msg-1"}
        payload = {"type": "AGENT_REPLY", "data": {"message": "Hello"}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/chat/event",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/chat/event",
            params=None,
            json=payload,
        )

    async def test_rt_notebook_read_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/notebook/read proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"entry_id": "e1", "title": "Note", "content": "Hello"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"entry_id": "e1"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/notebook/read",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/notebook/read",
            params=None,
            json=payload,
        )

    async def test_rt_notebook_list_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/notebook/list proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"entries": [{"entry_id": "e1", "title": "Note"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"limit": 10, "entry_type": "observation"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/notebook/list",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/notebook/list",
            params=None,
            json=payload,
        )

    async def test_rt_chat_message_GET_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/chat/message/{message_id} proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "id": "m1", "role": "assistant", "content": {}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/chat/message/msg-123",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/chat/message/msg-123",
            params=None,
            json=None,
        )

    async def test_rt_qemu_status_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/qemu/status proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "qemu_running": True, "agent_id": "agent-a"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/qemu/status",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/qemu/status",
            params=None,
            json=None,
        )

    async def test_rt_qemu_ssh_exec_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/qemu/ssh-exec proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"stdout": "ok", "stderr": "", "exit_code": 0, "success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"command": "echo hi", "timeout": 10}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/qemu/ssh-exec",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/qemu/ssh-exec",
            params=None,
            json=payload,
        )

    async def test_rt_qemu_start_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/qemu/start proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "pid": 12345}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"memory": "4096", "cpus": 4}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/qemu/start",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/qemu/start",
            params=None,
            json=payload,
        )

    async def test_rt_qemu_shutdown_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/qemu/shutdown proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"graceful": True, "quick": False}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/qemu/shutdown",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/qemu/shutdown",
            params=None,
            json=payload,
        )

    async def test_rt_qemu_restart_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/qemu/restart proxies when RUNTIME_ORCHESTRATOR_URL set."""
        canned = {"success": True, "stop_result": {}, "start_result": {"pid": 12345}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"graceful": True}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/qemu/restart",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/qemu/restart",
            params=None,
            json=payload,
        )

    async def test_rt_subagent_status_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/subagent/{target_subagent_id}/status proxies."""
        canned = {
            "subagent_id": "sub-1",
            "status": "completed",
            "completed": True,
            "progress": None,
            "result": "done",
            "error": None,
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/subagent/sub-1/status",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/subagent/sub-1/status",
            params=None,
            json=None,
        )

    async def test_rt_tasks_spawn_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/tasks/spawn proxies."""
        canned = {"task_id": "t1", "status": "queued"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"task_type": "tool", "config": {}, "label": "test"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/tasks/spawn",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/tasks/spawn",
            params=None,
            json=payload,
        )

    async def test_rt_subagent_spawn_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/subagent/spawn proxies."""
        canned = {"subagent_id": "sub-1", "message_id": "m1"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"task": "Do something", "share_context": False}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/subagent/spawn",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/subagent/spawn",
            params=None,
            json=payload,
        )

    async def test_rt_subagent_cancel_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/subagent/{target_subagent_id}/cancel proxies."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/subagent/sub-1/cancel",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/subagent/sub-1/cancel",
            params=None,
            json=None,
        )

    async def test_rt_subagent_report_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/subagent/report proxies."""
        canned = {"success": True, "subagent_id": "sub-1", "message": "Result reported"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"result": "Task completed successfully"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-proxy-1/subagent/report",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/subagent/report",
            params=None,
            json=payload,
        )

    async def test_rt_tasks_uses_proxy(self, minimal_internal_app):
        """GET /rt/{runtime_id}/tasks proxies."""
        canned = {"tasks": [], "total": 0}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/tasks",
                    params={"status": "running"},
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/tasks",
            params={"status": "running"},
            json=None,
        )

    async def test_rt_drive_GET_uses_proxy(self, minimal_internal_app):
        """GET /internal/rt/{runtime_id}/drive proxies."""
        canned = {
            "agent_id": "a1",
            "soul_md": "",
            "heartbeat_md": "",
            "memory_md": "",
            "user_md": "",
            "active_hours_start": "09:00",
            "active_hours_end": "22:00",
            "active_hours_timezone": "Asia/Shanghai",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-proxy-1/drive",
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/rt/rt-proxy-1/drive",
            params=None,
            json=None,
        )

    async def test_rt_drive_get_POST_uses_proxy(self, minimal_internal_app):
        """POST /rt/{runtime_id}/drive/get proxies (read-like get_or_create)."""
        canned = {"agent_id": "a1", "soul_md": "", "memory_md": "", "user_md": ""}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/rt/rt-proxy-1/drive/get", json={})

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/rt/rt-proxy-1/drive/get",
            params=None,
            json={},
        )

    async def test_messages_mark_read_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok"}
        payload = {"message_ids": ["m1"], "agent_id": "agent-test-123"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch("/internal/messages/mark-read", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "PATCH", "/internal/messages/mark-read", params=None, json=payload
        )

    async def test_messages_mark_processed_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok"}
        payload = {"message_ids": ["m1", "m2"], "agent_id": "agent-test-123"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/messages/mark-processed", json=payload
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "PATCH", "/internal/messages/mark-processed", params=None, json=payload
        )

    async def test_messages_inject_subagent_completed_uses_proxy(
        self, minimal_internal_app
    ):
        canned = {
            "success": True,
            "message_id": "msg-xyz",
            "agent_id": "a1",
            "subagent_id": "sub-1",
            "parent_subagent_id": "main-a1",
        }
        payload = {
            "agent_id": "a1",
            "subagent_id": "sub-1",
            "parent_subagent_id": "main-a1",
            "result": "done",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/messages/inject-subagent-completed", json=payload
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/messages/inject-subagent-completed",
            params=None,
            json=payload,
        )

    async def test_messages_inject_wake_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "message_id": "msg-wake-1", "agent_id": "agent-a"}
        payload = {"agent_id": "agent-a", "metadata": {"wake_reason": "scheduled"}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/messages/inject-wake", json=payload
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/messages/inject-wake", params=None, json=payload
        )

    async def test_messages_create_uses_proxy(self, minimal_internal_app):
        canned = {
            "id": "msg-new-1",
            "agent_id": "agent-a",
            "type": "USER_MESSAGE",
            "content": "hi",
            "status": "sending",
        }
        payload = {
            "agent_id": "agent-a",
            "type": "USER_MESSAGE",
            "content": "hi",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages", json=payload)

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/messages", params=None, json=payload
        )

    async def test_subagent_status_uses_proxy(self, minimal_internal_app):
        canned = {
            "subagent_id": "sub-1",
            "status": "running",
            "completed": False,
            "progress": "working",
            "result": None,
            "error": None,
            "runtime_id": "rt-1",
        }
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/agent-x/sub-1/status")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/subagents/agent-x/sub-1/status", params=None, json=None
        )

    # Subagent lifecycle endpoints (Phase 4 next batch)
    async def test_subagent_awake_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "status": "awake", "previous_status": None}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/subagents/agent-a/sub-main/awake")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/subagents/agent-a/sub-main/awake",
            params=None, json=None,
        )

    async def test_subagent_sleeping_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "status": "sleeping", "previous_status": None}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/subagents/agent-a/sub-main/sleeping")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/subagents/agent-a/sub-main/sleeping",
            params=None, json=None,
        )

    async def test_subagent_completed_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok", "result_preserved": False}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"result": "Task done"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-main/completed",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/subagents/agent-a/sub-main/completed",
            params=None, json=payload,
        )

    async def test_subagent_failed_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"error": "Something went wrong"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-main/failed",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/subagents/agent-a/sub-main/failed",
            params=None, json=payload,
        )

    async def test_subagent_cancel_uses_proxy(self, minimal_internal_app):
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/subagents/agent-a/sub-main/cancel")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/subagents/agent-a/sub-main/cancel",
            params=None, json=None,
        )

    async def test_subagent_patch_uses_proxy(self, minimal_internal_app):
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"historical_summary": "updated summary"}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/subagents/agent-a/sub-main",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "PATCH", "/internal/subagents/agent-a/sub-main",
            params=None, json=payload,
        )

    async def test_subagent_summarizing_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/{subagent_id}/summarizing proxies."""
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/sub-main/summarizing"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/sub-main/summarizing",
            params=None,
            json=None,
        )

    async def test_subagent_spawn_uses_proxy(self, minimal_internal_app):
        """POST /subagents/{agent_id}/spawn proxies with json body."""
        canned = {"subagent_id": "sub-abc123", "message_id": "msg-xyz"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)
        payload = {"task": "test task", "share_context": True}

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-a/spawn",
                    json=payload,
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/subagents/agent-a/spawn",
            params=None,
            json=payload,
        )

    async def test_subagent_delete_uses_proxy(self, minimal_internal_app):
        """DELETE /subagents/{agent_id}/{subagent_id} proxies."""
        canned = {"status": "ok"}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.delete(
                    "/internal/subagents/agent-a/sub-main"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "DELETE",
            "/internal/subagents/agent-a/sub-main",
            params=None,
            json=None,
        )

    async def test_increment_drive_interaction_uses_proxy(self, minimal_internal_app):
        """POST /agents/{agent_id}/drive/increment-interaction proxies."""
        canned = {"success": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/agents/agent-a/drive/increment-interaction"
                )

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST",
            "/internal/agents/agent-a/drive/increment-interaction",
            params=None,
            json=None,
        )

    async def test_messages_find_sending_uses_proxy(self, minimal_internal_app):
        canned = {"message": {"id": "m42", "status": "sending"}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages/find-sending")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/messages/find-sending", params=None, json=None
        )

    async def test_messages_confirm_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "message_id": "m42", "confirmed": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages/m42/confirm")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/messages/m42/confirm", params=None, json=None
        )

    async def test_messages_claim_uses_proxy(self, minimal_internal_app):
        canned = {"success": True, "message_id": "m42", "claimed": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages/m42/claim")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "POST", "/internal/messages/m42/claim", params=None, json=None
        )

    async def test_messages_has_new_uses_proxy(self, minimal_internal_app):
        canned = {"has_new_messages": True}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/messages/has-new/agent-test-123")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/messages/has-new/agent-test-123", params=None, json=None
        )

    async def test_messages_unread_uses_proxy(self, minimal_internal_app):
        canned = {"messages": [{"id": "m1", "type": "USER_MESSAGE"}]}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/messages/unread/agent-test-123")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/messages/unread/agent-test-123", params=None, json=None
        )

    async def test_messages_unread_count_uses_proxy(self, minimal_internal_app):
        canned = {"count": 3}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/messages/unread-count/agent-test-123")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/messages/unread-count/agent-test-123",
            params=None,
            json=None,
        )

    async def test_messages_unread_grouped_uses_proxy(self, minimal_internal_app):
        canned = {"messages_by_agent": {"agent-test-123": [{"id": "m1"}]}}
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value=canned)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/messages/unread-grouped")

        assert resp.status_code == 200
        assert resp.json() == canned
        mock_client.forward.assert_called_once_with(
            "GET", "/internal/messages/unread-grouped", params=None, json=None
        )

    async def test_proxy_http_error_is_mapped_to_same_status_and_detail(
        self, minimal_internal_app
    ):
        req = httpx.Request("GET", "http://orchestrator/internal/runtimes/list")
        resp = httpx.Response(
            status_code=503,
            request=req,
            json={"detail": "orchestrator unavailable"},
        )
        err = httpx.HTTPStatusError("bad gateway", request=req, response=resp)

        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(side_effect=err)

        with (
            patch.object(
                ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", "http://orchestrator:21000"
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/list")

        assert resp.status_code == 503
        assert resp.json() == {"detail": "orchestrator unavailable"}


@pytest.mark.asyncio
class TestLocalWhenNotConfigured:
    """When RUNTIME_ORCHESTRATOR_URL is not set, raises 500 (strict, no fallback); forward not called."""

    async def test_runtimes_list_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/list")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_active_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /runtimes/active returns envelope with empty runtimes."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/active")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_has_active_runtime_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /agents/.../has-active-runtime returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/agents/agent-x/subagents/sub-y/has-active-runtime"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagents_get_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /subagents/{agent_id}/{subagent_id} with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/subagents/agent-x/sub-nonexistent"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagents_hrl_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /subagents/{agent_id}/{subagent_id}/hrl returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/subagents/agent-x/sub-nonexistent/hrl"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_hrl_add_uses_local_forward_not_called(self, minimal_internal_app):
        """Local: POST hrl/add returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"runtime_id": "rt-new"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-x/sub-nonexistent/hrl/add",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_agents_notebook_summary_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /agents/{agent_id}/notebook-summary returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/agents/agent-notebook-local/notebook-summary"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagents_main_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /subagents/{agent_id}/main returns subagent envelope."""
        from gateway.db.access import get_db

        db = get_db()
        db.execute(
            "INSERT INTO agents (id, name) VALUES (?, ?)",
            ("agent-main-local", "Test Agent"),
        )

        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/subagents/agent-main-local/main"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagents_summary_lock_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /subagents/{agent_id}/{subagent_id}/summary-lock returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/subagents/agent-x/sub-nonexistent/summary-lock"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_summary_lock_acquire_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST summary-lock/acquire returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-x/sub-nonexistent/summary-lock/acquire"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_summary_lock_release_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST summary-lock/release returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-x/sub-nonexistent/summary-lock/release"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_merge_history_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST merge-history returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"new_history": "local merge", "remove_runtime_ids": ["rt-1"]}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-x/sub-nonexistent/merge-history",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_agents_drive_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /agents/{agent_id}/drive returns drive envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/agents/agent-drive-local/drive")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_agents_info_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /agents/{agent_id}/info returns default envelope when agent unknown."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/agents/agent-info-local/info")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_get_by_id_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /runtimes/{runtime_id} with non-existent runtime returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/rt-nonexistent")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_main_GET_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /runtimes/main/{agent_id} returns envelope with runtime: None."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/main/agent-nonexistent")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_subagent_GET_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /runtimes/subagent/{agent_id}/{subagent_id} returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/runtimes/subagent/agent-a/sub-nonexistent"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_latest_GET_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /runtimes/latest/{agent_id}/{subagent_id} returns envelope."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/runtimes/latest/agent-a/sub-1",
                    params={"limit": 10},
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagents_due_wake_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", ""),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/subagents/due-wake")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_unread_sent_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/messages/unread-sent/agent-local-456"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_batch_uses_local_forward_not_called(self, minimal_internal_app):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"runtime_ids": []}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/batch", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_get_or_create_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local path: missing agent_id returns 400; forward not called."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {}  # missing agent_id -> 400 before any DB/proxy

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/get-or-create", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_POST_uses_local_forward_not_called(self, minimal_internal_app):
        """Local path: POST /runtimes with missing agent_id returns 400; forward not called."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {}  # missing agent_id -> 400 before any DB/proxy

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_main_uses_local_forward_not_called(self, minimal_internal_app):
        """Local path: missing agent_id returns 400; forward not called."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {}  # missing agent_id -> 400 before any DB/proxy

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/runtimes/main", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_PATCH_uses_local_forward_not_called(self, minimal_internal_app):
        """Local path: PATCH /runtimes/{runtime_id} uses local; forward not called."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"phase": "running"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/runtimes/rt-nonexistent",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_vm_tools_GET_uses_local_forward_not_called(self, minimal_internal_app):
        """Local path: GET /runtimes/{runtime_id}/vm-tools with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/runtimes/rt-nonexistent/vm-tools",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_namespaces_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/memory/namespaces with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/memory/namespaces",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_recall_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/memory/recall with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"key": "k1", "namespace": "default"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/memory/recall",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_save_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/memory/save with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"key": "k1", "value": "v1", "namespace": "default"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/memory/save",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_delete_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/memory/delete with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"key": "k1", "namespace": "default"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/memory/delete",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_task_log_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/memory/task/log with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"action": "create", "details": "test", "status": "completed"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/memory/task/log",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_notebook_delete_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/notebook/delete with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"entry_id": "e1"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/notebook/delete",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_memory_task_history_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/memory/task/history with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"limit": 20}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/memory/task/history",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_chat_history_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/chat/history with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/chat/history",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_chat_event_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/chat/event with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"type": "AGENT_REPLY", "data": {"message": "Hello"}}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/chat/event",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_notebook_read_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/notebook/read with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"entry_id": "e1"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/notebook/read",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_notebook_list_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/notebook/list with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"limit": 10}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/notebook/list",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_notebook_write_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/notebook/write with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"title": "Note", "content": "text", "entry_type": "observation"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/notebook/write",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_notebook_update_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/notebook/update with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"entry_id": "e1", "content": "updated"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/notebook/update",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_drive_update_profile_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/drive/update-profile with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"key": "preference", "value": "value"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/drive/update-profile",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_drive_update_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/drive/update with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"relationship_delta": 0.1, "reason": "test"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/drive/update",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_chat_message_GET_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/chat/message/{message_id} with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/chat/message/msg-123",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_qemu_status_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/qemu/status with non-existent returns 404 or error body."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/qemu/status",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_qemu_ssh_exec_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/qemu/ssh-exec with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"command": "echo hi", "timeout": 10}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/qemu/ssh-exec",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_qemu_start_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/qemu/start with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"memory": "4096", "cpus": 4}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/qemu/start",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_qemu_shutdown_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/qemu/shutdown with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"graceful": True}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/qemu/shutdown",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_qemu_restart_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/qemu/restart with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"graceful": True}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/qemu/restart",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_subagent_status_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/subagent/.../status with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/subagent/sub-1/status",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_tasks_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /rt/{runtime_id}/tasks uses local; 404 when runtime not found."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/tasks",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_tasks_spawn_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/tasks/spawn uses local; 404 when runtime not found."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"task_type": "tool", "config": {}}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/tasks/spawn",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_subagent_spawn_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/subagent/spawn uses local; 404 when runtime not found."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"task": "Do something"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/subagent/spawn",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_subagent_cancel_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/subagent/{id}/cancel uses local; 404 when runtime not found."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/subagent/sub-1/cancel",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_subagent_report_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/subagent/report uses local; 404 when runtime not found."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"result": "Task done"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/subagent/report",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_drive_GET_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: GET /internal/rt/{runtime_id}/drive with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get(
                    "/internal/rt/rt-nonexistent/drive",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_rt_drive_get_POST_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        """Local: POST /rt/{runtime_id}/drive/get with non-existent returns 404."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/rt/rt-nonexistent/drive/get",
                    json={},
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_context_append_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"message": {"role": "user", "content": "hi"}}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/context/append",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_send_uses_local_forward_not_called(self, minimal_internal_app):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"message": "hello"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/send",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_rest_uses_local_forward_not_called(self, minimal_internal_app):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"reason": "test", "wake_triggers": [{"type": "user_response"}]}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/rest",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_wake_uses_local_forward_not_called(self, minimal_internal_app):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/wake",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_advance_uses_local_forward_not_called(self, minimal_internal_app):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"expected_round_num": 0}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/advance",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_set_status_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"expected_status": "active", "new_status": "completed"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/set-status",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_summarized_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/summarized",
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_need_rest_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"value": True}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/need-rest",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_tool_ports_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"ports": {"vmuse": 8080}}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/tool-ports",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_hot_cold_summary_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"hot_summary": "hot", "cold_summary": "cold"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/hot-cold-summary",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_history_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"limit": 50, "offset": 0}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/runtimes/rt-nonexistent/history",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_runtimes_delete_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.delete("/internal/runtimes/rt-nonexistent")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_mark_read_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"message_ids": []}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch("/internal/messages/mark-read", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_mark_processed_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"message_ids": []}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/messages/mark-processed", json=payload
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_inject_subagent_completed_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {}  # missing agent_id -> local validation error

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/messages/inject-subagent-completed", json=payload
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_inject_wake_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {}  # missing agent_id -> local validation error

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/messages/inject-wake", json=payload
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_create_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {
            "agent_id": "agent-local-create",
            "type": "USER_MESSAGE",
            "content": "test message",
        }

        # Insert agent so chat_messages FK constraint is satisfied
        from gateway.db.access import get_db

        db = get_db()
        db.execute(
            "INSERT INTO agents (id, name) VALUES (?, ?)",
            ("agent-local-create", "Test Agent"),
        )

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages", json=payload)

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_find_sending_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/messages/find-sending")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_messages_unread_grouped_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/messages/unread-grouped")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    # Subagent lifecycle local-mode (Phase 4 next batch)
    async def test_subagent_sleeping_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-local/sub-main/sleeping"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_awake_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", ""),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post("/internal/subagents/agent-local/sub-main/awake")

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_completed_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"result": "done"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-local/sub-main/completed",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_failed_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"error": "failed"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-local/sub-main/failed",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_cancel_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-local/nonexistent-sub/cancel"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_patch_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"historical_summary": "local update"}

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/subagents/agent-local/sub-main",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_summarizing_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-local/sub-main/summarizing"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_spawn_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()
        payload = {"task": "local spawn task"}
        from gateway.db.access import get_db

        db = get_db()
        db.execute(
            "INSERT INTO agents (id, name) VALUES (?, ?)",
            ("agent-spawn-local", "Test Agent"),
        )

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/subagents/agent-spawn-local/spawn",
                    json=payload,
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_subagent_delete_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.delete(
                    "/internal/subagents/agent-local/sub-to-delete"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()

    async def test_increment_drive_interaction_uses_local_forward_not_called(
        self, minimal_internal_app
    ):
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock()

        with (
            patch.object(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ) as mock_get,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=minimal_internal_app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/internal/agents/agent-local/drive/increment-interaction"
                )

        assert resp.status_code == 500
        assert "Runtime Orchestrator" in resp.json().get("detail", "")
        mock_get.assert_not_called()
        mock_client.forward.assert_not_called()
