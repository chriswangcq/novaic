"""
Unit tests for maybe_forward_to_runtime_orchestrator self-bypass behavior.

Verifies:
1) When NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS=true -> returns None, does not call get_runtime_orchestrator_client
2) When process flag false and URL configured -> calls client.forward with expected args
3) When process flag false and URL missing -> raises HTTPException 500 (strict, no silent fallback)
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from gateway.api.internal.helpers import maybe_forward_to_runtime_orchestrator


class TestMaybeForwardToRuntimeOrchestrator:
    """Tests for maybe_forward_to_runtime_orchestrator()."""

    @pytest.mark.asyncio
    async def test_self_bypass_when_runtime_orchestrator_process_true(self):
        """When NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS=true, returns None and does not call get_runtime_orchestrator_client."""
        mock_get_client = AsyncMock()

        with (
            patch.dict("os.environ", {"NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS": "true"}),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                mock_get_client,
            ),
        ):
            result = await maybe_forward_to_runtime_orchestrator(
                "GET", "/internal/runtimes/list"
            )

        assert result is None
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_forwards_when_url_configured_and_process_flag_false(self):
        """When process flag false and URL configured, calls client.forward with expected args."""
        mock_client = AsyncMock()
        mock_client.forward = AsyncMock(return_value={"success": True, "runtimes": []})

        with (
            patch.dict("os.environ", {"NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS": ""}),
            patch(
                "gateway.clients.runtime_orchestrator.RuntimeOrchestratorClient.is_enabled",
                return_value=True,
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                return_value=mock_client,
            ),
        ):
            result = await maybe_forward_to_runtime_orchestrator(
                "GET", "/internal/runtimes/list", params={"agent_id": "a1"}
            )

        assert result == {"success": True, "runtimes": []}
        mock_client.forward.assert_called_once_with(
            "GET",
            "/internal/runtimes/list",
            params={"agent_id": "a1"},
            json=None,
        )

    @pytest.mark.asyncio
    async def test_raises_500_when_url_missing(self):
        """When process flag false and URL missing, raises HTTPException 500 (strict, no silent fallback)."""
        mock_get_client = AsyncMock()

        with (
            patch.dict("os.environ", {"NOVAIC_RUNTIME_ORCHESTRATOR_PROCESS": ""}),
            patch(
                "gateway.clients.runtime_orchestrator.RuntimeOrchestratorClient.is_enabled",
                return_value=False,
            ),
            patch(
                "gateway.clients.runtime_orchestrator.get_runtime_orchestrator_client",
                mock_get_client,
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await maybe_forward_to_runtime_orchestrator(
                    "GET", "/internal/runtimes/list"
                )

        assert exc_info.value.status_code == 500
        assert "Runtime Orchestrator" in str(exc_info.value.detail)
        mock_get_client.assert_not_called()
