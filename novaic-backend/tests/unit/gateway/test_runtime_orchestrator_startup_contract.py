"""
Unit tests for Gateway startup contract: strict Runtime Orchestrator health check.

Verifies that:
- healthy orchestrator -> startup check passes
- unhealthy orchestrator -> startup check raises RuntimeError
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from gateway.clients.runtime_orchestrator import check_runtime_orchestrator_health


class TestCheckRuntimeOrchestratorHealth:
    """Tests for check_runtime_orchestrator_health()."""

    @pytest.mark.asyncio
    async def test_healthy_orchestrator_passes(self):
        """When GET /api/health returns 200, the check passes (no exception)."""
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://127.0.0.1:19993",
        ):
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "gateway.clients.runtime_orchestrator.internal_async_client",
                return_value=mock_client,
            ):
                await check_runtime_orchestrator_health()
                mock_client.get.assert_called_once()
                call_url = mock_client.get.call_args[0][0]
                assert call_url == "http://127.0.0.1:19993/api/health"

    @pytest.mark.asyncio
    async def test_non_200_raises(self):
        """When GET /api/health returns non-200, raises RuntimeError."""
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://127.0.0.1:19993",
        ):
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 503
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "gateway.clients.runtime_orchestrator.internal_async_client",
                return_value=mock_client,
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    await check_runtime_orchestrator_health()
                assert "503" in str(exc_info.value)
                assert "health check failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        """When health check times out, raises RuntimeError."""
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://127.0.0.1:19993",
        ):
            with patch(
                "gateway.clients.runtime_orchestrator.internal_async_client",
            ) as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(
                    side_effect=httpx.TimeoutException("timeout")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                with pytest.raises(RuntimeError) as exc_info:
                    await check_runtime_orchestrator_health()
                assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_error_raises(self):
        """When orchestrator is unreachable, raises RuntimeError."""
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "http://127.0.0.1:19993",
        ):
            with patch(
                "gateway.clients.runtime_orchestrator.internal_async_client",
            ) as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(
                    side_effect=httpx.ConnectError("connection refused")
                )
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client

                with pytest.raises(RuntimeError) as exc_info:
                    await check_runtime_orchestrator_health()
                assert "unreachable" in str(exc_info.value) or "19993" in str(
                    exc_info.value
                )

    @pytest.mark.asyncio
    async def test_empty_url_raises(self):
        """When RUNTIME_ORCHESTRATOR_URL is empty, raises RuntimeError."""
        with patch(
            "gateway.clients.runtime_orchestrator.ServiceConfig.RUNTIME_ORCHESTRATOR_URL",
            "",
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await check_runtime_orchestrator_health()
            assert "not configured" in str(exc_info.value)
