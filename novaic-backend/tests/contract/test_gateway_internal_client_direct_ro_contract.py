"""
Contract tests for GatewayInternalClient routing policy.

Production contract:
- /internal/* traffic defaults to Runtime Orchestrator direct path
- public /api/* traffic still goes to Gateway
"""

from unittest.mock import patch

import httpx
import pytest

from common.config import ServiceConfig
from task_queue.client import GatewayInternalClient


def _mock_transport(calls):
    def _handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path.startswith("/internal/"):
            return httpx.Response(
                status_code=200,
                json={"runtime": {"runtime_id": "rt-1", "agent_id": "agent-1"}},
                request=request,
            )
        return httpx.Response(status_code=200, json={"ok": True}, request=request)

    return httpx.MockTransport(_handler)


class TestGatewayInternalClientDirectRoutingContract:
    def test_internal_uses_runtime_orchestrator_and_api_uses_gateway(self):
        calls = []

        with (
            patch.object(
                ServiceConfig,
                "RUNTIME_ORCHESTRATOR_URL",
                "http://orchestrator-test:19993",
            ),
            patch("task_queue.client.os.environ", {}, create=True),
            patch(
                "task_queue.client.internal_client",
                return_value=httpx.Client(transport=_mock_transport(calls)),
            ),
        ):
            client = GatewayInternalClient("http://gateway-test:19999")
            runtime = client.get_runtime("rt-1")
            _ = client.broadcast_log(agent_id="agent-1", log_type="TEST", data={"x": 1})
            client.close()

        assert runtime["runtime_id"] == "rt-1"
        assert calls[0].startswith("http://orchestrator-test:19993/internal/runtimes/rt-1")
        assert calls[1].startswith("http://gateway-test:19999/api/logs/broadcast")

    def test_internal_defaults_to_service_config_runtime_orchestrator_url(self):
        calls = []

        with (
            patch.object(
                ServiceConfig,
                "RUNTIME_ORCHESTRATOR_URL",
                "http://orchestrator-default:19993",
            ),
            patch("task_queue.client.os.environ", {}, create=True),
            patch(
                "task_queue.client.internal_client",
                return_value=httpx.Client(transport=_mock_transport(calls)),
            ),
        ):
            client = GatewayInternalClient("http://gateway-test:19999")
            _ = client.get_runtime("rt-1")
            client.close()

        assert calls[0].startswith("http://orchestrator-default:19993/internal/runtimes/rt-1")
