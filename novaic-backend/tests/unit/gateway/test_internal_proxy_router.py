"""
Unit tests for Gateway /internal proxy router.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from gateway.api.internal_proxy import router as internal_proxy_router


@pytest.fixture
def internal_proxy_app():
    app = FastAPI()
    app.include_router(internal_proxy_router)
    return app


@pytest.mark.asyncio
class TestInternalProxyRouter:
    async def test_proxy_forwards_get_with_query(self, internal_proxy_app):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"ok":true}'
        mock_response.headers = {"content-type": "application/json"}

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://127.0.0.1:19993",
            ),
            patch("gateway.api.internal_proxy.internal_async_client", return_value=mock_http_client),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=internal_proxy_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/list?agent_id=a1")

        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        mock_http_client.request.assert_called_once_with(
            method="GET",
            url="http://127.0.0.1:19993/internal/runtimes/list",
            params={"agent_id": "a1"},
            content=None,
            headers=None,
        )

    async def test_proxy_forwards_patch_with_json_body(self, internal_proxy_app):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"status":"ok"}'
        mock_response.headers = {"content-type": "application/json"}

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://127.0.0.1:19993",
            ),
            patch("gateway.api.internal_proxy.internal_async_client", return_value=mock_http_client),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=internal_proxy_app),
                base_url="http://test",
            ) as client:
                resp = await client.patch(
                    "/internal/messages/mark-read",
                    json={"message_ids": ["m1"]},
                )

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        call_kwargs = mock_http_client.request.call_args.kwargs
        assert call_kwargs["method"] == "PATCH"
        assert call_kwargs["url"] == "http://127.0.0.1:19993/internal/messages/mark-read"
        assert call_kwargs["params"] == {}
        assert call_kwargs["headers"]["content-type"].startswith("application/json")
        assert call_kwargs["content"] is not None

    async def test_proxy_returns_503_on_connect_error(self, internal_proxy_app):
        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(
                "gateway.api.internal_proxy.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
                "http://127.0.0.1:19993",
            ),
            patch("gateway.api.internal_proxy.internal_async_client", return_value=mock_http_client),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=internal_proxy_app),
                base_url="http://test",
            ) as client:
                resp = await client.get("/internal/runtimes/list")

        assert resp.status_code == 503
        assert "Runtime Orchestrator unavailable" in resp.json().get("detail", "")
