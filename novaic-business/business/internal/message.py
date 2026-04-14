"""
Internal API module: message

All message operations go through RemoteEntityStore → Entangled HTTP.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import json
import logging
import uuid as _uuid

logger = logging.getLogger(__name__)

from common.utils.time import utc_now_iso
from common.config import ServiceConfig
router = APIRouter(tags=["internal"])


def _get_store():
    from business.entity_store import get_entity_store
    return get_entity_store()


def _store_add_message(
    store,
    agent_id: str,
    type: str,
    content: str,
    *,
    metadata: Dict[str, Any] | None = None,
    status: str = "sent",
) -> dict:
    """Write a message via the entity store (→ Entangled HTTP)."""
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


# ==================== Message Operations ====================

@router.get("/chat/history")
async def get_chat_history(
    agent_id: str = Query(..., description="Agent ID"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get chat history for one agent."""
    store = _get_store()
    rows = store.list_stream(
        "messages", "",
        params={"agent_id": agent_id},
        not_in_filters={"type": ["SYSTEM_WAKE"]},
        order_by="timestamp DESC",
        limit=limit,
    )
    messages = [
        {
            "id": row["id"],
            "type": row["type"],
            "content": row.get("content"),
            "timestamp": row["timestamp"],
            "read": bool(row.get("read", False)),
        }
        for row in reversed(rows)
    ]
    return {"messages": messages}


@router.post("/chat/clear")
async def clear_chat_history(agent_id: str = Query(..., description="Agent ID")):
    """Mark one agent's chat history as read."""
    store = _get_store()
    rows = store.list(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0},
        limit=1000,
    )
    if rows:
        ids = [r["id"] for r in rows]
        store.batch_update("messages", "", ids, {"read": 1}, params={"agent_id": agent_id})
    return {"status": "ok", "message": "History cleared (messages marked as read)"}


@router.post("/agents/{agent_id}/interrupt")
async def interrupt_agent(agent_id: str):
    """Interrupt one agent: enqueue INTERRUPT message, then call direct cancellation."""
    import httpx

    store = _get_store()

    all_subagents = store.list("subagents", "", params={"agent_id": agent_id})
    for sa in all_subagents:
        if sa.get("status") == "awake":
            store.update("subagents", "", sa["subagent_id"],
                {"status": "sleeping", "need_rest": 0},
                params={"agent_id": agent_id})

    queue_url = ServiceConfig.QUEUE_SERVICE_URL.rstrip("/")
    cancelled_tasks = 0
    cancelled_sagas = 0

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{queue_url}/api/queue/recover/cancel-all",
                params={"agent_id": agent_id},
                timeout=10.0
            )
            if resp.status_code == 200:
                data = resp.json()
                cancelled_tasks = data.get("cancelled_tasks", 0)
                cancelled_sagas = data.get("cancelled_sagas", 0)
    except Exception as e:
        logger.error(f"[interrupt_agent] Failed to call cancel-all on Queue Service: {e}")

    msg = _store_add_message(
        store, agent_id,
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
        "note": "Cancellation executed directly via Queue Service",
    }

@router.get("/messages/unread/{agent_id}")
async def get_unread_messages(agent_id: str):
    """Get unread messages for an agent (for Scheduler to include in context)."""
    store = _get_store()
    rows = store.list(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0, "type": "USER_MESSAGE"},
        limit=500,
    )
    return {"messages": rows}


def _parse_message_content(content) -> dict:
    """Parse stored content: JSON {"text","attachments"} or plain string -> dict."""
    if content is None:
        return {"text": "", "attachments": []}
    if isinstance(content, dict):
        return content
    s = str(content).strip()
    if not s:
        return {"text": "", "attachments": []}
    if s.startswith("{") and "attachments" in s:
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            logger.debug("[Message] Content JSON parse fallback: %s", e)
    return {"text": s, "attachments": []}


@router.get("/messages/unread-sent/{agent_id}")
async def get_unread_sent_messages(agent_id: str):
    """Get unread sent messages for an agent (USER_MESSAGE, SYSTEM_WAKE, SUBAGENT_COMPLETED)."""
    store = _get_store()
    rows = store.list(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0},
        limit=500,
        skip_default_not_in=True,
    )

    valid_types = ("USER_MESSAGE", "SYSTEM_WAKE", "SUBAGENT_COMPLETED", "SUBAGENT_SEND")
    user_messages = []
    for m in rows:
        if m.get("type") not in valid_types:
            continue
        content = _parse_message_content(m.get("content"))
        msg_entry = {
            "id": m["id"],
            "content": content,
            "timestamp": m["timestamp"],
            "type": m.get("type"),
        }
        if m.get("metadata"):
            msg_entry["metadata"] = m["metadata"]
        user_messages.append(msg_entry)

    return {"messages": user_messages}


