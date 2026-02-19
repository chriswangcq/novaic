"""
Unit tests: Gateway resolve_agent_id_from_subagent via RO API.

Ensures Gateway does NOT query local SubAgent table; resolution is via RO internal API.
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx


class TestResolveAgentIdFromSubagent:
    """resolve_agent_id_from_subagent must call RO API, not local DB."""

    def test_resolve_calls_ro_api_and_returns_agent_id(self):
        """When RO returns 200 with agent_id, helper returns agent_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "subagent_id": "main-agent123",
            "agent_id": "agent-123",
            "type": "main",
            "status": "sleeping",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with patch("gateway.api.internal.helpers.ServiceConfig") as mock_config:
            mock_config.RUNTIME_ORCHESTRATOR_URL = "http://ro:8000"
            mock_config.HTTP_TIMEOUT = 30.0
            with patch(
                "common.http.clients.internal_client"
            ) as mock_client_factory:
                mock_client_factory.return_value = mock_client

                from gateway.api.internal.helpers import resolve_agent_id_from_subagent

                result = resolve_agent_id_from_subagent("main-agent123")
                assert result == "agent-123"
                mock_client.get.assert_called_once()
                call_args = mock_client.get.call_args
                # client.get(path) with base_url on client
                assert "/internal/subagents/by-id/main-agent123" in str(call_args)

    def test_resolve_does_not_use_subagent_repository(self):
        """resolve_agent_id_from_subagent must NOT use SubAgentRepository (RO is source of truth)."""
        # Patch SubAgentRepository.get_by_subagent_id to fail if ever called
        with patch(
            "gateway.db.repositories.subagent.SubAgentRepository.get_by_subagent_id"
        ) as mock_get:
            mock_get.side_effect = AssertionError(
                "Gateway must NOT use SubAgentRepository for resolution"
            )

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "agent_id": "agent-1",
                "subagent_id": "main-a",
                "type": "main",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response

            with patch("gateway.api.internal.helpers.ServiceConfig") as mock_config:
                mock_config.RUNTIME_ORCHESTRATOR_URL = "http://ro:8000"
                mock_config.HTTP_TIMEOUT = 30.0
                with patch(
                    "common.http.clients.internal_client"
                ) as mock_client_factory:
                    mock_client_factory.return_value = mock_client

                    from gateway.api.internal.helpers import (
                        resolve_agent_id_from_subagent,
                    )

                    result = resolve_agent_id_from_subagent("main-a")
                    assert result == "agent-1"
                    # SubAgentRepository.get_by_subagent_id must never have been called
                    mock_get.assert_not_called()

    def test_resolve_raises_404_when_ro_returns_404(self):
        """When RO returns 404, helper raises HTTPException 404."""
        from fastapi import HTTPException

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404",
            request=MagicMock(),
            response=MagicMock(
                status_code=404,
                json=lambda: {"detail": "SubAgent not found: xyz"},
                text="SubAgent not found",
            ),
        )

        with patch("gateway.api.internal.helpers.ServiceConfig") as mock_config:
            mock_config.RUNTIME_ORCHESTRATOR_URL = "http://ro:8000"
            with patch("common.http.clients.internal_client") as mock_factory:
                mock_factory.return_value = mock_client

                from gateway.api.internal.helpers import resolve_agent_id_from_subagent

                with pytest.raises(HTTPException) as exc_info:
                    resolve_agent_id_from_subagent("xyz")
                assert exc_info.value.status_code == 404

    def test_resolve_raises_500_when_ro_not_configured(self):
        """When RUNTIME_ORCHESTRATOR_URL is not set, helper raises 500."""
        from fastapi import HTTPException

        with patch(
            "gateway.clients.runtime_orchestrator.RuntimeOrchestratorClient.is_enabled",
            return_value=False,
        ):
            from gateway.api.internal.helpers import resolve_agent_id_from_subagent

            with pytest.raises(HTTPException) as exc_info:
                resolve_agent_id_from_subagent("main-x")
            assert exc_info.value.status_code == 500
