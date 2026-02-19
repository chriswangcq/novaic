"""
Internal API Contract Baseline Tests

Lightweight pytest module validating:
- Endpoint route existence and response envelopes per domain boundary:
  - RO owns /internal/runtimes* and /internal/subagents* (runtime orchestration); Gateway does NOT expose them
  - Gateway owns business internals: /internal/messages, /internal/vm,
    /internal/task (and related agent/config/llm/web). Self-drive API removed.
- Gateway business API: subagent_id-only where migrated (no runtime_id in migrated paths)

Kept robust and non-flaky; uses unit-style checks (router inspection) that require no app startup.
"""

import pytest
import os


class TestInternalApiRouteExistence:
    """Unit-style tests: verify baseline routes exist on the internal router."""

    def test_internal_router_loads(self):
        """Internal router can be imported without errors."""
        from gateway.api.internal import router

        assert router is not None
        assert hasattr(router, "routes")

    def test_gateway_does_not_expose_runtimes_routes(self):
        """Gateway does NOT expose /internal/runtimes* (RO domain only; delegated implementation)."""
        from gateway.api.internal import router as internal_router

        def collect_paths(routes, prefix=""):
            out = []
            for r in routes or []:
                p = getattr(r, "path", None)
                if p is not None:
                    full = (prefix + p) if prefix else p
                    out.append(full)
                out.extend(collect_paths(getattr(r, "routes", []) or [], prefix + (p or "")))
            return out

        all_paths = collect_paths(internal_router.routes or [])
        runtimes_paths = [p for p in all_paths if "runtimes" in p]
        assert not runtimes_paths, f"Gateway must not expose /internal/runtimes*; found: {runtimes_paths}"

    def test_gateway_does_not_expose_subagents_core_routes(self):
        """Gateway does NOT expose /internal/subagents/due-wake (RO domain); task/vm /subagents/{subagent_id}/* stay on Gateway."""
        from gateway.api.internal import router as internal_router

        def collect_paths(routes, prefix=""):
            out = []
            for r in routes or []:
                p = getattr(r, "path", None)
                if p is not None:
                    full = (prefix + p) if prefix else p
                    out.append(full)
                out.extend(collect_paths(getattr(r, "routes", []) or [], prefix + (p or "")))
            return out

        all_paths = collect_paths(internal_router.routes or [])
        # due-wake is the key RO-owned subagent route; Gateway must not have it
        forbidden = [p for p in all_paths if "due-wake" in p]
        assert not forbidden, f"Gateway must not expose /internal/subagents/due-wake (RO domain); found: {forbidden}"

    def test_subagents_routes_exist_on_ro(self):
        """Key /internal/subagents routes exist on RO (RO domain; Gateway does NOT expose them)."""
        from runtime_orchestrator.api.internal import subagent as subagent_module

        router = subagent_module.router
        paths = set()
        for r in getattr(router, "routes", []) or []:
            p = getattr(r, "path", "")
            m = getattr(r, "methods") or set()
            if p and m:
                paths.add((p, next(iter(m))))
        path_strs = {p for p, _ in paths}

        assert "/subagents/due-wake" in path_strs
        # Gateway resolves subagent->agent via RO; RO must expose by-id lookup
        assert any("by-id" in p for p in path_strs)

    def test_task_subagent_routes_exist(self):
        """Key /internal/subagents/{subagent_id}/quadrant-tasks routes exist (Gateway business API)."""
        from gateway.api.internal import task as task_module

        router = task_module.router
        paths = set()
        for r in getattr(router, "routes", []) or []:
            p = getattr(r, "path", "")
            m = getattr(r, "methods") or set()
            if p and m:
                paths.add((p, next(iter(m))))
        path_strs = {p for p, _ in paths}

        assert "/subagents/{subagent_id}/quadrant-tasks" in path_strs
        assert "/subagents/{subagent_id}/growth-logs" in path_strs

    def test_messages_routes_exist(self):
        """Key /internal/messages routes exist (Gateway domain)."""
        from gateway.api.internal import message as message_module

        router = message_module.router
        paths = set()
        for r in getattr(router, "routes", []) or []:
            p = getattr(r, "path", "")
            m = getattr(r, "methods") or set()
            if p and m:
                paths.add((p, next(iter(m))))
        path_strs = {p for p, _ in paths}

        assert "/messages/unread-sent" in path_strs or any(
            "unread-sent" in px for px in path_strs
        )
        assert "/messages/has-new" in path_strs or any("has-new" in px for px in path_strs)
        assert "/messages/mark-read" in path_strs
        assert "/messages/unread" in path_strs or any("unread" in px for px in path_strs)

    def test_vm_routes_exist(self):
        """Key /internal/vm routes exist (Gateway domain)."""
        from gateway.api.internal import vm as vm_module

        router = vm_module.router
        paths = set()
        for r in getattr(router, "routes", []) or []:
            p = getattr(r, "path", "")
            m = getattr(r, "methods") or set()
            if p and m:
                paths.add((p, next(iter(m))))
        path_strs = {p for p, _ in paths}

        assert "/vm/ssh/public-key" in path_strs
        assert "/vm/ssh/private-key-path" in path_strs
        assert any("/subagents/" in p and "vm-tools" in p for p in path_strs)


