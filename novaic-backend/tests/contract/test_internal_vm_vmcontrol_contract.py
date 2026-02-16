"""
Internal VM/Runtime Contract Tests (Phase3 vmcontrol source-of-truth)

Validates internal endpoints that depend on vmcontrol enforce unified contract:
- All qemu endpoints (status, start, stop, restart): 200 + success/error body.
- vmcontrol unavailable: 200, success: false, error mentions vmcontrol (no HTTP 5xx, no local fallback).
- Uses mocks/stubs for vmcontrol client; no external services
"""

import sys
import os

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Stub deployer before gateway.api.vm is imported (deployer requires paramiko)
_stub_deployer = MagicMock()
_stub_deployer.deploy = MagicMock(return_value={"success": True})
_stub_deployer.health_check = MagicMock(return_value=True)
_fake_deployer_module = type(sys)("gateway.vm.deployer")
_fake_deployer_module.get_vmuse_deployer = lambda: _stub_deployer
sys.modules["gateway.vm.deployer"] = _fake_deployer_module


def _make_mock_vmcontrol_raises():
    """Mock vmcontrol client that raises on any call (unavailable)."""
    mock = MagicMock()
    mock.health_check = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.get_vm_info = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.list_vms = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.register_vm = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.shutdown_vm = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    mock.shutdown_all_vms = AsyncMock(side_effect=Exception("vmcontrol unavailable"))
    return mock


def _make_mock_vmcontrol_healthy():
    """Mock vmcontrol client that returns healthy data."""
    mock = MagicMock()
    mock.health_check = AsyncMock(return_value=True)
    mock.get_vm_info = AsyncMock(
        return_value={
            "id": "agent-ct-test",
            "status": "running",
            "pid": 12345,
            "started_at": "2025-01-01T00:00:00",
            "error_message": None,
        }
    )
    mock.list_vms = AsyncMock(return_value=[{"id": "agent-ct-test", "status": "running"}])
    mock.register_vm = AsyncMock(return_value={"id": "agent-ct-test", "status": "registered"})
    mock.shutdown_vm = AsyncMock(return_value={"success": True})
    mock.shutdown_all_vms = AsyncMock(return_value={})
    return mock


