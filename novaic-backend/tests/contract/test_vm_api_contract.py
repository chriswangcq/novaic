"""
VM API Contract Tests

Validates /api/vm endpoints enforce vmcontrol-only behavior expectations.
- Route existence and response semantics for representative VM API endpoints
- vmcontrol unavailable MUST return error (no local fallback)
- Non-flaky: mocks vmcontrol client to avoid external service dependency
"""

import sys

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Stub deployer before importing gateway.api.vm (deployer requires paramiko)
_stub_deployer = MagicMock()
_stub_deployer.deploy = MagicMock(return_value={"success": True})
_stub_deployer.health_check = MagicMock(return_value=True)
_fake_deployer_module = type(sys)("gateway.vm.deployer")
_fake_deployer_module.get_vmuse_deployer = lambda: _stub_deployer
sys.modules["gateway.vm.deployer"] = _fake_deployer_module


def _collect_vm_routes():
    """Collect path and methods from VM router (paths include /api/vm prefix)."""
    from gateway.api.vm import router

    paths = set()
    for r in getattr(router, "routes", []) or []:
        p = getattr(r, "path", "")
        m = getattr(r, "methods") or set()
        if p and m:
            for method in m:
                paths.add((p, method))
    return paths


def _make_mock_vmcontrol_healthy():
    """Mock vmcontrol client that returns healthy data."""
    mock = MagicMock()
    mock.health_check = AsyncMock(return_value=True)
    mock.get_vm_info = AsyncMock(
        return_value={
            "id": "test-agent-001",
            "status": "running",
            "pid": 12345,
            "started_at": "2025-01-01T00:00:00",
            "error_message": None,
        }
    )
    mock.list_vms = AsyncMock(
        return_value=[
            {"id": "test-agent-001", "status": "running", "pid": 12345},
        ]
    )
    mock.shutdown_vm = AsyncMock(return_value={"success": True})
    mock.shutdown_all_vms = AsyncMock(return_value={})
    return mock


def _make_mock_vmcontrol_unavailable():
    """Mock vmcontrol client that simulates unavailable service."""
    mock = MagicMock()
    mock.health_check = AsyncMock(return_value=False)
    mock.get_vm_info = AsyncMock(side_effect=Exception("connection refused"))
    mock.list_vms = AsyncMock(side_effect=Exception("connection refused"))
    mock.shutdown_vm = AsyncMock(side_effect=Exception("connection refused"))
    mock.shutdown_all_vms = AsyncMock(side_effect=Exception("connection refused"))
    return mock


def _make_mock_vmcontrol_raises():
    """Mock vmcontrol that raises on any call (generic error)."""
    mock = MagicMock()
    mock.health_check = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.get_vm_info = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.list_vms = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.shutdown_vm = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.shutdown_all_vms = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    return mock


@pytest.fixture
def minimal_vm_app():
    """Build minimal FastAPI app with VM router only."""
    from fastapi import FastAPI
    from gateway.api.vm import router as vm_router
    from httpx import AsyncClient, ASGITransport

    app = FastAPI()
    app.include_router(vm_router)
    return app


@pytest.fixture
def vm_client(minimal_vm_app):
    """Async HTTP client for VM API."""
    from httpx import AsyncClient, ASGITransport

    return AsyncClient(
        transport=ASGITransport(app=minimal_vm_app),
        base_url="http://test",
    )


class TestVmApiRouteExistence:
    """Verify VM API routes exist on the router (paths include /api/vm prefix)."""

    def test_vm_status_agent_route_exists(self):
        paths = _collect_vm_routes()
        path_strs = {p for p, _ in paths}
        assert any("/status/" in p and "{agent_id}" in p for p in path_strs)

    def test_vm_status_route_exists(self):
        paths = _collect_vm_routes()
        path_strs = {p for p, _ in paths}
        assert any(p.endswith("/status") or p == "/status" for p in path_strs)

    def test_vm_running_route_exists(self):
        paths = _collect_vm_routes()
        path_strs = {p for p, _ in paths}
        assert any("/running" in p for p in path_strs)

    def test_vm_is_running_route_exists(self):
        paths = _collect_vm_routes()
        path_strs = {p for p, _ in paths}
        assert any("/is-running/" in p for p in path_strs)

    def test_vm_vnc_status_route_exists(self):
        paths = _collect_vm_routes()
        path_strs = {p for p, _ in paths}
        assert any("/vnc/status/" in p for p in path_strs)

    def test_vm_stop_route_exists(self):
        paths = _collect_vm_routes()
        methods = {(p, m) for p, m in paths}
        assert any("/stop" in p and m == "POST" for p, m in methods)

    def test_vm_stop_all_route_exists(self):
        paths = _collect_vm_routes()
        methods = {(p, m) for p, m in paths}
        assert any("stop-all" in p and m == "POST" for p, m in methods)


