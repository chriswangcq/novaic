"""
Process-level startup tests for strict Runtime Orchestrator dependency.

Validates:
1) Runtime Orchestrator process starts and serves /api/health.
2) Gateway fails fast when Runtime Orchestrator is unavailable.
"""

import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import httpx
import pytest
from .http_probe import local_get


def _find_free_port() -> int:
    """Find a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _base_env():
    """Base subprocess env with proxy bypass for localhost."""
    env = os.environ.copy()
    env["no_proxy"] = "localhost,127.0.0.1,::1"
    env["NO_PROXY"] = "localhost,127.0.0.1,::1"
    return env


def _backend_dir() -> Path:
    """Path to novaic-backend (project root for main_novaic.py)."""
    return Path(__file__).resolve().parents[2]


def _main_novaic_cmd() -> list:
    """Path to main_novaic.py entry point."""
    return [os.environ.get("PYTHON_EXE", "python"), str(_backend_dir() / "main_novaic.py")]


def _dummy_service_url(port: int) -> str:
    """Build a localhost service URL for required CLI args."""
    return f"http://127.0.0.1:{port}"


class TestRuntimeOrchestratorProcessHealth:
    """Runtime Orchestrator process starts and serves health."""

    def test_runtime_orchestrator_process_health(self):
        """Start runtime orchestrator, poll /api/health until healthy or 45s, assert healthy, terminate."""
        port = _find_free_port()
        data_dir = tempfile.mkdtemp(prefix="novaic-ro-test-")
        env = _base_env()
        env["NOVAIC_DATA_DIR"] = data_dir
        env["RUNTIME_ORCHESTRATOR_PORT"] = str(port)
        env["RUNTIME_ORCHESTRATOR_HOST"] = "127.0.0.1"

        cmd = _main_novaic_cmd() + [
            "runtime-orchestrator",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--data-dir", data_dir,
        ]
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(_backend_dir()),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            url = f"http://127.0.0.1:{port}/api/health"
            deadline = time.monotonic() + 45.0
            healthy = False
            while time.monotonic() < deadline:
                try:
                    resp = local_get(url, timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        assert data.get("status") == "ok"
                        assert "runtime-orchestrator" in data.get("service", "")
                        healthy = True
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                time.sleep(0.25)
            assert healthy, (
                f"Runtime Orchestrator /api/health did not become healthy within 45s (port {port})"
            )
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            try:
                import shutil
                shutil.rmtree(data_dir, ignore_errors=True)
            except Exception:
                pass


class TestGatewayFailsFastWithoutRuntimeOrchestrator:
    """Gateway must exit non-zero when Runtime Orchestrator is unreachable."""

    def test_gateway_fails_fast_without_runtime_orchestrator(self):
        """Gateway exits non-zero within 20s when RUNTIME_ORCHESTRATOR_URL points to unused port."""
        unused_port = _find_free_port()
        gateway_port = _find_free_port()
        queue_port = _find_free_port()
        tools_port = _find_free_port()
        vmcontrol_port = _find_free_port()
        file_service_port = _find_free_port()
        tool_result_port = _find_free_port()
        data_dir = tempfile.mkdtemp(prefix="novaic-gw-test-")
        env = _base_env()
        env["NOVAIC_DATA_DIR"] = data_dir
        env["RUNTIME_ORCHESTRATOR_URL"] = f"http://127.0.0.1:{unused_port}"
        env["NOVAIC_PORT"] = str(gateway_port)

        cmd = _main_novaic_cmd() + [
            "gateway",
            "--host", "127.0.0.1",
            "--port", str(gateway_port),
            "--data-dir", data_dir,
            "--runtime-orchestrator-url", _dummy_service_url(unused_port),
            "--queue-service-url", _dummy_service_url(queue_port),
            "--tools-server-url", _dummy_service_url(tools_port),
            "--vmcontrol-url", _dummy_service_url(vmcontrol_port),
            "--file-service-url", _dummy_service_url(file_service_port),
            "--tool-result-service-url", _dummy_service_url(tool_result_port),
        ]
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(_backend_dir()),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            exit_code = proc.wait(timeout=20)
            assert exit_code != 0, (
                f"Gateway should exit non-zero when Runtime Orchestrator unreachable; got exit_code={exit_code}"
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail(
                "Gateway did not exit within 20s when Runtime Orchestrator unreachable; "
                "expected strict fail-fast behavior"
            )
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            try:
                import shutil
                shutil.rmtree(data_dir, ignore_errors=True)
            except Exception:
                pass


class TestGatewayStartsWithRuntimeOrchestrator:
    """Gateway should boot and proxy /internal when orchestrator is healthy."""

    def test_gateway_starts_and_proxies_internal_with_runtime_orchestrator(self):
        ro_port = _find_free_port()
        gateway_port = _find_free_port()
        queue_port = _find_free_port()
        tools_port = _find_free_port()
        vmcontrol_port = _find_free_port()
        file_service_port = _find_free_port()
        tool_result_port = _find_free_port()
        data_dir = tempfile.mkdtemp(prefix="novaic-gw-ro-test-")

        base_env = _base_env()
        base_env["NOVAIC_DATA_DIR"] = data_dir

        ro_env = base_env.copy()
        ro_env["RUNTIME_ORCHESTRATOR_PORT"] = str(ro_port)
        ro_env["RUNTIME_ORCHESTRATOR_HOST"] = "127.0.0.1"

        gw_env = base_env.copy()
        gw_env["NOVAIC_PORT"] = str(gateway_port)
        gw_env["RUNTIME_ORCHESTRATOR_URL"] = f"http://127.0.0.1:{ro_port}"
        gw_env["RUNTIME_ORCHESTRATOR_PORT"] = str(ro_port)
        gw_env["RUNTIME_ORCHESTRATOR_HOST"] = "127.0.0.1"

        ro_cmd = _main_novaic_cmd() + [
            "runtime-orchestrator",
            "--host", "127.0.0.1",
            "--port", str(ro_port),
            "--data-dir", data_dir,
        ]
        gw_cmd = _main_novaic_cmd() + [
            "gateway",
            "--host", "127.0.0.1",
            "--port", str(gateway_port),
            "--data-dir", data_dir,
            "--runtime-orchestrator-url", _dummy_service_url(ro_port),
            "--queue-service-url", _dummy_service_url(queue_port),
            "--tools-server-url", _dummy_service_url(tools_port),
            "--vmcontrol-url", _dummy_service_url(vmcontrol_port),
            "--file-service-url", _dummy_service_url(file_service_port),
            "--tool-result-service-url", _dummy_service_url(tool_result_port),
        ]

        ro_proc = None
        gw_proc = None
        try:
            ro_proc = subprocess.Popen(
                ro_cmd,
                cwd=str(_backend_dir()),
                env=ro_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait Runtime Orchestrator health
            ro_health = f"http://127.0.0.1:{ro_port}/api/health"
            ro_deadline = time.monotonic() + 45.0
            while time.monotonic() < ro_deadline:
                try:
                    resp = local_get(ro_health, timeout=2.0)
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                time.sleep(0.25)
            else:
                pytest.fail("Runtime Orchestrator did not become healthy in 45s")

            gw_proc = subprocess.Popen(
                gw_cmd,
                cwd=str(_backend_dir()),
                env=gw_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait Gateway health
            gw_health = f"http://127.0.0.1:{gateway_port}/api/health"
            gw_deadline = time.monotonic() + 20.0
            while time.monotonic() < gw_deadline:
                try:
                    resp = local_get(gw_health, timeout=2.0)
                    if resp.status_code == 200:
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                # Fail early if process exited unexpectedly
                if gw_proc.poll() is not None:
                    pytest.fail(
                        f"Gateway exited early with code {gw_proc.returncode} while waiting for health"
                    )
                time.sleep(0.25)
            else:
                pytest.fail("Gateway did not become healthy in 20s")

            # Runtime routes are RO-owned and removed from Gateway internals.
            # Verify architecture contract still holds after both services start.
            proxy_resp = local_get(
                f"http://127.0.0.1:{gateway_port}/internal/runtimes/list",
                timeout=3.0,
            )
            assert proxy_resp.status_code == 404
        finally:
            for proc in (gw_proc, ro_proc):
                if proc is not None and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            try:
                import shutil
                shutil.rmtree(data_dir, ignore_errors=True)
            except Exception:
                pass
