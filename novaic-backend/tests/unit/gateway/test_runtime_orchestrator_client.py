"""
Unit tests for RuntimeOrchestratorClient.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from gateway.clients.runtime_orchestrator import (
    RuntimeOrchestratorClient,
    close_runtime_orchestrator_client,
    get_runtime_orchestrator_client,
)


class TestRuntimeOrchestratorClient:
    def test_init_requires_url(self):
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            None,
        ):
            with pytest.raises(ValueError):
                RuntimeOrchestratorClient()

    def test_is_enabled(self):
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://orchestrator:21000",
        ):
            assert RuntimeOrchestratorClient.is_enabled() is True

        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            None,
        ):
            assert RuntimeOrchestratorClient.is_enabled() is False

    @pytest.mark.asyncio
    async def test_forward_success_json(self):
        client = RuntimeOrchestratorClient(base_url="http://orchestrator:21000")
        original_http_client = client.client
        await original_http_client.aclose()
        mock_http_client = AsyncMock()
        client.client = mock_http_client

        mock_response = Mock()
        mock_response.text = '{"success": true}'
        mock_response.json.return_value = {"success": True, "runtimes": []}
        mock_response.raise_for_status.return_value = None
        mock_http_client.request.return_value = mock_response

        data = await client.forward("get", "/internal/runtimes/list")

        assert data["success"] is True
        assert isinstance(data["runtimes"], list)
        mock_http_client.request.assert_called_once_with(
            method="GET",
            url="/internal/runtimes/list",
            params=None,
            json=None,
        )

    @pytest.mark.asyncio
    async def test_forward_empty_body_returns_success(self):
        client = RuntimeOrchestratorClient(base_url="http://orchestrator:21000")
        original_http_client = client.client
        await original_http_client.aclose()
        mock_http_client = AsyncMock()
        client.client = mock_http_client

        mock_response = Mock()
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_http_client.request.return_value = mock_response

        data = await client.forward("post", "/internal/messages/mark-read", json={})

        assert data == {"success": True}

    @pytest.mark.asyncio
    async def test_forward_raises_http_status_error(self):
        client = RuntimeOrchestratorClient(base_url="http://orchestrator:21000")
        original_http_client = client.client
        await original_http_client.aclose()
        mock_http_client = AsyncMock()
        client.client = mock_http_client

        req = httpx.Request("GET", "http://orchestrator/internal/runtimes/list")
        resp = httpx.Response(status_code=503, request=req)
        error = httpx.HTTPStatusError("service unavailable", request=req, response=resp)

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = error
        mock_http_client.request.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await client.forward("get", "/internal/runtimes/list")


class TestGlobalRuntimeOrchestratorClient:
    @pytest.fixture(autouse=True)
    async def reset_singleton(self):
        await close_runtime_orchestrator_client()
        yield
        await close_runtime_orchestrator_client()

    def test_get_runtime_orchestrator_client_singleton(self):
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://orchestrator:21000",
        ):
            c1 = get_runtime_orchestrator_client()
            c2 = get_runtime_orchestrator_client()
            assert c1 is c2
