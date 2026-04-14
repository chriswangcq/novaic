"""
business/agent_actions.py — Agent entity action handlers.

Migrated from gateway/api/agent_actions.py.
Actions: interrupt, init, get_model, prompts_preview, available_images
"""

import json
import logging
import uuid as _uuid
from typing import Any, Dict

import httpx

from business.auth import check_agent_access
from business.entity_store import get_entity_store
from common.config import ServiceConfig
from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)


def _store_add_message(
    store,
    agent_id: str,
    type: str,
    content: str,
    *,
    metadata: Dict[str, Any] | None = None,
    status: str = "sent",
) -> dict:
    msg_id = _uuid.uuid4().hex[:12]
    now = utc_now_iso()
    row = {
        "id": msg_id,
        "agent_id": agent_id,
        "type": type,
        "content": content,
        "read": 0,
        "status": status,
        "metadata": json.dumps(metadata or {}),
        "timestamp": now,
    }
    result = store.append("messages", "", row, params={"agent_id": agent_id})
    return result or row


def interrupt_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agents.interrupt — Sleep all awake subagents, cancel queue work, add INTERRUPT message."""
    agent_id = data.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    es = get_entity_store()

    all_subagents = es.list("subagents", "", params={"agent_id": agent_id})
    for sa in all_subagents:
        if sa.get("status") == "awake":
            es.update("subagents", "", sa["subagent_id"],
                      {"status": "sleeping", "need_rest": 0},
                      params={"agent_id": agent_id})

    queue_url = ServiceConfig.QUEUE_SERVICE_URL.rstrip("/")
    cancelled_tasks = 0
    cancelled_sagas = 0

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{queue_url}/api/queue/recover/cancel-all",
                params={"agent_id": agent_id},
            )
            if resp.status_code == 200:
                d = resp.json()
                cancelled_tasks = d.get("cancelled_tasks", 0)
                cancelled_sagas = d.get("cancelled_sagas", 0)
    except Exception as e:
        logger.error("[interrupt_action] Queue cancel-all failed: %s", e)

    msg = _store_add_message(
        es, agent_id,
        type="INTERRUPT",
        content="User requested interrupt",
        status="sent",
        metadata={
            "action": "cancel_all",
            "target_agent_id": agent_id,
            "interrupted_runtimes": 0,
            "cancelled_tasks": cancelled_tasks,
            "cancelled_sagas": cancelled_sagas,
        },
    )
    return {
        "status": "ok",
        "message_id": msg["id"],
        "interrupted_runtimes": 0,
        "cancelled_tasks": cancelled_tasks,
        "cancelled_sagas": cancelled_sagas,
    }


def init_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agents.init — Initialize agent (stub: previously broken import in Gateway)."""
    agent_id = data.get("agent_id") or params.get("agent_id")
    # TODO: implement full init logic (create default config, tools, etc.)
    return {"success": True, "agent_id": agent_id}


def get_model_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agents.get_model — Get the model config for an agent via EntityStore."""
    agent_id = data.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    es = get_entity_store()
    agent = es.get("agents", user_id, agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    model_id = agent.get("model_id") or ""

    prefs = None
    try:
        prefs = es.get("user-preferences", user_id, user_id)
    except Exception:
        pass

    available = es.list("available-models", user_id)
    api_key_models = es.list("api-key-models", user_id)

    return {
        "agent_id": agent_id,
        "model_id": model_id,
        "default_model": (prefs or {}).get("default_model", "gpt-4o"),
        "available_models": available,
        "api_key_models": api_key_models,
    }


def prompts_preview_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agents.prompts_preview — Build and return the system prompt preview."""
    check_agent_access(data.get("agent_id") or params.get("agent_id", ""), user_id)

    agent_id = data.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    try:
        from task_queue.client import GatewayInternalClient
        from task_queue.utils.system_prompt import build_system_prompt, build_wake_message
    except (ImportError, ModuleNotFoundError):
        return {
            "agent_id": agent_id,
            "system_prompt": "[Not available — task_queue module is in novaic-agent-runtime]",
            "system_prompt_length": 0,
            "wake_message": "[Not available — task_queue module is in novaic-agent-runtime]",
            "wake_message_length": 0,
        }

    client = GatewayInternalClient(ServiceConfig.GATEWAY_URL)
    try:
        try:
            system_prompt = build_system_prompt(agent_id, client)
        except Exception as e:
            system_prompt = f"[Error building system prompt: {e}]"
        try:
            wake_message = build_wake_message(agent_id, client)
        except Exception as e:
            wake_message = f"[Error building wake message: {e}]"
    finally:
        client.close()

    return {
        "agent_id": agent_id,
        "system_prompt": system_prompt,
        "system_prompt_length": len(system_prompt),
        "wake_message": wake_message,
        "wake_message_length": len(wake_message),
    }


def available_images_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agents.available_images — List available VM base images (stub: requires filesystem access)."""
    # TODO: Implement filesystem scan or proxy to Gateway if image data resides there
    return {"images": []}
