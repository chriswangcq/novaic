"""
Internal API module: subagent (RO-owned).

Runtime Orchestrator owns /internal/subagents* and related /internal/agents/* subagent-facing routes.
No proxy logic; RO is the canonical provider.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException

from common.enums import RuntimeStatus, SubagentStatus
from common.config import ServiceConfig
from runtime_orchestrator.db import get_db
from .helpers import _runtime_to_dict, _subagent_to_dict

router = APIRouter(tags=["internal"])

# ==================== SubAgent Operations (v14) ====================


# ==================== SubAgent Resolution by ID Only (Gateway contract) ====================
# Gateway calls this to resolve agent_id from subagent_id; RO is the canonical source.


@router.get("/subagents/by-id/{subagent_id}")
async def get_subagent_by_id(subagent_id: str):
    """Resolve subagent relation by subagent_id only.

    Returns agent_id and subagent metadata for Gateway business APIs that
    accept subagent_id-only input (e.g. quadrant-tasks, vm-tools).

    Raises 404 if subagent not found.
    """
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    subagent = repo.get_by_subagent_id(subagent_id)

    if not subagent:
        raise HTTPException(status_code=404, detail=f"SubAgent not found: {subagent_id}")

    return _subagent_to_dict(subagent)


# ==================== SubAgent Operations (v14) ====================


@router.get("/subagents/due-wake")
async def get_subagents_due_for_wake():
    """Get sleeping SubAgents whose wake_at timer has expired."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    due = repo.get_due_for_wake()

    return {
        "subagents": [
            {
                "agent_id": sa.agent_id,
                "subagent_id": sa.subagent_id,
                "wake_at": sa.wake_at,
                "wake_triggers": sa.wake_triggers,
                "handoff_notes": sa.handoff_notes,
            }
            for sa in due
        ]
    }


@router.get("/subagents/{agent_id}/main")
async def get_main_subagent(agent_id: str):
    """Get the main SubAgent for an agent (creates if not exists)."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    subagent = repo.get_or_create_main_subagent(agent_id)
    return _subagent_to_dict(subagent)


@router.get("/subagents/{agent_id}/{subagent_id}")
async def get_subagent(agent_id: str, subagent_id: str):
    """Get a SubAgent by ID."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    subagent = repo.get_by_id(subagent_id, agent_id)

    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")

    return _subagent_to_dict(subagent)


@router.post("/subagents/{agent_id}/{subagent_id}/sleeping")
async def set_subagent_sleeping(agent_id: str, subagent_id: str):
    """Set SubAgent to sleeping status."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    repo.set_sleeping(subagent_id, agent_id)
    subagent = repo.get_by_id(subagent_id, agent_id)
    return {
        "success": True,
        "status": subagent.status if subagent else "sleeping",
        "previous_status": None,
    }


@router.post("/subagents/{agent_id}/{subagent_id}/awake")
async def set_subagent_awake(agent_id: str, subagent_id: str):
    """Set SubAgent to awake status (after runtime created successfully)."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    repo.set_awake(subagent_id, agent_id)
    subagent = repo.get_by_id(subagent_id, agent_id)
    return {
        "success": True,
        "status": subagent.status if subagent else "awake",
        "previous_status": None,
    }