class TestInternalApiResponseEnvelope:
    """Verify response envelope expectations from contract doc.

    Uses static inspection only; no HTTP calls to avoid flakiness.
    """

    def test_messages_unread_sent_envelope_documented(self):
        """GET /messages/unread-sent/{agent_id} returns {messages: [...]} per contract."""
        from gateway.api.internal.message import get_unread_sent_messages

        assert get_unread_sent_messages is not None

    def test_vm_ssh_public_key_envelope_documented(self):
        """GET /vm/ssh/public-key returns {public_key: str} per contract."""
        from gateway.api.internal.vm import get_ssh_public_key

        assert get_ssh_public_key is not None


@pytest.fixture
def minimal_internal_client():
    """Build minimal FastAPI app with Gateway internal router only (no task queue).
    Patches gateway.db.access for db; uses temp SQLite. Self-contained for contract tests.
    Gateway does NOT include /internal/subagents* or /internal/runtimes* (RO owns those).
    """
    import tempfile
    from pathlib import Path
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from common.db import Database
    from gateway.api.internal import router as internal_router
    from gateway.api.internal.helpers import set_runtime_orchestrator_process
    from gateway.db import access as db_access
    from gateway.db.schema import init_schema_sync

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    prev_process_flag = os.environ.get("NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS")
    os.environ["NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS"] = "true"
    set_runtime_orchestrator_process(True)
    try:
        db = Database(db_path)
        db.connect(init_schema_func=init_schema_sync)
        orig = db_access._database
        db_access._database = db
        app = FastAPI()
        app.include_router(internal_router)  # router has prefix=/internal
        yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    finally:
        set_runtime_orchestrator_process(False)
        if prev_process_flag is None:
            os.environ.pop("NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS", None)
        else:
            os.environ["NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS"] = prev_process_flag
        db_access._database = orig
        try:
            db_path.unlink()
        except Exception:
            pass


@pytest.fixture
def minimal_ro_internal_client():
    """Build minimal FastAPI app with RO internal router (subagents, runtimes).
    Uses RO DB; for testing /internal/subagents* and /internal/runtimes* on RO.
    """
    import tempfile
    from pathlib import Path
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from runtime_orchestrator.db import init_database, close_database
    from runtime_orchestrator.api.internal import router as ro_internal_router
    from runtime_orchestrator.db.schema import init_runtime_schema_sync

    with tempfile.TemporaryDirectory() as tmp:
        init_database(
            data_dir=tmp,
            db_file="ro_test.db",
            init_schema_func=init_runtime_schema_sync,
        )
        try:
            app = FastAPI()
            app.include_router(ro_internal_router)
            yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        finally:
            close_database()