@pytest.mark.asyncio
class TestVmApiVmcontrolUnavailableReturnsError:
    """
    Contract: vmcontrol unavailable MUST return error (HTTP 5xx), NOT local fallback.
    """

    async def test_status_agent_id_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.get("/api/vm/status/test-agent-001")
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        assert "vmcontrol" in data["detail"].lower()

    async def test_status_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.get("/api/vm/status")
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        assert "vmcontrol" in data["detail"].lower()

    async def test_running_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.get("/api/vm/running")
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        assert "vmcontrol" in data["detail"].lower()

    async def test_is_running_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.get("/api/vm/is-running/test-agent-001")
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        assert "vmcontrol" in data["detail"].lower()

    async def test_vnc_status_vmcontrol_unhealthy_returns_available_false(
        self, vm_client, minimal_vm_app
    ):
        """VNC status when vmcontrol unhealthy returns available=False, reason mentions VmControl."""
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_unavailable(),
        ):
            resp = await vm_client.get("/api/vm/vnc/status/test-agent-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("available") is False
        assert data.get("vmcontrol_healthy") is False
        assert "vmcontrol" in (data.get("reason") or "").lower() or "VmControl" in (
            data.get("reason") or ""
        )

    async def test_stop_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.post(
                "/api/vm/stop",
                json={"agent_id": "test-agent-001"},
            )
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data
        assert "vmcontrol" in (data["detail"] or "").lower()

    async def test_stop_all_vmcontrol_unavailable_returns_500(
        self, vm_client, minimal_vm_app
    ):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await vm_client.post("/api/vm/stop-all")
        assert resp.status_code == 500
        data = resp.json()
        assert "detail" in data


@pytest.mark.asyncio
class TestVmApiResponseSemantics:
    """Verify response envelope and semantics when vmcontrol is healthy (mocked)."""

    async def test_status_agent_id_returns_envelope(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.get("/api/vm/status/test-agent-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "agent_id" in data
        assert "running" in data
        assert "ports" in data
        assert "vnc_url" in data
        assert "ws://" in data.get("vnc_url", "")

    async def test_status_returns_dict_envelope(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.get("/api/vm/status")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "test-agent-001" in data
        entry = data["test-agent-001"]
        assert "agent_id" in entry
        assert "running" in entry
        assert "vnc_url" in entry

    async def test_running_returns_agents_list(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.get("/api/vm/running")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert "test-agent-001" in data["agents"]

    async def test_is_running_returns_running_flag(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.get("/api/vm/is-running/test-agent-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert data["running"] is True

    async def test_vnc_status_returns_full_envelope(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.get("/api/vm/vnc/status/test-agent-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data
        assert "vmcontrol_healthy" in data
        assert "vm_registered" in data
        assert "vm_running" in data
        assert "vnc_url" in data

    async def test_stop_returns_success_envelope(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.post(
                "/api/vm/stop",
                json={"agent_id": "test-agent-001"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        assert "status" in data

    async def test_stop_all_returns_success_envelope(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.post("/api/vm/stop-all")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        assert "results" in data


@pytest.mark.asyncio
class TestVmApiStopAllRouteAndParams:
    """Verify /api/vm/stop-all route accepts query params (quick, graceful)."""

    async def test_stop_all_accepts_quick_param(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.post("/api/vm/stop-all?quick=true")
        assert resp.status_code == 200

    async def test_stop_all_accepts_graceful_param(self, vm_client, minimal_vm_app):
        with patch(
            "gateway.api.vm.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await vm_client.post("/api/vm/stop-all?graceful=false")
        assert resp.status_code == 200