@router.post("/subagents/{agent_id}/{subagent_id}/summarizing")
async def set_subagent_summarizing(agent_id: str, subagent_id: str):
    """Set SubAgent to summarizing status."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    repo.set_summarizing(subagent_id, agent_id)
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/completed")
async def set_subagent_completed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to completed status with result."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    existing_subagent = repo.get_by_id(subagent_id, agent_id)
    existing_result = existing_subagent.result if existing_subagent else None

    result = data.get("result") if data else None
    if existing_result:
        result = existing_result

    repo.set_completed(subagent_id, agent_id, result=result)
    return {"status": "ok", "result_preserved": bool(existing_result)}


@router.post("/subagents/{agent_id}/{subagent_id}/failed")
async def set_subagent_failed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to failed status with error message."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    error = data.get("error") if data else None
    repo.set_failed(subagent_id, agent_id, error=error)
    return {"status": "ok"}


@router.patch("/subagents/{agent_id}/{subagent_id}")
async def update_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Update SubAgent fields."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)

    if "historical_summary" in data:
        repo.update_historical_summary(subagent_id, agent_id, data["historical_summary"])

    if "wake_triggers" in data or "handoff_notes" in data:
        repo.update_wake_triggers(
            subagent_id,
            agent_id,
            data.get("wake_triggers", [{"type": "user_response"}]),
            data.get("handoff_notes")
        )

    return {"status": "ok"}


@router.post("/subagents/{agent_id}/spawn")
async def spawn_subagent(agent_id: str, data: Dict[str, Any]):
    """Spawn a new SubAgent and its Runtime (async mode)."""
    from runtime_orchestrator.db.repositories import SubAgentRepository, RuntimeRepository

    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)

    parent_subagent_id = data.get("parent_subagent_id")
    if not parent_subagent_id:
        main_subagent = subagent_repo.get_or_create_main_subagent(agent_id)
        parent_subagent_id = main_subagent.subagent_id

    task_description = data.get("task", "")
    share_context = data.get("share_context", False)
    timeout_minutes = data.get("timeout_minutes", 30)

    now = datetime.utcnow()
    timeout_at = (now + timedelta(minutes=timeout_minutes)).isoformat()

    subagent = subagent_repo.create_sub_subagent(
        agent_id,
        parent_subagent_id,
        task=task_description,
        timeout_at=timeout_at,
    )

    initial_context = []
    if share_context:
        parent_runtime = runtime_repo.get_active_runtime(parent_subagent_id, agent_id)
        if parent_runtime and parent_runtime.context:
            initial_context = parent_runtime.context.copy()

    initial_context.append({
        "role": "user",
        "content": f"[SubAgent Task]\n{task_description}"
    })

    trigger_id = f"spawn-{subagent.subagent_id}-{uuid.uuid4().hex[:8]}"

    # RO has no messages table; call Gateway to add SPAWN_SUBAGENT for Watchdog
    gateway_url = ServiceConfig.GATEWAY_URL.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            msg_resp = await client.post(
                f"{gateway_url}/internal/messages",
                json={
                    "agent_id": agent_id,
                    "type": "SPAWN_SUBAGENT",
                    "content": task_description,
                    "metadata": {
                        "subagent_id": subagent.subagent_id,
                        "trigger_id": trigger_id,
                        "initial_context": initial_context,
                        "parent_subagent_id": parent_subagent_id,
                    },
                },
            )
            msg_resp.raise_for_status()
            msg = msg_resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to register spawn message with Gateway: {e}")

    return {
        "subagent_id": subagent.subagent_id,
        "message_id": msg.get("id", msg.get("message_id", "")),
    }


@router.get("/subagents/{agent_id}/{subagent_id}/status")
async def get_subagent_status(agent_id: str, subagent_id: str):
    """Get SubAgent status for async spawn polling."""
    from runtime_orchestrator.db.repositories import SubAgentRepository, RuntimeRepository

    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)

    subagent = subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")

    if subagent.status == SubagentStatus.RUNNING.value and subagent.timeout_at:
        try:
            timeout_at = datetime.fromisoformat(subagent.timeout_at)
            if datetime.utcnow() > timeout_at:
                subagent_repo.set_failed(subagent_id, agent_id, error="SubAgent timed out")
                subagent = subagent_repo.get_by_id(subagent_id, agent_id)
        except (ValueError, TypeError):
            pass

    completed = subagent.status in (
        SubagentStatus.COMPLETED.value,
        SubagentStatus.FAILED.value,
        SubagentStatus.CANCELLED.value,
        SubagentStatus.SLEEPING.value
    )

    response = {
        "subagent_id": subagent_id,
        "status": subagent.status,
        "completed": completed,
        "progress": getattr(subagent, "progress", None),
        "result": getattr(subagent, "result", None),
        "error": getattr(subagent, "error", None),
    }

    runtime = runtime_repo.get_most_recent_runtime(subagent_id, agent_id)
    if runtime:
        response["runtime_id"] = runtime.runtime_id
        response["runtime_status"] = runtime.status
        if not response["result"] and runtime.status == RuntimeStatus.COMPLETED.value and runtime.context:
            for msg in reversed(runtime.context):
                if msg.get("role") == "assistant":
                    response["result"] = msg.get("content", "")
                    break

    return response


@router.post("/subagents/{agent_id}/{subagent_id}/cancel")
async def cancel_subagent(agent_id: str, subagent_id: str):
    """Cancel a running SubAgent."""
    from runtime_orchestrator.db.repositories import SubAgentRepository, RuntimeRepository

    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)

    subagent = subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")

    if subagent.status != SubagentStatus.RUNNING.value:
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}

    subagent_repo.set_cancelled(subagent_id, agent_id)
    runtime_ids = runtime_repo.get_runtime_ids_for_subagent(subagent_id, agent_id)
    for runtime_id in runtime_ids:
        runtime_repo.set_status(runtime_id, "cancelled")

    return {"success": True}


def _get_active_runtime_or_404(agent_id: str, subagent_id: str):
    from runtime_orchestrator.db.repositories import RuntimeRepository

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_active_runtime(subagent_id, agent_id)
    if not runtime:
        raise HTTPException(status_code=404, detail="Active runtime not found for subagent")
    return runtime, runtime_repo


@router.get("/subagents/{agent_id}/{subagent_id}/runtime")
async def get_runtime_by_subagent(agent_id: str, subagent_id: str):
    """Get active runtime state by subagent handle."""
    runtime, _ = _get_active_runtime_or_404(agent_id, subagent_id)
    data = _runtime_to_dict(runtime)
    data.pop("runtime_id", None)
    return data


@router.patch("/subagents/{agent_id}/{subagent_id}/runtime")
async def update_runtime_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Update active runtime fields by subagent handle."""
    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    runtime_id = runtime.runtime_id

    if "phase" in data and "pending_actions" in data:
        runtime_repo.set_pending_actions(runtime_id, data["pending_actions"], data["phase"])
    elif "phase" in data:
        runtime_repo.set_phase(runtime_id, data["phase"])

    if "context" in data:
        runtime_repo.update_context(runtime_id, data["context"])
    if "mcp_url" in data:
        runtime_repo.set_mcp_url(runtime_id, data["mcp_url"])
    if "status" in data:
        if data["status"] == RuntimeStatus.COMPLETED.value:
            runtime_repo.mark_completed(runtime_id)
        elif data["status"] == RuntimeStatus.FAILED.value:
            runtime_repo.mark_failed(runtime_id, data.get("error", "Unknown error"))
        elif data["status"] == RuntimeStatus.ACTIVE.value:
            runtime_repo.set_status(runtime_id, RuntimeStatus.ACTIVE.value)
    if "summary" in data:
        runtime_repo.set_summary(runtime_id, data["summary"])
    if "is_merged" in data and data["is_merged"]:
        runtime_repo.mark_merged(runtime_id)
    if "current_round_num" in data and "current_round_id" in data:
        runtime_repo.reset_round(runtime_id, data["current_round_num"], data["current_round_id"])

    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/advance")
