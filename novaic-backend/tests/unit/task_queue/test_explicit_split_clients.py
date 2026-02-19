"""
Unit tests for explicit split clients (GatewayBusinessClient, RuntimeOrchestratorClient).

Verifies that main worker paths use explicit clients and hit the correct URLs:
- GatewayBusinessClient: Gateway-owned routes (/internal/messages*, /api/*)
- RuntimeOrchestratorClient: RO-owned routes (/internal/runtimes*, /internal/subagents*)
"""

from unittest.mock import Mock, patch
import httpx
import pytest

from task_queue.client import GatewayBusinessClient, RuntimeOrchestratorClient
from task_queue.exceptions import TaskQueueError


class _FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload
        self.text = '{"ok": true}'

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.calls = []

    def request(self, method, url, json=None, params=None):
        self.calls.append({"method": method, "url": url, "json": json, "params": params})
        return _FakeResponse({"ok": True, "runtime": {"runtime_id": "rt-1"}, "messages": []})


def test_runtime_orchestrator_client_hits_ro_url():
    """RuntimeOrchestratorClient.get_runtime hits RO base_url."""
    client = RuntimeOrchestratorClient("http://ro:19993")
    fake = _FakeSession()
    with patch.object(client, "_get_session", return_value=fake):
        client.get_runtime("rt-1")
    assert fake.calls[0]["url"] == "http://ro:19993/internal/runtimes/rt-1"


def test_gateway_business_client_hits_gateway_url():
    """GatewayBusinessClient.broadcast_log hits Gateway base_url."""
    client = GatewayBusinessClient("http://gateway:19999")
    fake = _FakeSession()
    with patch.object(client, "_get_session", return_value=fake):
        client.broadcast_log(agent_id="agent-1", log_type="TEST", data={"x": 1})
    assert fake.calls[0]["url"] == "http://gateway:19999/api/logs/broadcast"


def test_gateway_business_client_find_sending_hits_messages():
    """GatewayBusinessClient.find_sending_message hits /internal/messages (Gateway)."""
    client = GatewayBusinessClient("http://gateway:19999")
    fake = _FakeSession()
    with patch.object(client, "_get_session", return_value=fake):
        client.find_sending_message()
    assert "internal/messages/find-sending" in fake.calls[0]["url"]


def test_gateway_business_client_recover_all_hits_queue_service():
    """GatewayBusinessClient.recover_all targets Queue Service /api/queue/recover/all."""
    from unittest.mock import patch, MagicMock

    client = GatewayBusinessClient("http://gateway:19999", queue_service_url="http://queue:19997")
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {"tasks_recovered": 1, "sagas_recovered": 0}

    with patch("task_queue.client.internal_client") as mock_internal:
        mock_http = MagicMock()
        mock_http.post.return_value = fake_resp
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=None)
        mock_internal.return_value = mock_http

        result = client.recover_all(task_timeout=60, saga_timeout=300)

    assert result == {"tasks_recovered": 1, "sagas_recovered": 0}
    mock_http.post.assert_called_once()
    call_args = mock_http.post.call_args
    assert call_args[0][0] == "/api/queue/recover/all"
    assert call_args[1]["params"] == {"task_timeout": 60, "saga_timeout": 300}


def test_gateway_business_client_recover_all_raises_when_no_queue_url():
    """GatewayBusinessClient.recover_all raises when queue_service_url is empty."""
    client = GatewayBusinessClient("http://gateway:19999", queue_service_url="")
    with pytest.raises(TaskQueueError, match="QUEUE_SERVICE_URL not configured"):
        client.recover_all()


def test_gateway_business_client_get_all_memory_hits_gateway():
    """GatewayBusinessClient.get_all_memory hits Gateway /internal/agents/{id}/memory/all."""
    client = GatewayBusinessClient("http://gateway:19999")
    fake = _FakeSession()
    with patch.object(client, "_get_session", return_value=fake):
        client.get_all_memory("agent-1")
    assert fake.calls[0]["url"] == "http://gateway:19999/internal/agents/agent-1/memory/all"


def test_task_worker_ctx_has_explicit_clients():
    """TaskWorkerSync passes gateway_client and ro_client in ctx."""
    import os
    from common.config import ServiceConfig
    from task_queue.workers.task_worker_sync import TaskWorkerSync

    with patch.dict(os.environ, {"RUNTIME_ORCHESTRATOR_URL": "http://ro:19993"}):
        worker = TaskWorkerSync(
            topics=["test"],
            queue_service_url="http://qs:8716",
            gateway_url="http://gw:19999",
        )
    assert hasattr(worker, "gateway_client")
    assert hasattr(worker, "ro_client")
    assert worker.gateway_client.base_url == "http://gw:19999"
    # TaskWorkerSync currently reads RO URL from ServiceConfig (loaded config), not patched env.
    assert worker.ro_client.base_url == (ServiceConfig.RUNTIME_ORCHESTRATOR_URL or "").rstrip("/")