@router.get("/messages/unread-count/{agent_id}")
async def get_unread_count(agent_id: str):
    """Get count of unread messages (for Monitor to detect new messages)."""
    store = _get_store()
    count = store.count(
        "messages", "",
        params={"agent_id": agent_id},
        filters={"read": 0, "type": "USER_MESSAGE"},
    )
    return {"count": count}


@router.get("/messages/unread-grouped")
async def get_unread_messages_grouped(agent_id: Optional[str] = None):
    """Get unread messages grouped by agent_id (v14 for Monitor)."""
    store = _get_store()

    rows = store.list(
        "messages", "",
        filters={"read": 0, "type": "USER_MESSAGE"},
        order_by="timestamp ASC",
    )

    messages_by_agent: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        aid = row.get("agent_id", "")
        if not aid:
            continue
        if aid not in messages_by_agent:
            messages_by_agent[aid] = []
        messages_by_agent[aid].append({
            "id": row["id"],
            "type": row["type"],
            "content": row.get("content"),
            "metadata": row.get("metadata") or {},
            "timestamp": row["timestamp"],
        })

    return {"messages_by_agent": messages_by_agent}


@router.post("/messages")
async def create_message(data: Dict[str, Any]):
    """Create a chat message for internal use."""
    store = _get_store()
    msg = _store_add_message(
        store, data["agent_id"],
        type=data["type"],
        content=data["content"],
        metadata=data.get("metadata"),
        status="sent",
    )
    return msg


# ==================== Agent-scoped Chat APIs ====================

@router.get("/agents/{agent_id}/chat/history")
async def get_agent_chat_history(
    agent_id: str,
    limit: int = Query(20, ge=1, le=1000),
    summary_length: int = Query(50, ge=0, le=500),
):
    """Get chat history for an agent."""
    store = _get_store()
    rows = store.list_stream(
        "messages", "",
        params={"agent_id": agent_id},
        order_by="timestamp DESC",
        limit=limit,
    )

    result = []
    for m in rows:
        content = m.get("content", {})
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                content = {"text": content, "attachments": []}

        role = "user" if m["type"] == "USER_MESSAGE" else "assistant"
        result.append({
            "id": m["id"],
            "role": role,
            "type": m["type"],
            "content": content,
            "timestamp": m["timestamp"],
        })

    return {"messages": list(reversed(result)), "has_more": len(result) == limit}


@router.post("/agents/{agent_id}/chat/event")
async def agent_chat_event(agent_id: str, data: Dict[str, Any]):
    """Send a chat event for an agent."""
    store = _get_store()

    event_type = data.get("type", "AGENT_REPLY")
    event_data = data.get("data", {})

    if event_type == "AGENT_REPLY":
        text = event_data.get("message", "")

        if text.strip() == "HEARTBEAT_OK" or text.strip().startswith("HEARTBEAT_OK"):
            return {"success": True, "silent": True, "message": "Heartbeat acknowledged silently."}

        raw_attachments = event_data.get("attachments") or []
        attachments = []
        for a in raw_attachments:
            if isinstance(a, dict) and a.get("url"):
                att = {
                    "url": a["url"],
                    "filename": a.get("filename") or a["url"].rsplit("/", 1)[-1].split("?")[0] or "file",
                    "mime_type": a.get("mime_type", "application/octet-stream"),
                }
                att["modality"] = "image" if att["mime_type"].startswith("image/") else "resource"
                attachments.append(att)

        content_obj = {"text": text, "attachments": attachments}
        content = json.dumps(content_obj, ensure_ascii=False)
    else:
        content = event_data.get("message", "") or json.dumps(event_data)

    msg = _store_add_message(
        store, agent_id,
        type=event_type,
        content=content,
        status="sent",
    )

    return {"success": True, "message_id": msg["id"], "timestamp": msg["timestamp"]}


@router.get("/agents/{agent_id}/chat/message/{message_id}")
async def get_agent_chat_message(agent_id: str, message_id: str):
    """Get a single chat message."""
    store = _get_store()
    msg = store.get("messages", "", message_id, params={"agent_id": agent_id})

    if not msg:
        raise HTTPException(status_code=404, detail=f"Message not found: {message_id}")

    if msg.get("agent_id") != agent_id:
        raise HTTPException(status_code=403, detail="Message does not belong to this agent")

    return msg