async def advance_runtime_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Advance active runtime round by subagent handle."""
    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    expected_round_num = data.get("expected_round_num") if data else None
    new_round_id = runtime_repo.advance_round(runtime.runtime_id, expected_round_num)
    if new_round_id is None:
        return {"round_id": None, "success": False, "reason": "CAS conflict"}
    return {"round_id": new_round_id, "success": True}


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/context/append")
async def append_runtime_context_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Append context to active runtime by subagent handle."""
    message = data.get("message")
    if message is None:
        raise HTTPException(status_code=400, detail="message required")
    if not message or (isinstance(message, dict) and not message.get("role") and not message.get("content")):
        return {"success": True, "appended": False, "context_length": 0, "message": "Empty message skipped"}

    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    runtime_id = runtime.runtime_id
    context = runtime.context or []
    idempotency_key = data.get("idempotency_key")
    message_type = data.get("message_type", "unknown")
    round_id = data.get("round_id")

    if idempotency_key:
        for msg in context:
            if msg.get("_idempotency_key") == idempotency_key:
                return {
                    "success": True,
                    "appended": False,
                    "context_length": len(context),
                    "message": "Message already exists",
                }

    message_with_meta = {**message, "_round_id": round_id, "_message_type": message_type}
    if idempotency_key:
        message_with_meta["_idempotency_key"] = idempotency_key
    context.append(message_with_meta)
    runtime_repo.update_context(runtime_id, context)
    return {"success": True, "appended": True, "context_length": len(context)}


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/set-status")
async def set_runtime_status_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """CAS set active runtime status by subagent handle."""
    expected_status = data.get("expected_status")
    new_status = data.get("new_status")
    error = data.get("error")
    if not expected_status or not new_status:
        raise HTTPException(status_code=400, detail="expected_status and new_status required")
    expected_list = [expected_status] if isinstance(expected_status, str) else expected_status

    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    runtime_id = runtime.runtime_id
    if error is not None:
        success = runtime_repo.cas_set_status_with_error(runtime_id, expected_list, new_status, error)
    else:
        success = runtime_repo.cas_set_status(runtime_id, expected_list, new_status)
    if success:
        return {"success": True}
    current = runtime_repo.get_by_id(runtime_id)
    current_status = current.status if current else "not_found"
    return {"success": current_status == new_status, "current_status": current_status}


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/summarized")
async def set_runtime_summarized_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set active runtime summarized flag by subagent handle."""
    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    runtime_id = runtime.runtime_id
    success = runtime_repo.cas_set_summarized(runtime_id)
    if success:
        return {"success": True}
    current = runtime_repo.get_by_id(runtime_id)
    if not current:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": current.summarized == 1,
        "current_value": str(current.summarized),
        "message": "Already summarized" if current.summarized == 1 else "Update failed",
    }


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/hot-cold-summary")
async def set_runtime_hot_cold_summary_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Set active runtime hot/cold summaries by subagent handle."""
    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    runtime_repo.set_hot_cold_summary(
        runtime.runtime_id,
        data.get("hot_summary", ""),
        data.get("cold_summary", ""),
    )
    return {"success": True}


