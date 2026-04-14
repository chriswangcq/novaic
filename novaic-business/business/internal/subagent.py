"""
Internal API module: subagent

Manages SubAgent lifecycle, status, context, HRL, and tool ports.
Migrated from SubAgentRepository to EntityStore + subagent_utils.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from business.entity_store import get_entity_store
from common.enums import SubagentStatus
from .helpers import _subagent_to_dict
from . import subagent_utils

router = APIRouter(tags=["internal"])


def _get_agent_user_id(agent_id: str) -> str:
    """Return the owner user_id for an agent. Raises if agent not found."""
    store = get_entity_store()
    agent = store.get("agents", "", agent_id)
    if not agent:
        raise ValueError(f"Agent '{agent_id}' not found — cannot determine owner user_id")
    return agent.get("user_id", "")


# ==================== SubAgent Operations (v14) ====================

# ==================== SubAgent List (v41 - SubAgent-centric, no runtime_id) ====================

@router.get("/subagents/list")
async def list_subagents(agent_id: str = Query(..., description="Agent ID")):
    """
    List all SubAgents for an agent. SubAgent-centric: no runtime_id.
    Used by subagent_list tool.
    """
    store = get_entity_store()
    db = None
    subagents = store.list("subagents", "", params={"agent_id": agent_id})
    if not subagents:
        # Ensure main exists (each agent has at least main subagent)
        subagent_utils.get_or_create_main_subagent(store, db, agent_id)
        subagents = store.list("subagents", "", params={"agent_id": agent_id})

    return {
        "subagents": [
            {
                "subagent_id": sa["subagent_id"],
                "agent_id": sa["agent_id"],
                "type": sa["type"],
                "status": sa["status"],
                "created_at": sa.get("created_at"),
            }
            for sa in subagents
        ]
    }


@router.get("/subagents/due-wake")
async def get_subagents_due_for_wake():
    """Get sleeping SubAgents whose wake_at timer has expired.
    
    Used by SchedulerWorker to find agents that need to be woken up.
    """
    db = None
    due = subagent_utils.get_due_for_wake(db)

    return {
        "subagents": [
            {
                "agent_id": sa["agent_id"],
                "subagent_id": sa["subagent_id"],
                "wake_at": sa.get("wake_at"),
                "wake_triggers": sa.get("wake_triggers"),
                "handoff_notes": sa.get("handoff_notes"),
            }
            for sa in due
        ]
    }


@router.get("/subagents/{agent_id}/main")
async def get_main_subagent(agent_id: str):
    """Get the main SubAgent for an agent (creates if not exists)."""
    store = get_entity_store()
    db = None
    subagent = subagent_utils.get_or_create_main_subagent(store, db, agent_id)
    return _subagent_to_dict(subagent)


@router.get("/subagents/by-id/{subagent_id}")
async def get_subagent_by_id(subagent_id: str):
    """
    Get SubAgent by subagent_id only (globally unique). Returns agent_id for resolution.
    Used by RO and other callers that need to resolve agent_id from subagent_id.
    """
    store = get_entity_store()
    # user_id="" bypasses scope for internal system lookup
    subagent = store.get("subagents", "", subagent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail=f"SubAgent not found: {subagent_id}")
    return {"agent_id": subagent["agent_id"], "subagent_id": subagent["subagent_id"]}


@router.get("/subagents/{agent_id}/{subagent_id}/history")
async def get_subagent_history(
    agent_id: str,
    subagent_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get SubAgent context history. Used by subagent_history tool.
    Data comes from subagent_context (RO pushes via append).
    """
    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")

    db = None
    messages = subagent_utils.context_get_history(db, agent_id, subagent_id, limit=limit, offset=offset)
    return {"messages": messages}


# ==================== Tool Context (v42 - Tools Server, subagent dimension) ====================

@router.get("/subagents/{agent_id}/{subagent_id}/tool-context")
async def get_subagent_tool_context(agent_id: str, subagent_id: str):
    """
    Get tool context for a SubAgent (agent_id, subagent_id, tool_ports).
    Used by Tools Server for lazy hydrate and session_state.
    """
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    return {
        "agent_id": agent_id,
        "subagent_id": subagent_id,
        "tool_ports": subagent.get("tool_ports") or {},
    }


