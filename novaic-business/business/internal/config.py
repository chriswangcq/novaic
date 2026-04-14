"""
Internal API module: config

Reads agent configuration and LLM config from Entangled entity store.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from business.entity_store import get_entity_store

router = APIRouter(tags=["internal"])

# ==================== Config ====================

@router.get("/config/agent/{agent_id}")
def get_agent_config(agent_id: str):
    """Get agent configuration."""
    store = get_entity_store()
    agent = store.get("agents", "", agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": agent.get("id") or agent_id,
        "name": agent.get("name", ""),
        "default_model": agent.get("model_id", ""),
    }


@router.get("/config/ports/by-agent/{agent_id}")
def get_ports_by_agent_id(agent_id: str):
    """Get port configuration for an agent by agent_id.

    Reads device/port info from Entangled entities.
    Falls back to common config constants when entity data is missing.
    """
    from common.config import ServiceConfig

    store = get_entity_store()
    device = store.get("devices", "", agent_id)

    gateway_port = ServiceConfig.GATEWAY_PORT

    if not device or not device.get("ports"):
        raise HTTPException(status_code=404, detail="Agent not found or has no port configuration")

    ports = device["ports"]
    ssh_port = ports.get("ssh") if isinstance(ports, dict) else None

    return {
        "agent_id": agent_id,
        "gateway_port": gateway_port,
        "ports": {
            "ssh": ssh_port,
        }
    }


@router.get("/config/llm/agent/{agent_id}")
def get_agent_llm_config(agent_id: str):
    """Get LLM configuration for a specific agent.

    INTERNAL USE ONLY - includes sensitive data.
    Used by task_queue workers for LLM calls.
    Delegates to LLM Factory for model resolution.
    """
    from business.internal.factory_client import build_llm_config_for_agent_via_factory
    result = build_llm_config_for_agent_via_factory(None, agent_id)
    return result

@router.get("/config/llm/agent/{agent_id}/audio")
def get_agent_audio_llm_config(agent_id: str):
    """Get audio LLM configuration for a specific agent.

    INTERNAL USE ONLY.
    Delegates to LLM Factory for model resolution.
    """
    from business.internal.factory_client import build_llm_config_for_agent_via_factory
    result = build_llm_config_for_agent_via_factory(None, agent_id, use_audio_model=True)
    return result
