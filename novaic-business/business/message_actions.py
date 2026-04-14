"""
business/message_actions.py — Message entity action handlers.

Migrated from gateway/api/message_actions.py.
Actions: send, mark_all_read, clear
"""

import json as json_module
import logging
import uuid as _uuid
from typing import Any, Dict

import httpx

from business.auth import check_agent_access
from common.config import ServiceConfig
from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)


def _store_add_message(
    store,
    user_id: str,
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
        "metadata": json_module.dumps(metadata or {}),
        "timestamp": now,
    }
    result = store.append("messages", user_id, row, params={"agent_id": agent_id})
    return result or row


def _dispatch_trigger(agent_id: str, user_id: str):
    """Fire-and-forget dispatch to Queue Service."""
    queue_url = ServiceConfig.QUEUE_SERVICE_URL.rstrip("/")
    subagent_id = f"main-{agent_id[:8]}"

    try:
        resp = httpx.post(
            f"{queue_url}/api/queue/dispatch",
            json={
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "user_id": user_id,
                "trigger_type": "user_message",
            },
            timeout=5.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            logger.info(
                "[send_action] dispatch: agent=%s action=%s saga=%s",
                agent_id, data.get("action"), data.get("saga_id"),
            )
        else:
            logger.warning(
                "[send_action] dispatch failed: agent=%s status=%d body=%s",
                agent_id, resp.status_code, resp.text[:200],
            )
    except Exception as e:
        logger.error("[send_action] dispatch error: agent=%s err=%s", agent_id, e)


def send_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """messages.send — Send a user chat message, then dispatch to Queue Service."""
    agent_id = payload.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    check_agent_access(agent_id, user_id)

    text = payload.get("message", "").strip()
    attachments = payload.get("attachments") or []
    if isinstance(attachments, dict):
        attachments = [attachments]
    model = payload.get("model")
    api_key_id = payload.get("api_key_id")

    if not text and not attachments:
        raise ValueError("Message content or attachments required")

    att_list = []
    for a in attachments:
        if isinstance(a, dict) and a.get("url"):
            att = {
                "url": a["url"],
                "filename": a.get("filename", ""),
                "mime_type": a.get("mime_type", "application/octet-stream"),
            }
            att["modality"] = (
                "image" if (att["mime_type"] or "").startswith("image/") else "resource"
            )
            att_list.append(att)

    content_obj = {"text": text, "attachments": att_list}
    content_str = json_module.dumps(content_obj, ensure_ascii=False)

    msg = _store_add_message(
        store, user_id, agent_id,
        type="USER_MESSAGE",
        content=content_str,
        metadata={"model": model, "api_key_id": api_key_id},
        status="sent",
    )

    _dispatch_trigger(agent_id, user_id)

    return {
        "message_id": msg["id"],
        "status": "sent",
        "timestamp": msg["timestamp"],
    }


def mark_all_read_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """messages.mark_all_read — Mark all unread agent messages as read."""
    agent_id = payload.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    check_agent_access(agent_id, user_id)

    rows = store.list(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0, "type": "AGENT_REPLY"},
        limit=500,
    ) + store.list(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0, "type": "AGENT_ASK"},
        limit=500,
    )
    if not rows:
        return {"updated": 0}

    ids = [r["id"] for r in rows]

    count = store.batch_update(
        entity="messages",
        user_id=user_id,
        entity_ids=ids,
        data={"read": 1},
        params={"agent_id": agent_id},
    )

    logger.info("[mark_all_read] agent=%s marked %d agent messages as read", agent_id, count)
    return {"updated": count}


def clear_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """messages.clear — Delete all messages for an agent."""
    agent_id = payload.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    check_agent_access(agent_id, user_id)

    count = store.delete_where(
        "messages", "",
        params={"agent_id": agent_id},
    )

    logger.info("[clear] agent=%s deleted %d messages", agent_id, count)
    return {"deleted": count}