@pytest.fixture
def internal_vm_app():
    """Minimal FastAPI app with internal router (vm/runtime endpoints)."""
    import tempfile
    from pathlib import Path
    from common.db import Database
    from gateway.api.internal import router as internal_router
    from gateway.db import access as db_access
    from gateway.db.schema import init_schema_sync

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    prev_process_flag = os.environ.get("NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS")
    os.environ["NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS"] = "true"
    try:
        db = Database(db_path)
        db.connect(init_schema_func=init_schema_sync)
        orig = db_access._database
        db_access._database = db

        # Reset agent config manager singleton so it uses our patched db
        import gateway.config.agents_db as agents_db_module
        agents_db_module._agent_config_manager = None

        # Seed agent, subagent, runtime for resolve_runtime_ids and get_agent
        from common.utils.time import utc_now_iso
        from gateway.db.repositories import RuntimeRepository
        from gateway.db.repositories.subagent import SubAgentRepository

        now = utc_now_iso()
        with db.transaction("agent", resource_id="agent-ct-test"):
            db.execute(
                "INSERT OR IGNORE INTO agents (id, name, vm_config, ports) VALUES (?, ?, ?, ?)",
                ("agent-ct-test", "Test Agent", "{}", '{"ssh": 20000, "vmuse": 18000}'),
            )
        # Create subagent (main subagent_id = main-{agent_id[:8]} = main-agent-ct)
        sub_repo = SubAgentRepository(db)
        sub_repo.get_or_create_main_subagent("agent-ct-test")
        subagent_id = "main-agent-ct"  # main-{agent-ct-test[:8]}
        # Create runtime with fixed id for tests
        with db.transaction("agent", resource_id="rt-ct-vm-001"):
            db.execute(
                """INSERT OR REPLACE INTO agent_runtimes
                   (runtime_id, subagent_id, agent_id, mcp_url, current_round_id, current_round_num,
                    phase, context, pending_actions, status, error, summary, is_merged,
                    summarized, need_rest, simple_summary, hot_summary, cold_summary,
                    tool_ports, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "rt-ct-vm-001", subagent_id, "agent-ct-test", None, "round-1", 1,
                    "thinking", "[]", "[]", "active", None, None, 0,
                    0, 0, None, None, None,
                    None, now, now,
                ),
            )

        app = FastAPI()
        app.include_router(internal_router)
        yield app
    finally:
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
def internal_vm_client(internal_vm_app):
    """Async HTTP client for internal VM/runtime API."""
    return AsyncClient(
        transport=ASGITransport(app=internal_vm_app),
        base_url="http://test",
    )


@pytest.mark.asyncio
class TestInternalQemuStatusVmcontrolUnavailable:
    """
    Contract: GET /internal/rt/{runtime_id}/qemu/status when vmcontrol unavailable
    returns 200 + success:false + error (unified contract, no HTTP 5xx, no local fallback).
    """

    async def test_qemu_status_vmcontrol_unavailable_returns_structured_error(
        self, internal_vm_client
    ):
        with patch(
            "gateway.clients.vmcontrol.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_raises(),
        ):
            resp = await internal_vm_client.get(
                "/internal/rt/rt-ct-vm-001/qemu/status"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False
        assert "error" in data
        assert "vmcontrol" in (data.get("error") or "").lower()

    async def test_qemu_status_vmcontrol_connection_error_returns_structured_error(
        self, internal_vm_client
    ):
        """Any vmcontrol failure (connection refused, etc.) → 200 + success:false."""
        mock = MagicMock()
        mock.get_vm_info = AsyncMock(
            side_effect=Exception("Connection refused to vmcontrol")
        )
        with patch(
            "gateway.clients.vmcontrol.get_vmcontrol_client",
            return_value=mock,
        ):
            resp = await internal_vm_client.get(
                "/internal/rt/rt-ct-vm-001/qemu/status"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False
        assert "error" in data
        err = (data.get("error") or "").lower()
        assert "vmcontrol" in err or "connection" in err or "refused" in err


@pytest.mark.asyncio
class TestInternalQemuStatusVmcontrolHealthy:
    """When vmcontrol is healthy (mocked), status returns structured envelope."""

    async def test_qemu_status_vmcontrol_healthy_returns_envelope(
        self, internal_vm_client
    ):
        with patch(
            "gateway.clients.vmcontrol.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await internal_vm_client.get(
                "/internal/rt/rt-ct-vm-001/qemu/status"
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True
        assert "qemu_running" in data
        assert "qemu_pid" in data
        assert "agent_id" in data
        assert data.get("qemu_running") is True
        assert data.get("agent_id") == "agent-ct-test"


@pytest.mark.asyncio
class TestInternalQemuStartVmcontrolUnavailable:
    """
    Contract: POST /internal/rt/{runtime_id}/qemu/start when vmcontrol unavailable
    returns structured error (success: false, error mentions vmcontrol).
    No local fallback; start fails.
    """

    async def test_qemu_start_vmcontrol_unavailable_returns_structured_error(
        self, internal_vm_client
    ):
        mock_manager = MagicMock()
        mock_manager.start = MagicMock(
            side_effect=RuntimeError("vmcontrol registration failed: vmcontrol unavailable")
        )
        with patch(
            "gateway.vm.get_vm_manager",
            return_value=mock_manager,
        ):
            resp = await internal_vm_client.post(
                "/internal/rt/rt-ct-vm-001/qemu/start",
                json={"memory": "4096", "cpus": 4},
            )
        # Endpoint catches Exception and returns 200 with success: false
        # (Contract: no local fallback; start fails with structured error)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False
        assert "error" in data
        assert "vmcontrol" in (data.get("error") or "").lower()


@pytest.mark.asyncio
class TestInternalQemuShutdownRestartUnifiedContract:
    """
    Contract: shutdown and restart use same 200 + success/error body pattern.
    """

    async def test_qemu_shutdown_failure_returns_structured_error(
        self, internal_vm_client
    ):
        mock_manager = MagicMock()
        mock_manager.stop = MagicMock(
            side_effect=RuntimeError("SSH connection failed")
        )
        with patch(
            "gateway.vm.get_vm_manager",
            return_value=mock_manager,
        ):
            resp = await internal_vm_client.post(
                "/internal/rt/rt-ct-vm-001/qemu/shutdown",
                json={"graceful": True},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False
        assert "error" in data

    async def test_qemu_restart_start_failure_returns_structured_error(
        self, internal_vm_client
    ):
        """Restart fails at start phase (e.g. vmcontrol) → same structured error as start."""
        mock_manager = MagicMock()
        mock_manager.stop = MagicMock(return_value={"status": "stopped"})
        mock_manager.start = MagicMock(
            side_effect=RuntimeError("vmcontrol registration failed: vmcontrol unavailable")
        )
        with patch(
            "gateway.vm.get_vm_manager",
            return_value=mock_manager,
        ):
            resp = await internal_vm_client.post(
                "/internal/rt/rt-ct-vm-001/qemu/restart",
                json={"graceful": True},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is False
        assert "error" in data
        assert "vmcontrol" in (data.get("error") or "").lower()


@pytest.mark.asyncio
class TestInternalQemuStatus404ForMissing:
    """404 behavior for missing runtime (not a vmcontrol test, but contract sanity)."""

    async def test_qemu_status_404_for_nonexistent_runtime(
        self, internal_vm_client
    ):
        with patch(
            "gateway.clients.vmcontrol.get_vmcontrol_client",
            return_value=_make_mock_vmcontrol_healthy(),
        ):
            resp = await internal_vm_client.get(
                "/internal/rt/rt-nonexistent-xyz-999/qemu/status"
            )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "not found" in (data.get("detail") or "").lower()