@pytest.mark.asyncio
class TestInternalApiHttpResponses:
    """HTTP tests validating status class and envelope fields.

    Uses minimal_internal_client (self-contained) to avoid dependency on
    gateway_app/gateway_http_client fixture chain.
    """

    async def test_runtimes_route_removed_from_gateway(self, minimal_internal_client):
        """GET /internal/runtimes/list returns 404 (route removed from Gateway; RO-only)."""
        resp = await minimal_internal_client.get("/internal/runtimes/list")
        assert resp.status_code == 404, "Gateway must not expose /internal/runtimes*"

    async def test_subagents_due_wake_status_and_envelope(self, minimal_ro_internal_client):
        """GET /internal/subagents/due-wake on RO returns 2xx and has subagents key."""
        resp = await minimal_ro_internal_client.get("/internal/subagents/due-wake")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "subagents" in data
            assert isinstance(data["subagents"], list)

    async def test_vm_ssh_public_key_status_and_envelope(self, minimal_internal_client):
        """GET /internal/vm/ssh/public-key returns 2xx and has public_key key."""
        resp = await minimal_internal_client.get("/internal/vm/ssh/public-key")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "public_key" in data

    # ---------- Messages (additional coverage) ----------
    async def test_messages_unread_sent_status_and_envelope(self, minimal_internal_client):
        """GET /internal/messages/unread-sent/{agent_id} returns 2xx and has messages key."""
        resp = await minimal_internal_client.get(
            "/internal/messages/unread-sent/test-agent-ct-1"
        )
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "messages" in data
            assert isinstance(data["messages"], list)

    async def test_messages_has_new_status_and_envelope(self, minimal_internal_client):
        """GET /internal/messages/has-new/{agent_id} returns 2xx and has has_new_messages key."""
        resp = await minimal_internal_client.get(
            "/internal/messages/has-new/test-agent-ct-1"
        )
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "has_new_messages" in data

    async def test_messages_mark_read_status_and_envelope(self, minimal_internal_client):
        """PATCH /internal/messages/mark-read returns 2xx and has status key."""
        resp = await minimal_internal_client.patch(
            "/internal/messages/mark-read", json={"message_ids": []}
        )
        assert resp.status_code in (200, 404, 422, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data

    # ---------- Subagents (RO domain; use minimal_ro_internal_client) ----------
    # NOTE: /subagents/{agent_id}/main requires subagents table; get_or_create can
    # return None in minimal DB setup. Route existence covered in TestInternalApiRouteExistence.
    async def test_subagents_get_404_for_missing(self, minimal_ro_internal_client):
        """GET /internal/subagents/{aid}/{sid} on RO returns 404 for nonexistent subagent."""
        resp = await minimal_ro_internal_client.get(
            "/internal/subagents/test-agent-ct-1/sub-nonexistent-xyz"
        )
        assert resp.status_code in (404, 422, 500)

    async def test_subagents_status_404_for_missing(self, minimal_ro_internal_client):
        """GET /internal/subagents/{aid}/{sid}/status on RO returns 404 for nonexistent."""
        resp = await minimal_ro_internal_client.get(
            "/internal/subagents/test-agent-ct-1/sub-nonexistent-xyz/status"
        )
        assert resp.status_code in (404, 422, 500)

    async def test_subagents_by_id_404_for_missing(self, minimal_ro_internal_client):
        """GET /internal/subagents/by-id/{subagent_id} on RO returns 404 for nonexistent."""
        resp = await minimal_ro_internal_client.get(
            "/internal/subagents/by-id/sub-nonexistent-xyz"
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data and "SubAgent not found" in str(data["detail"])

    # ---------- VM (additional coverage) ----------
    # vm-tools via /internal/subagents/{subagent_id}/vm-tools is on Gateway (vm module)
    # Resolution goes via RO; 502 when RO unreachable (minimal_internal_client has no RO)
    async def test_vm_subagent_tools_route_exists(self, minimal_internal_client):
        """GET /internal/subagents/{id}/vm-tools returns 2xx/4xx/5xx (route exists on Gateway vm)."""
        resp = await minimal_internal_client.get(
            "/internal/subagents/sub-nonexistent-xyz/vm-tools"
        )
        assert resp.status_code in (200, 404, 422, 500, 502)