@router.patch("/subagents/{agent_id}/{subagent_id}/tool-ports")
async def set_subagent_tool_ports(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """
    Set tool_ports for a SubAgent. Used by Tools Server for persistence.
    Body: {"ports": {...}}
    """
    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")
    ports = data.get("ports", {})
    store.update("subagents", "", subagent_id, {"tool_ports": ports}, params={"agent_id": agent_id})
    return {"success": True}


@router.get("/subagents/with-tools")
async def list_subagents_with_tools():
    """
    List SubAgents that have tool_ports set. Used by Tools Server for restore on startup.
    Returns: {"subagents": [{"agent_id", "subagent_id", "tool_ports"}, ...]}
    """
    db = None
    subagents = subagent_utils.list_with_tool_ports(db)
    return {"subagents": subagents}


@router.post("/subagents/{agent_id}/{subagent_id}/send")
async def subagent_send(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """
    Send message to SubAgent via Entangled store.
    Used by subagent_send tool.
    """
    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")

    message_content = data.get("message", "")
    sender_subagent_id = data.get("sender_subagent_id")

    import json as _json, uuid as _uuid
    from common.utils.time import utc_now_iso
    msg_id = _uuid.uuid4().hex[:12]
    now = utc_now_iso()
    msg = store.append("messages", "", {
        "id": msg_id,
        "agent_id": agent_id,
        "type": "SUBAGENT_SEND",
        "content": message_content,
        "read": 0,
        "status": "sent",
        "metadata": _json.dumps({
            "target_subagent_id": subagent_id,
            "sender_subagent_id": sender_subagent_id,
        }),
        "timestamp": now,
    }, params={"agent_id": agent_id}) or {"id": msg_id}
    
    _dispatch_trigger(
        agent_id, 
        user_id=_get_agent_user_id(agent_id), 
        trigger_type="subagent_send", 
        subagent_id=subagent_id
    )

    return {"success": True, "message_id": msg["id"]}

@router.post("/subagents/{agent_id}/{subagent_id}/context/append")
async def append_subagent_context(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """
    RO pushes context increments. Used during execution (e.g. per round).
    """
    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="messages must be a list")

    round_id = data.get("round_id")
    db = None
    count = subagent_utils.context_append(db, agent_id, subagent_id, messages, round_id=round_id)
    return {"appended": count}


@router.get("/subagents/{agent_id}/{subagent_id}")
async def get_subagent(agent_id: str, subagent_id: str):
    """Get a SubAgent by ID."""
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    return _subagent_to_dict(subagent)


# DELETED: wake_subagent() - 用 get_or_create_runtime 替代



# DELETED (v2): set_subagent_sleeping, set_subagent_awake, set_subagent_summarizing,
# set_subagent_completed, set_subagent_failed — all Worker-side status transitions
# are now handled via EntityStore entity_update through Task Queue handlers
# (subagent_handlers.py). See gateway_v2_checklist.md Step 4.


@router.patch("/subagents/{agent_id}/{subagent_id}")
async def update_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Update SubAgent fields. Supports historical_summary, wake_triggers, handoff_notes, wake_at."""
    from datetime import timedelta
    from common.utils.time import utc_now

    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")

    if "historical_summary" in data:
        store.update("subagents", "", subagent_id,
            {"historical_summary": data["historical_summary"]},
            params={"agent_id": agent_id})

    # RO reporting: status, progress (v41)
    if "status" in data:
        status_val = data["status"]
        status_updates = {"status": status_val}
        if status_val == "sleeping":
            status_updates["need_rest"] = 0
        if status_val == "running" and "progress" in data:
            status_updates["progress"] = data["progress"]
        if status_val == "completed":
            status_updates["result"] = data.get("result")
            status_updates["progress"] = None
        if status_val == "failed":
            status_updates["error"] = data.get("error")
            status_updates["progress"] = None
        if status_val == "cancelled":
            status_updates["progress"] = None
        store.update("subagents", "", subagent_id, status_updates, params={"agent_id": agent_id})
    elif "progress" in data:
        # Only update progress if status is running (check first)
        subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
        if subagent and subagent.get("status") == SubagentStatus.RUNNING.value:
            store.update("subagents", "", subagent_id,
                {"progress": data["progress"]},
                params={"agent_id": agent_id})

    # wake_info: wake_triggers, handoff_notes, wake_at (or rest_duration_minutes)
    if "wake_triggers" in data or "handoff_notes" in data or "wake_at" in data or "rest_duration_minutes" in data:
        wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
        handoff_notes = data.get("handoff_notes")
        wake_at = data.get("wake_at")
        if wake_at is None and "rest_duration_minutes" in data:
            rest_duration = max(1, min(1440, int(data.get("rest_duration_minutes", 30))))
            wake_at = (utc_now() + timedelta(minutes=rest_duration)).isoformat()
        updates = {
            "wake_triggers": wake_triggers,
            "wake_at": wake_at,
            "handoff_notes": handoff_notes,
        }
        store.update("subagents", "", subagent_id, updates, params={"agent_id": agent_id})

    return {"status": "ok"}



# DELETED (v2): subagent_rest, check_and_clear_need_rest_api — Worker now
# writes need_rest/wake_at directly via entity_update (tool_handlers.py).


@router.post("/subagents/{agent_id}/spawn")
async def spawn_subagent(agent_id: str, data: Dict[str, Any]):
    """
    Spawn a new SubAgent and its Runtime (async mode).
    """
    from datetime import timedelta
    import uuid

    store = get_entity_store()
    db = None

    # Get parent subagent_id (defaults to main)
    parent_subagent_id = data.get("parent_subagent_id")
    if not parent_subagent_id:
        main_subagent = subagent_utils.get_or_create_main_subagent(store, db, agent_id)
        parent_subagent_id = main_subagent["subagent_id"]

    # Parse parameters
    task_description = data.get("task", "")
    timeout_minutes = data.get("timeout_minutes", 30)

    # Calculate timeout
    now = datetime.utcnow()
    timeout_at = (now + timedelta(minutes=timeout_minutes)).isoformat()

    # Create sub SubAgent via EntityStore
    subagent_utils.ensure_agent_stub(db, agent_id)
    sub_id = f"sub-{uuid.uuid4().hex[:12]}"
    subagent = store.create("subagents", "", {
        "subagent_id": sub_id,
        "agent_id": agent_id,
        "type": "sub",
        "parent_subagent_id": parent_subagent_id,
        "status": "sleeping",
        "task": task_description,
        "timeout_at": timeout_at,
    })

    initial_context = []

    # Add task as user message
    initial_context.append({
        "role": "user",
        "content": f"[SubAgent Task]\n{task_description}"
    })

    trigger_id = f"spawn-{sub_id}-{uuid.uuid4().hex[:8]}"
    import json as _json
    from common.utils.time import utc_now_iso
    msg_id = uuid.uuid4().hex[:12]
    now = utc_now_iso()
    msg = store.append("messages", "", {
        "id": msg_id,
        "agent_id": agent_id,
        "type": "SPAWN_SUBAGENT",
        "content": task_description,
        "read": 0,
        "status": "sent",
        "metadata": _json.dumps({
            "subagent_id": sub_id,
            "trigger_id": trigger_id,
            "initial_context": initial_context,
            "parent_subagent_id": parent_subagent_id,
        }),
        "timestamp": now,
    }, params={"agent_id": agent_id}) or {"id": msg_id}

    logger.info("[Gateway] Created SPAWN_SUBAGENT message %s for subagent %s", msg["id"], sub_id)
    
    _dispatch_trigger(
        agent_id,
        user_id=_get_agent_user_id(agent_id),
        trigger_type="spawn_subagent",
        subagent_id=sub_id,
        metadata={"initial_context": initial_context}
    )

    return {
        "subagent_id": sub_id,
        "message_id": msg["id"],
    }

def _dispatch_trigger(agent_id: str, user_id: str, trigger_type: str, subagent_id: str = None, metadata: dict = None):
    """Call Queue Service dispatch (fire-and-forget)."""
    import httpx
    from common.config import ServiceConfig

    queue_url = ServiceConfig.QUEUE_SERVICE_URL.rstrip("/")
    if not subagent_id:
        subagent_id = f"main-{agent_id[:8]}"

    try:
        resp = httpx.post(
            f"{queue_url}/api/queue/dispatch",
            json={
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "user_id": user_id,
                "trigger_type": trigger_type,
                "metadata": metadata or {},
            },
            timeout=5.0,
        )
        if resp.status_code != 200:
            logger.warning(
                "[subagent_dispatch] dispatch failed: agent=%s status=%d",
                agent_id, resp.status_code
            )
    except Exception as e:
        logger.error("[subagent_dispatch] dispatch error: agent=%s err=%s", agent_id, e)



@router.get("/subagents/{agent_id}/{subagent_id}/status")
async def get_subagent_status(agent_id: str, subagent_id: str):
    """Get SubAgent status for async spawn polling."""
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")

    # Check timeout
    if subagent["status"] == SubagentStatus.RUNNING.value and subagent.get("timeout_at"):
        try:
            timeout_at = datetime.fromisoformat(subagent["timeout_at"])
            if datetime.utcnow() > timeout_at:
                store.update("subagents", "", subagent_id,
                    {"status": SubagentStatus.FAILED.value, "error": "SubAgent timed out", "progress": None},
                    params={"agent_id": agent_id})
                subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
        except (ValueError, TypeError) as e:
            logger.warning("[SubAgent] Invalid timeout_at format for subagent %s: %s", subagent_id, e)

    completed = subagent["status"] in (
        SubagentStatus.COMPLETED.value,
        SubagentStatus.FAILED.value,
        SubagentStatus.CANCELLED.value,
        SubagentStatus.SLEEPING.value
    )

    return {
        "subagent_id": subagent_id,
        "status": subagent["status"],
        "completed": completed,
        "progress": subagent.get("progress"),
        "result": subagent.get("result"),
        "error": subagent.get("error"),
    }


@router.post("/subagents/{agent_id}/{subagent_id}/cancel")
async def cancel_subagent(agent_id: str, subagent_id: str):
    """Cancel a running SubAgent."""
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")

    if subagent["status"] != SubagentStatus.RUNNING.value:
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent['status']})"}

    store.update("subagents", "", subagent_id,
        {"status": SubagentStatus.CANCELLED.value, "progress": None},
        params={"agent_id": agent_id})

    return {"success": True}


@router.delete("/subagents/{agent_id}/{subagent_id}")
async def delete_subagent(agent_id: str, subagent_id: str):
    """Delete a SubAgent."""
    store = get_entity_store()
    store.delete("subagents", "", subagent_id, params={"agent_id": agent_id})
    return {"status": "ok"}



# ==================== HRL and Summary Lock Operations (v24) ====================

@router.get("/subagents/{agent_id}/{subagent_id}/hrl")
async def get_hrl(agent_id: str, subagent_id: str):
    """Get Hot Runtime List for a SubAgent."""
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    hrl = subagent.get("hrl", []) if subagent else []

    return {
        "hrl": hrl,
        "length": len(hrl),
    }


@router.post("/subagents/{agent_id}/{subagent_id}/hrl/add")
async def add_to_hrl_api(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Add a runtime to HRL."""
    runtime_id = data.get("runtime_id")
    if not runtime_id:
        raise HTTPException(status_code=400, detail="runtime_id is required")

    db = None
    success = subagent_utils.add_to_hrl(db, subagent_id, agent_id, runtime_id)

    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    hrl = subagent.get("hrl", []) if subagent else []

    return {
        "success": success,
        "hrl": hrl,
        "length": len(hrl),
    }


@router.get("/subagents/{agent_id}/{subagent_id}/summary-lock")
async def get_summary_lock(agent_id: str, subagent_id: str):
    """Get summary_lock status for a SubAgent."""
    store = get_entity_store()
    subagent = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    lock = subagent.get("summary_lock", 0) if subagent else 0
    return {"summary_lock": lock}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/acquire")
async def acquire_summary_lock_api(agent_id: str, subagent_id: str):
    """Try to acquire summary_lock using CAS."""
    db = None
    success = subagent_utils.acquire_summary_lock(db, subagent_id, agent_id)
    return {"success": success}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/release")
async def release_summary_lock_api(agent_id: str, subagent_id: str):
    """Release summary_lock."""
    db = None
    subagent_utils.release_summary_lock(db, subagent_id, agent_id)
    return {"success": True}


@router.post("/subagents/{agent_id}/{subagent_id}/merge-history")
async def merge_history(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Atomically update historical_summary and remove runtimes from HRL."""
    db = None
    new_history = data.get("new_history", "")
    remove_runtime_ids = data.get("remove_runtime_ids", [])

    success = subagent_utils.atomic_update_history_and_hrl(
        db,
        subagent_id=subagent_id,
        agent_id=agent_id,
        new_history=new_history,
        remove_runtime_ids=remove_runtime_ids
    )
    return {"success": success}


# ==================== Drive Prompt Data (Phase 3) ====================

@router.get("/agents/{agent_id}/drive")
async def get_agent_drive(agent_id: str):
    """Get agent drive record for Drive Prompt builder."""
    from business.prompt_defaults import fill_prompt_defaults
    store = get_entity_store()
    drive = store.get("agent-tools", "", agent_id, params={"agent_id": agent_id})
    if not drive:
        drive = {
            "agent_id": agent_id,
            "personality": {},
            "communication_style": "friendly",
            "user_profile": {},
            "user_active_hours": None,
            "proactiveness": 0.5,
            "min_rest_minutes": 15,
            "max_rest_minutes": 120,
            "relationship_level": 0,
            "interaction_count": 0,
            "no_response_streak": 0,
            "last_proactive_at": None,
            "disabled_tools": [],
            "custom_instructions": "",
            "soul_md": "",
            "heartbeat_md": "",
            "memory_md": "",
            "user_md": "",
            "behavior_guide_md": "",
            "capability_list_md": "",
            "sub_subagent_guide_md": "",
            "active_hours_start": "09:00",
            "active_hours_end": "22:00",
            "active_hours_timezone": "Asia/Shanghai",
            "created_at": None,
            "updated_at": None,
        }
    return fill_prompt_defaults(drive)


@router.get("/agents/{agent_id}/notebook-summary")
async def get_agent_notebook_summary(agent_id: str):
    """Get notebook summary for Drive Prompt builder."""
    from common.utils.time import utc_now_iso
    
    store = get_entity_store()
    entries = store.list("agent-notebook", "", params={"agent_id": agent_id})
    now = utc_now_iso()
    
    summary = []
    for e in entries:
        if e.get("status") == "archived":
            continue
        exp = e.get("expires_at")
        if exp and exp <= now:
            continue
            
        summary.append({
            "id": e.get("id"),
            "type": e.get("entry_type"),
            "title": e.get("title"),
            "status": e.get("status"),
            "relevance": e.get("relevance_score"),
            "created_at": e.get("created_at"),
        })
        
    summary.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    summary = summary[:10]
    
    return {
        "success": True,
        "entries": summary,
        "count": len(summary),
    }


# ==================== Agent Info & Drive Lifecycle (Phase 4) ====================

@router.post("/agents/{agent_id}/drive/increment-interaction")
async def increment_drive_interaction(agent_id: str):
    """Increment interaction count and reset no-response streak in agent_drive."""
    store = get_entity_store()
    current = store.get("agent-tools", "", agent_id, params={"agent_id": agent_id})
    if not current:
        current = {"interaction_count": 0, "no_response_streak": 0}
        
    store.upsert(
        "agent-tools", "", agent_id,
        data={
            "interaction_count": current.get("interaction_count", 0) + 1,
            "no_response_streak": 0
        },
        params={"agent_id": agent_id}
    )
    
    return {"success": True}


@router.get("/agents/{agent_id}/info")
async def get_agent_info(agent_id: str):
    """Get basic agent info for system prompt builder."""
    store = get_entity_store()
    agent = store.get("agents", "", agent_id)

    if not agent:
        return {"name": "NovAIC Agent", "os": "unknown", "agent_id": agent_id}

    return {
        "name": agent.get("name", "NovAIC Agent"),
        "os": agent.get("os", "unknown"),
        "agent_id": agent_id,
    }