@router.post("/subagents/{agent_id}/{subagent_id}/runtime/need-rest")
async def set_runtime_need_rest_by_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Set active runtime need_rest flag by subagent handle."""
    runtime, runtime_repo = _get_active_runtime_or_404(agent_id, subagent_id)
    target = 1 if bool(data.get("value", True)) else 0
    runtime_repo.set_need_rest(runtime.runtime_id, target)
    current = runtime_repo.get_by_id(runtime.runtime_id)
    if not current:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": current.need_rest == target,
        "current_value": str(current.need_rest),
        "message": "OK" if current.need_rest == target else "Update failed",
    }


@router.delete("/subagents/{agent_id}/{subagent_id}")
async def delete_subagent(agent_id: str, subagent_id: str):
    """Delete a SubAgent and its runtimes."""
    from runtime_orchestrator.db.repositories import SubAgentRepository, RuntimeRepository

    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)

    with db.transaction("agent", resource_id=agent_id):
        db.execute(
            "DELETE FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )

    subagent_repo.delete(subagent_id, agent_id)
    return {"status": "ok"}


# ==================== HRL and Summary Lock Operations (v24) ====================


@router.get("/subagents/{agent_id}/{subagent_id}/hrl")
async def get_hrl(agent_id: str, subagent_id: str):
    """Get Hot Runtime List for a SubAgent."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    hrl = repo.get_hrl(subagent_id, agent_id)
    return {"hrl": hrl, "length": len(hrl)}


@router.post("/subagents/{agent_id}/{subagent_id}/hrl/add")
async def add_to_hrl(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Add a runtime to HRL."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    runtime_id = data.get("runtime_id")
    if not runtime_id:
        raise HTTPException(status_code=400, detail="runtime_id is required")
    success = repo.add_to_hrl(subagent_id, agent_id, runtime_id)
    hrl = repo.get_hrl(subagent_id, agent_id)
    return {"success": success, "hrl": hrl, "length": len(hrl)}


@router.get("/subagents/{agent_id}/{subagent_id}/summary-lock")
async def get_summary_lock(agent_id: str, subagent_id: str):
    """Get summary_lock status for a SubAgent."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    lock = repo.get_summary_lock(subagent_id, agent_id)
    return {"summary_lock": lock}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/acquire")
async def acquire_summary_lock(agent_id: str, subagent_id: str):
    """Try to acquire summary_lock using CAS."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    success = repo.acquire_summary_lock(subagent_id, agent_id)
    return {"success": success}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/release")
async def release_summary_lock(agent_id: str, subagent_id: str):
    """Release summary_lock."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    repo.release_summary_lock(subagent_id, agent_id)
    return {"success": True}


@router.post("/subagents/{agent_id}/{subagent_id}/merge-history")
async def merge_history(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Atomically update historical_summary and remove runtimes from HRL."""
    from runtime_orchestrator.db.repositories import SubAgentRepository

    db = get_db()
    repo = SubAgentRepository(db)
    new_history = data.get("new_history", "")
    remove_runtime_ids = data.get("remove_runtime_ids", [])
    success = repo.atomic_update_history_and_hrl(
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
    from runtime_orchestrator.db.repositories.drive import DriveRepository

    db = get_db()
    repo = DriveRepository(db)
    return repo.get_or_create(agent_id)


@router.get("/agents/{agent_id}/notebook-summary")
async def get_agent_notebook_summary(agent_id: str):
    """Get notebook summary for Drive Prompt builder."""
    from runtime_orchestrator.db.repositories.notebook import NotebookRepository

    db = get_db()
    repo = NotebookRepository(db)
    return repo.get_summary(agent_id)


# ==================== Agent Info & Drive Lifecycle (Phase 4) ====================


@router.post("/agents/{agent_id}/drive/increment-interaction")
async def increment_drive_interaction(agent_id: str):
    """Increment interaction count and reset no-response streak in agent_drive."""
    from runtime_orchestrator.db.repositories.drive import DriveRepository

    db = get_db()
    repo = DriveRepository(db)
    return repo.increment_interaction(agent_id)


@router.get("/agents/{agent_id}/info")
async def get_agent_info(agent_id: str):
    """Get basic agent info for system prompt builder."""
    try:
        from gateway.config.agents import get_agent_config_manager

        config_mgr = get_agent_config_manager()
        agent = config_mgr.get_agent(agent_id)
    except Exception:
        return {"name": "NovAIC Agent", "os": "unknown", "agent_id": agent_id}

    if not agent:
        return {"name": "NovAIC Agent", "os": "unknown", "agent_id": agent_id}

    return {
        "name": agent.name,
        "os": getattr(agent, "os", "unknown"),
        "agent_id": agent_id,
    }
