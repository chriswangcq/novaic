"""
Internal API for Master（Backend 组件）.

Master 通过本 API 与 Gateway（DB、任务、消息等）交互。
工具服务由 Tools Server（另一 Backend 组件）提供。仅内部使用。

v14: Added SubAgent API endpoints for SubAgent state management.
v15: Runtime-first API design - all APIs accept runtime_id and resolve agent_id/subagent_id from DB.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

from common.enums import RuntimeStatus, SubagentStatus
from common.config import ServiceConfig
from gateway.db.access import get_db

router = APIRouter(prefix="/internal", tags=["internal"])


# ==================== Runtime Resolution Helper ====================

def resolve_runtime_ids(runtime_id: str) -> Tuple[str, str, str]:
    """
    Resolve agent_id and subagent_id from runtime_id.
    
    This is the core of "runtime-first" API design:
    - MCP tools only need to pass runtime_id
    - agent_id and subagent_id are resolved from database
    
    Args:
        runtime_id: Runtime ID (rt-xxx)
    
    Returns:
        Tuple of (runtime_id, agent_id, subagent_id)
    
    Raises:
        HTTPException: If runtime not found
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime not found: {runtime_id}")
    
    return runtime.runtime_id, runtime.agent_id, runtime.subagent_id


def get_runtime_context(runtime_id: str) -> Dict[str, Any]:
    """
    Get full runtime context including agent_id, subagent_id, and runtime details.
    
    Args:
        runtime_id: Runtime ID (rt-xxx)
    
    Returns:
        Dict with runtime_id, agent_id, subagent_id, status, etc.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime not found: {runtime_id}")
    
    return {
        "runtime_id": runtime.runtime_id,
        "agent_id": runtime.agent_id,
        "subagent_id": runtime.subagent_id,
        "status": runtime.status,
        "phase": runtime.phase,
        "mcp_url": runtime.mcp_url,
    }


# ==================== SubAgent Operations (v14) ====================

@router.get("/subagents/{agent_id}/main")
def get_main_subagent(agent_id: str):
    """Get the main SubAgent for an agent (creates if not exists)."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    subagent = repo.get_or_create_main_subagent(agent_id)
    
    return _subagent_to_dict(subagent)


@router.get("/subagents/{agent_id}/{subagent_id}")
def get_subagent(agent_id: str, subagent_id: str):
    """Get a SubAgent by ID."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    subagent = repo.get_by_id(subagent_id, agent_id)
    
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    return _subagent_to_dict(subagent)


@router.post("/subagents/{agent_id}/{subagent_id}/wake")
def wake_subagent(agent_id: str, subagent_id: str, target_status: str = SubagentStatus.AWAKE.value):
    """Atomically wake a SubAgent (sleeping -> target_status).
    
    Args:
        target_status: "awaking" (intermediate) or "awake" (final)
    
    Returns success=True if wake succeeded, False if already awake/awaking.
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    success = repo.try_wake(subagent_id, agent_id, target_status=target_status)
    subagent = repo.get_by_id(subagent_id, agent_id)
    current_status = subagent.status if subagent else None
    return {
        "success": success,
        "status": current_status,
        "previous_status": None,
        "message": "Wake succeeded" if success else "Wake skipped",
    }


@router.post("/subagents/{agent_id}/{subagent_id}/sleeping")
def set_subagent_sleeping(agent_id: str, subagent_id: str):
    """Set SubAgent to sleeping status."""
    from gateway.db.repositories import SubAgentRepository
    
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
def set_subagent_awake(agent_id: str, subagent_id: str):
    """Set SubAgent to awake status (after runtime created successfully)."""
    from gateway.db.repositories import SubAgentRepository
    
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
def set_subagent_summarizing(agent_id: str, subagent_id: str):
    """Set SubAgent to summarizing status."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    repo.set_summarizing(subagent_id, agent_id)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/completed")
def set_subagent_completed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to completed status with result."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    
    result = data.get("result") if data else None
    repo.set_completed(subagent_id, agent_id, result=result)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/failed")
def set_subagent_failed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to failed status with error message."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    
    error = data.get("error") if data else None
    repo.set_failed(subagent_id, agent_id, error=error)
    
    return {"status": "ok"}


@router.patch("/subagents/{agent_id}/{subagent_id}")
def update_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Update SubAgent fields."""
    from gateway.db.repositories import SubAgentRepository
    
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
def spawn_subagent(agent_id: str, data: Dict[str, Any]):
    """
    Spawn a new SubAgent and its Runtime (async mode).
    
    Creates a sub SubAgent and triggers RuntimeStart Saga.
    Returns the subagent_id immediately. Use /status to poll for completion.
    
    Args (JSON body):
        task: Task description for the SubAgent
        share_context: If True, copy context from parent runtime
        parent_subagent_id: Parent SubAgent (defaults to main)
        timeout_minutes: Timeout in minutes (default 30)
    
    Returns:
        subagent_id: Use this to query status
    """
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime, timedelta
    import uuid
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    # Get parent subagent_id (defaults to main)
    parent_subagent_id = data.get("parent_subagent_id")
    if not parent_subagent_id:
        main_subagent = subagent_repo.get_or_create_main_subagent(agent_id)
        parent_subagent_id = main_subagent.subagent_id
    
    # Parse parameters
    task_description = data.get("task", "")
    share_context = data.get("share_context", False)
    timeout_minutes = data.get("timeout_minutes", 30)
    
    # Calculate timeout
    now = datetime.utcnow()
    timeout_at = (now + timedelta(minutes=timeout_minutes)).isoformat()
    
    # Create sub SubAgent with async fields
    subagent = subagent_repo.create_sub_subagent(
        agent_id, 
        parent_subagent_id,
        task=task_description,
        timeout_at=timeout_at,
    )
    
    # Prepare initial context
    initial_context = []
    
    # If sharing context, copy from parent's active runtime
    if share_context:
        parent_runtime = runtime_repo.get_active_runtime(parent_subagent_id, agent_id)
        if parent_runtime and parent_runtime.context:
            # Copy context but mark it as inherited
            initial_context = parent_runtime.context.copy()
    
    # Add task as user message
    initial_context.append({
        "role": "user",
        "content": f"[SubAgent Task]\n{task_description}"
    })
    
    # Set SubAgent to awaking status
    subagent_repo.try_wake(subagent.subagent_id, agent_id, target_status="awaking")
    
    # v2.1: 写入 SPAWN_SUBAGENT 消息，由 Watchdog 创建 Saga
    # Gateway 不再直接调用 Queue Service
    from gateway.db.repositories.message import MessageRepository
    
    trigger_id = f"spawn-{subagent.subagent_id}-{uuid.uuid4().hex[:8]}"
    message_repo = MessageRepository(db)
    
    # 写入消息，Watchdog 会监测并创建 runtime_start saga
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="SPAWN_SUBAGENT",
        content=task_description,
        status="sending",  # Watchdog 监测 sending 状态
        metadata={
            "subagent_id": subagent.subagent_id,
            "trigger_id": trigger_id,
            "initial_context": initial_context,
            "parent_subagent_id": parent_subagent_id,
        }
    )
    
    print(f"[Gateway] Created SPAWN_SUBAGENT message {msg['id']} for subagent {subagent.subagent_id}")
    
    return {
        "subagent_id": subagent.subagent_id,
        "message_id": msg["id"],
    }


@router.get("/subagents/{agent_id}/{subagent_id}/status")
def get_subagent_status(agent_id: str, subagent_id: str):
    """
    Get SubAgent status for async spawn polling.
    
    Returns:
        subagent_id: SubAgent ID
        status: running | completed | failed | cancelled | sleeping
        completed: True if finished (completed/failed/cancelled)
        progress: Current progress description
        result: Final result (when completed)
        error: Error message (when failed)
        runtime_id: Active runtime ID
    """
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    # Check timeout
    if subagent.status == SubagentStatus.RUNNING.value and subagent.timeout_at:
        try:
            timeout_at = datetime.fromisoformat(subagent.timeout_at)
            if datetime.utcnow() > timeout_at:
                # Mark as failed due to timeout
                subagent_repo.set_failed(
                    subagent_id, agent_id, 
                    error="SubAgent timed out"
                )
                subagent = subagent_repo.get_by_id(subagent_id, agent_id)
        except (ValueError, TypeError):
            pass  # Invalid timeout format, skip check
    
    # Determine completion status
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
    
    # Get the latest runtime
    runtimes = runtime_repo.get_latest_runtimes(subagent_id, agent_id, limit=1)
    if runtimes:
        runtime = runtimes[0]
        response["runtime_id"] = runtime.runtime_id
        response["runtime_status"] = runtime.status
        
        # If no explicit result set, try to get from runtime context
        if not response["result"] and runtime.status == RuntimeStatus.COMPLETED.value and runtime.context:
            for msg in reversed(runtime.context):
                if msg.get("role") == "assistant":
                    response["result"] = msg.get("content", "")
                    break
    
    return response


@router.post("/subagents/{agent_id}/{subagent_id}/cancel")
def cancel_subagent(agent_id: str, subagent_id: str):
    """
    Cancel a running SubAgent.
    
    Sets status to 'cancelled' and cancels all pending tasks.
    """
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    # Only cancel if running
    if subagent.status != SubagentStatus.RUNNING.value:
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
    
    # Set SubAgent to cancelled
    subagent_repo.set_cancelled(subagent_id, agent_id)
    
    # Cancel all active runtimes for this SubAgent
    runtime_ids = runtime_repo.get_runtime_ids_for_subagent(subagent_id, agent_id)
    for runtime_id in runtime_ids:
        runtime_repo.set_status(runtime_id, 'cancelled')
    
    return {"success": True}


@router.delete("/subagents/{agent_id}/{subagent_id}")
def delete_subagent(agent_id: str, subagent_id: str):
    """Delete a SubAgent and its runtimes."""
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    # Delete runtimes for this subagent
    with db.transaction("agent", resource_id=agent_id, timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT):
        db.execute(
            "DELETE FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )
    
    # Delete subagent
    subagent_repo.delete(subagent_id, agent_id)
    
    return {"status": "ok"}


# ==================== HRL and Summary Lock Operations (v24) ====================

@router.get("/subagents/{agent_id}/{subagent_id}/hrl")
def get_hrl(agent_id: str, subagent_id: str):
    """Get Hot Runtime List for a SubAgent.
    
    Returns:
        hrl: List of runtime_ids in HRL
        length: Number of runtimes in HRL
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    hrl = repo.get_hrl(subagent_id, agent_id)
    
    return {
        "hrl": hrl,
        "length": len(hrl),
    }


@router.post("/subagents/{agent_id}/{subagent_id}/hrl/add")
def add_to_hrl(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Add a runtime to HRL.
    
    Body:
        runtime_id: Runtime ID to add
        
    Returns:
        success: True if added, False if already exists
        hrl: Updated HRL list
        length: Updated HRL length
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    
    runtime_id = data.get("runtime_id")
    if not runtime_id:
        raise HTTPException(status_code=400, detail="runtime_id is required")
    
    success = repo.add_to_hrl(subagent_id, agent_id, runtime_id)
    hrl = repo.get_hrl(subagent_id, agent_id)
    
    return {
        "success": success,
        "hrl": hrl,
        "length": len(hrl),
    }


@router.get("/subagents/{agent_id}/{subagent_id}/summary-lock")
def get_summary_lock(agent_id: str, subagent_id: str):
    """Get summary_lock status for a SubAgent.
    
    Returns:
        summary_lock: 0 = idle, 1 = locked
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    lock = repo.get_summary_lock(subagent_id, agent_id)
    
    return {"summary_lock": lock}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/acquire")
def acquire_summary_lock(agent_id: str, subagent_id: str):
    """Try to acquire summary_lock using CAS.
    
    Returns:
        success: True if lock acquired, False if lock already held
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    success = repo.acquire_summary_lock(subagent_id, agent_id)
    
    return {"success": success}


@router.post("/subagents/{agent_id}/{subagent_id}/summary-lock/release")
def release_summary_lock(agent_id: str, subagent_id: str):
    """Release summary_lock.
    
    Returns:
        success: Always True
    """
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    repo.release_summary_lock(subagent_id, agent_id)
    
    return {"success": True}


@router.post("/subagents/{agent_id}/{subagent_id}/merge-history")
def merge_history(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Atomically update historical_summary and remove runtimes from HRL.
    
    Body:
        new_history: New merged historical summary
        remove_runtime_ids: List of runtime_ids to remove from HRL
        
    Returns:
        success: True if successful
    """
    from gateway.db.repositories import SubAgentRepository
    
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


# ==================== Runtime Operations ====================

@router.get("/runtimes/active")
def get_active_runtimes():
    """Get all active runtimes."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtimes = repo.get_all_active_runtimes()
    
    return {
        "runtimes": [_runtime_to_dict(r) for r in runtimes]
    }


@router.get("/runtimes/list")
def list_active_runtimes_for_mcp():
    """List all active runtimes.
    
    Used by Tools Server for runtime_list tool.
    NOTE: Must be defined BEFORE /runtimes/{runtime_id} to avoid route conflict.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtimes = runtime_repo.get_all_active_runtimes()
    
    return {
        "runtimes": [
            {
                "runtime_id": r.runtime_id,
                "agent_id": r.agent_id,
                "subagent_id": r.subagent_id,
                "type": "main" if r.subagent_id and r.subagent_id.startswith("main-") else "subagent",
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in runtimes
        ]
    }


@router.post("/runtimes/batch")
def get_runtimes_batch(data: Dict[str, Any]):
    """Get multiple runtimes by IDs (for context building).
    
    Request body:
        runtime_ids: List[str] - List of runtime IDs to fetch
        
    Returns:
        runtimes: List of runtime dicts with summaries, in input order
    """
    from gateway.db.repositories import RuntimeRepository
    
    runtime_ids = data.get("runtime_ids", [])
    if not runtime_ids:
        return {"runtimes": []}
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtimes = repo.get_runtimes_by_ids(runtime_ids)
    
    # Convert to dict with summary fields
    result = []
    for rt in runtimes:
        result.append({
            "runtime_id": rt.runtime_id,
            "subagent_id": rt.subagent_id,
            "agent_id": rt.agent_id,
            "status": rt.status,
            "simple_summary": rt.simple_summary,
            "hot_summary": rt.hot_summary,
            "cold_summary": rt.cold_summary,
            "created_at": rt.created_at,
        })
    
    return {"runtimes": result}


@router.get("/runtimes/with-tools")
def get_runtimes_with_tools():
    """Get all active runtimes that have tool_ports registered.
    
    Used by Tools Server on startup to restore runtime tool contexts.
    Returns only runtimes with status in (active, resting) AND tool_ports IS NOT NULL.
    
    NOTE: Must be defined BEFORE /runtimes/{runtime_id} to avoid route conflict.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtimes = runtime_repo.get_all_active_runtimes()
    
    # Filter to only runtimes with tool_ports registered (including empty ports)
    result = []
    for r in runtimes:
        if r.tool_ports is not None:
            result.append({
                "runtime_id": r.runtime_id,
                "agent_id": r.agent_id,
                "subagent_id": r.subagent_id,
                "tool_ports": r.tool_ports,
                "created_at": r.created_at,
            })
    
    return {"runtimes": result, "total": len(result)}


@router.get("/runtimes/{runtime_id}")
def get_runtime(runtime_id: str):
    """Get a single runtime by ID."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_by_id(runtime_id)
    
    if not runtime:
        raise HTTPException(status_code=404, detail="Runtime not found")
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes")
def create_runtime(data: Dict[str, Any]):
    """Create a new Runtime for a SubAgent (v14)."""
    from gateway.db.repositories import RuntimeRepository
    
    agent_id = data.get("agent_id")
    subagent_id = data.get("subagent_id", "main")
    initial_context = data.get("initial_context", [])
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.create_runtime(subagent_id, agent_id, initial_context)
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes/main")
def create_main_runtime(data: Dict[str, Any]):
    """Create a new Main Runtime (deprecated, use POST /runtimes)."""
    from gateway.db.repositories import RuntimeRepository, SubAgentRepository
    
    agent_id = data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    subagent_id = data.get("subagent_id")
    initial_context = data.get("initial_context", [])

    db = get_db()
    subagent_repo = SubAgentRepository(db)

    if subagent_id:
        subagent = subagent_repo.get_by_id(subagent_id, agent_id)
        if not subagent:
            raise HTTPException(status_code=404, detail="SubAgent not found")
    else:
        subagent = subagent_repo.get_or_create_main_subagent(agent_id)
        subagent_id = subagent.subagent_id

    repo = RuntimeRepository(db)
    runtime = repo.create_runtime(subagent_id, agent_id, initial_context)

    return _runtime_to_dict(runtime)


@router.patch("/runtimes/{runtime_id}")
def update_runtime(runtime_id: str, data: Dict[str, Any]):
    """Update runtime fields."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    
    # Handle specific updates
    if "phase" in data and "pending_actions" in data:
        repo.set_pending_actions(
            runtime_id, 
            data["pending_actions"], 
            data["phase"]
        )
    elif "phase" in data:
        repo.set_phase(runtime_id, data["phase"])
    
    if "context" in data:
        repo.update_context(runtime_id, data["context"])
    
    if "mcp_url" in data:
        repo.set_mcp_url(runtime_id, data["mcp_url"])
    
    if "status" in data:
        if data["status"] == RuntimeStatus.COMPLETED.value:
            repo.mark_completed(runtime_id)
        elif data["status"] == RuntimeStatus.FAILED.value:
            repo.mark_failed(runtime_id, data.get("error", "Unknown error"))
        elif data["status"] == RuntimeStatus.RESTING.value:
            repo.set_resting(runtime_id)
        elif data["status"] == RuntimeStatus.ACTIVE.value:
            repo.set_status(runtime_id, RuntimeStatus.ACTIVE.value)
    
    if "summary" in data:
        repo.set_summary(runtime_id, data["summary"])
    
    if "is_merged" in data and data["is_merged"]:
        repo.mark_merged(runtime_id)
    
    # Handle round updates
    if "current_round_num" in data and "current_round_id" in data:
        repo.reset_round(runtime_id, data["current_round_num"], data["current_round_id"])
    
    return {"status": "ok"}


@router.post("/runtimes/{runtime_id}/rest")
def rest_runtime(runtime_id: str, data: Dict[str, Any]):
    """
    Put a runtime into resting state (v14).
    
    Called by runtime_rest tool. Sets runtime status to 'resting' and
    updates the SubAgent's wake_triggers.
    
    Args:
        runtime_id: Runtime ID
        data: {
            "reason": str - Why the runtime is resting
            "wake_triggers": list - Conditions to wake up
            "handoff_notes": str - Notes for next activation
        }
    """
    from gateway.db.repositories import RuntimeRepository, SubAgentRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    subagent_repo = SubAgentRepository(db)
    
    # Check if runtime exists
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    # Set need_rest=1 (不再设置 status='resting')
    runtime_repo.set_need_rest(runtime_id, True)
    
    # Update SubAgent's wake triggers (v14)
    reason = data.get("reason", "No reason provided")
    wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
    handoff_notes = data.get("handoff_notes")
    
    subagent_repo.update_wake_triggers(
        runtime.subagent_id,
        runtime.agent_id,
        wake_triggers,
        handoff_notes
    )
    
    return {
        "success": True,
        "state": "resting",
        "reason": reason,
        "triggers_set": len(wake_triggers),
        "estimated_wake": None,
        "handoff_notes": handoff_notes,
    }


@router.post("/runtimes/{runtime_id}/wake")
def wake_runtime(runtime_id: str):
    """Wake a sleeping runtime (deprecated in v14, use SubAgent wake).
    
    Returns success=True only if the runtime was actually woken up.
    Returns success=False if runtime was already active or not found.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    success = repo.wake_main_runtime(runtime_id)
    
    return {"status": "ok" if success else "skipped", "success": success}


@router.post("/runtimes/{runtime_id}/advance")
def advance_runtime_round(runtime_id: str, data: Dict[str, Any] = None):
    """Advance runtime to next round (with optional CAS).
    
    Args:
        data: Optional dict with 'expected_round_num' for CAS operation
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    
    expected_round_num = None
    if data:
        expected_round_num = data.get("expected_round_num")
    
    new_round_id = repo.advance_round(runtime_id, expected_round_num)
    
    if new_round_id is None:
        return {"round_id": None, "success": False, "reason": "CAS conflict or runtime not found"}
    
    return {"round_id": new_round_id, "success": True}


@router.post("/runtimes/{runtime_id}/claim-phase")
def try_claim_phase(runtime_id: str, data: Dict[str, Any]):
    """Atomically claim a phase transition (CAS operation).
    
    Used to prevent race conditions where multiple Masters try to
    process the same runtime's results simultaneously.
    
    Args:
        data: {
            "expected_phase": current phase that must match
            "new_phase": phase to transition to if CAS succeeds
        }
    
    Returns:
        {"success": True} if claimed, {"success": False} if CAS failed
    """
    from datetime import datetime
    
    expected_phase = data.get("expected_phase")
    new_phase = data.get("new_phase")
    round_id = data.get("round_id")
    
    if not expected_phase or not new_phase:
        raise HTTPException(status_code=400, detail="expected_phase and new_phase required")
    
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    # Atomic CAS: only update if phase matches expected (v14: use runtime_id)
    success = runtime_repo.cas_update_phase(runtime_id, expected_phase, new_phase, round_id)
    
    return {"success": success}


@router.post("/runtimes/{runtime_id}/context/append")
def append_runtime_context(runtime_id: str, data: Dict[str, Any]):
    """Append a message to runtime context with idempotency."""
    from gateway.db.repositories import RuntimeRepository

    message = data.get("message")
    # 检查 message 是否为 None 或空字典（空字典视为无效消息）
    if message is None:
        raise HTTPException(status_code=400, detail="message required")
    # 空字典 {} 也视为无效消息，但返回成功（幂等处理）
    if not message or (isinstance(message, dict) and not message.get("role") and not message.get("content")):
        return {
            "success": True,
            "appended": False,
            "context_length": 0,
            "message": "Empty message skipped",
        }

    message_type = data.get("message_type", "unknown")
    round_id = data.get("round_id")
    idempotency_key = data.get("idempotency_key")

    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}

    context = runtime.context or []
    if idempotency_key:
        for msg in context:
            if msg.get("_idempotency_key") == idempotency_key:
                return {
                    "success": True,
                    "appended": False,
                    "context_length": len(context),
                    "message": "Message already exists",
                }

    message_with_meta = {
        **message,
        "_round_id": round_id,
        "_message_type": message_type,
    }
    if idempotency_key:
        message_with_meta["_idempotency_key"] = idempotency_key

    context.append(message_with_meta)
    repo.update_context(runtime_id, context)

    return {
        "success": True,
        "appended": True,
        "context_length": len(context),
    }


@router.post("/runtimes/{runtime_id}/set-status")
def set_runtime_status(runtime_id: str, data: Dict[str, Any]):
    """Set runtime status with CAS on expected status list."""
    from gateway.db.repositories import RuntimeRepository

    expected_status = data.get("expected_status")
    new_status = data.get("new_status")
    error = data.get("error")

    if not expected_status or not new_status:
        raise HTTPException(status_code=400, detail="expected_status and new_status required")

    if isinstance(expected_status, str):
        expected_list = [expected_status]
    else:
        expected_list = expected_status

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    # Use CAS update with expected status list
    if error is not None:
        success = runtime_repo.cas_set_status_with_error(runtime_id, expected_list, new_status, error)
    else:
        success = runtime_repo.cas_set_status(runtime_id, expected_list, new_status)

    if success:
        return {"success": True}

    # fetch current status for idempotency info
    runtime = runtime_repo.get_by_id(runtime_id)
    current_status = runtime.status if runtime else "not_found"
    return {"success": current_status == new_status, "current_status": current_status}


@router.post("/runtimes/{runtime_id}/summarized")
def set_runtime_summarized(runtime_id: str):
    """Set runtime summarized flag to 1 (idempotent)."""
    from gateway.db.repositories import RuntimeRepository

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    # Use CAS to set summarized flag
    success = runtime_repo.cas_set_summarized(runtime_id)
    
    if success:
        return {"success": True}

    # Check current value for idempotency info
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": runtime.summarized == 1,
        "current_value": str(runtime.summarized),
        "message": "Already summarized" if runtime.summarized == 1 else "Update failed",
    }


@router.post("/runtimes/{runtime_id}/hot-cold-summary")
def set_runtime_hot_cold_summary(runtime_id: str, data: Dict[str, Any]):
    """Set both hot and cold summaries for a runtime (v24).
    
    Hot summary: Earlier rounds summarized + last 3 rounds full content
    Cold summary: All rounds summarized by LLM
    """
    from gateway.db.repositories import RuntimeRepository

    hot_summary = data.get("hot_summary", "")
    cold_summary = data.get("cold_summary", "")

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    runtime_repo.set_hot_cold_summary(runtime_id, hot_summary, cold_summary)

    return {"success": True, "runtime_id": runtime_id}


@router.post("/runtimes/{runtime_id}/need-rest")
def set_runtime_need_rest(runtime_id: str, data: Dict[str, Any]):
    """Set runtime need_rest flag with CAS (idempotent)."""
    from gateway.db.repositories import RuntimeRepository

    value = bool(data.get("value", True))
    target = 1 if value else 0

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    # Use CAS to set need_rest flag
    success = runtime_repo.cas_set_need_rest(runtime_id, value)

    if success:
        return {"success": True, "current_value": str(target)}

    # Check current value for idempotency info
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": runtime.need_rest == target,
        "current_value": str(runtime.need_rest),
        "message": f"Already need_rest={target}" if runtime.need_rest == target else "Update failed",
    }


@router.post("/runtimes/{runtime_id}/tool-ports")
def set_runtime_tool_ports(runtime_id: str, data: Dict[str, Any]):
    """Save Tools Server MCP ports for a runtime.
    
    Called by Tools Server when registering/unregistering a runtime.
    Enables recovery after Tools Server restart.
    
    Request body:
        ports: dict - MCP ports (e.g. {"vmuse": 8080}), or null to clear
    """
    from gateway.db.repositories import RuntimeRepository
    
    ports = data.get("ports")
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    if ports is not None:
        runtime_repo.set_tool_ports(runtime_id, ports)
    else:
        runtime_repo.clear_tool_ports(runtime_id)
    
    return {"success": True, "runtime_id": runtime_id}


@router.delete("/runtimes/{runtime_id}")
def delete_runtime(runtime_id: str):
    """Delete a runtime."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    repo.delete(runtime_id)
    
    return {"status": "ok"}


@router.get("/runtimes/main/{agent_id}")
def get_main_runtime(agent_id: str):
    """Get active main runtime for an agent (v14: from main SubAgent)."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_active_runtime("main", agent_id)
    
    if not runtime:
        return {"runtime": None}
    
    return {"runtime": _runtime_to_dict(runtime)}


@router.get("/runtimes/subagent/{agent_id}/{subagent_id}")
def get_subagent_runtime(agent_id: str, subagent_id: str):
    """Get active runtime for a SubAgent (v14)."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_active_runtime(subagent_id, agent_id)
    
    if not runtime:
        return {"runtime": None}
    
    return {"runtime": _runtime_to_dict(runtime)}


@router.get("/runtimes/latest/{agent_id}/{subagent_id}")
def get_latest_runtimes(agent_id: str, subagent_id: str, limit: int = 30):
    """Get latest completed runtimes for a SubAgent (for context preparation, v14)."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtimes = repo.get_latest_runtimes(subagent_id, agent_id, limit)
    
    return {"runtimes": [_runtime_to_dict(r) for r in runtimes]}


@router.get("/agents/{agent_id}/subagents/{subagent_id}/has-active-runtime")
def has_active_runtime(agent_id: str, subagent_id: str):
    """Check if SubAgent has an active runtime (active/resting status)."""
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    has_active = repo.has_active_runtime(subagent_id, agent_id)
    
    return {"has_active_runtime": has_active}


# ==================== Message Operations ====================

@router.get("/messages/unread/{agent_id}")
def get_unread_messages(agent_id: str):
    """Get unread messages for an agent (for Scheduler to include in context).
    
    Uses read=0 to find messages that haven't been processed yet.
    """
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    messages = repo.get_unread(agent_id)
    
    # Filter for USER_MESSAGE type only (matching original behavior)
    user_messages = [m for m in messages if m.get("type") == "USER_MESSAGE"]
    
    return {"messages": user_messages}


@router.get("/messages/unread-sent/{agent_id}")
def get_unread_sent_messages(agent_id: str):
    """Get unread sent user messages for an agent."""
    from gateway.db.repositories.message import MessageRepository

    db = get_db()
    repo = MessageRepository(db)
    messages = repo.get_unread(agent_id)
    
    # Filter for USER_MESSAGE type only (matching original behavior)
    user_messages = [
        {"id": m["id"], "content": m["content"], "timestamp": m["timestamp"]}
        for m in messages if m.get("type") == "USER_MESSAGE"
    ]

    return {"messages": user_messages}


@router.get("/messages/unread-count/{agent_id}")
def get_unread_count(agent_id: str):
    """Get count of unread messages (for Monitor to detect new messages).
    
    Uses read=0 to find messages that haven't been processed yet.
    """
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    count = repo.get_unread_user_message_count(agent_id)
    
    return {"count": count}


@router.get("/messages/unread-grouped")
def get_unread_messages_grouped(agent_id: Optional[str] = None):
    """Get unread messages grouped by agent_id (v14 for Monitor).
    
    Returns all agents with unread USER_MESSAGE messages.
    Uses read=0 to find messages that haven't been processed yet.
    """
    
    db = get_db()
    
    # Get all unread messages with their agent_id
    rows = db.fetchall("""
        SELECT id, agent_id, type, content, metadata, timestamp 
        FROM chat_messages 
        WHERE read = 0 AND type = 'USER_MESSAGE'
        ORDER BY agent_id, timestamp ASC
    """)
    
    # Group by agent_id
    messages_by_agent: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        aid = row["agent_id"]
        if aid not in messages_by_agent:
            messages_by_agent[aid] = []
        messages_by_agent[aid].append({
            "id": row["id"],
            "type": row["type"],
            "content": row["content"],
            "metadata": json.loads(row["metadata"]) if row.get("metadata") else {},
            "timestamp": row["timestamp"],
        })
    
    return {"messages_by_agent": messages_by_agent}


@router.post("/messages/claim-and-prepare")
def claim_and_prepare_message():
    """Claim one sending message and prepare for processing.
    
    Used by Watchdog to:
    1. Find a sending message
    2. Claim it (sending → sent) atomically
    3. Return message info for saga creation
    
    Returns:
        {"message": {...}} if claimed, {"message": null} if queue is empty
    """
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    message = repo.claim_sending()
    
    return {"message": message}


@router.post("/messages/{message_id}/claim")
def claim_message(message_id: str):
    """
    Claim a message (sending -> sent) with CAS.
    
    Uses FIFO lock (sharded by message_id) to ensure fair ordering.
    """
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    
    claimed = repo.claim_by_id(message_id)
    
    if claimed:
        return {"success": True, "message_id": message_id, "claimed": True}

    # Check current status using repository
    msg = repo.get_message(message_id)
    current_status = msg["status"] if msg else "not_found"
    return {
        "success": current_status == "sent",
        "message_id": message_id,
        "claimed": False,
        "current_status": current_status,
    }


@router.get("/messages/has-new/{agent_id}")
def has_new_messages(agent_id: str):
    """Check if agent has new sent unread user messages."""
    from gateway.db.repositories.message import MessageRepository

    db = get_db()
    repo = MessageRepository(db)
    count = repo.get_pending_count(agent_id)
    
    return {"has_new_messages": count > 0}


@router.patch("/messages/mark-read")
def mark_messages_read(data: Dict[str, Any]):
    """Mark messages as read and broadcast status update."""
    from datetime import datetime
    import uuid as uuid_module
    from gateway.db.repositories.message import MessageRepository
    
    message_ids = data.get("message_ids", [])
    agent_id = data.get("agent_id")  # Optional: for SSE filtering
    
    if not message_ids:
        return {"status": "ok"}
    
    db = get_db()
    repo = MessageRepository(db)
    
    # If no agent_id provided, try to get it from the first message
    if not agent_id:
        msg = repo.get_message(message_ids[0])
        if msg:
            agent_id = msg["agent_id"]
    
    # Batch mark as read
    repo.batch_mark_read(message_ids, agent_id)
    
    # Broadcast STATUS_UPDATE to SSE for each message
    try:
        from main_gateway import _chat_subscribers
        for msg_id in message_ids:
            status_update = {
                "id": str(uuid_module.uuid4())[:8],
                "type": "STATUS_UPDATE",
                "message_id": msg_id,
                "status": "read",
                "agent_id": agent_id,  # Include agent_id for SSE filtering
                "timestamp": datetime.now().isoformat(),
            }
            for queue in _chat_subscribers.values():
                try:
                    queue.put_nowait(status_update)
                except:
                    pass
    except Exception as e:
        print(f"[Internal] Failed to broadcast status update: {e}")
    
    return {"status": "ok"}


@router.patch("/messages/mark-processed")
def mark_messages_processed(data: Dict[str, Any]):
    """Mark messages as read and broadcast status update to SSE.
    
    Note: 'processed' concept is merged into 'read'. Once read=1, message is considered processed.
    """
    from datetime import datetime
    import uuid as uuid_module
    from gateway.db.repositories.message import MessageRepository
    
    message_ids = data.get("message_ids", [])
    agent_id = data.get("agent_id")  # Optional: for SSE filtering
    
    if not message_ids:
        return {"status": "ok"}
    
    db = get_db()
    repo = MessageRepository(db)
    
    # If no agent_id provided, try to get it from the first message
    if not agent_id:
        msg = repo.get_message(message_ids[0])
        if msg:
            agent_id = msg["agent_id"]
    
    # Batch mark as read (read=1 means processed)
    repo.batch_mark_read(message_ids, agent_id)
    
    # Broadcast STATUS_UPDATE to SSE for each message
    # Import here to avoid circular import
    try:
        from main_gateway import _chat_subscribers
        for msg_id in message_ids:
            status_update = {
                "id": str(uuid_module.uuid4())[:8],
                "type": "STATUS_UPDATE",
                "message_id": msg_id,
                "status": "read",
                "agent_id": agent_id,  # Include agent_id for SSE filtering
                "timestamp": datetime.now().isoformat(),
            }
            for queue in _chat_subscribers.values():
                try:
                    queue.put_nowait(status_update)
                except:
                    pass
    except Exception as e:
        print(f"[Internal] Failed to broadcast status update: {e}")
    
    return {"status": "ok"}


@router.post("/messages")
def create_message(data: Dict[str, Any]):
    """Create a chat message (for agent replies).
    
    Agent replies use status='sent' directly (no Monitor processing needed).
    """
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    
    msg = repo.add_message(
        agent_id=data["agent_id"],
        type=data["type"],
        content=data["content"],
        metadata=data.get("metadata"),
        status="sent",  # v18: Agent replies skip Monitor queue
    )
    
    return msg


# ==================== Agent Operations ====================

@router.get("/agents/setup-complete")
def get_setup_complete_agents():
    """Get all agents with setup complete."""
    from gateway.db.repositories import AgentRepository
    
    db = get_db()
    agent_repo = AgentRepository(db)
    agent_ids = agent_repo.list_setup_complete_ids()
    
    return {"agent_ids": agent_ids}


@router.post("/agents/{agent_id}/awake")
def set_agent_awake(agent_id: str):
    """Set agent state to awake."""
    from gateway.db.repositories import AgentStateRepository
    
    db = get_db()
    repo = AgentStateRepository(db)
    repo.set_awake(agent_id)
    
    return {"status": "ok"}


@router.post("/agents/{agent_id}/sleep")
def set_agent_sleep(agent_id: str, data: Dict[str, Any] = None):
    """Set agent state to sleep."""
    from gateway.db.repositories import AgentStateRepository
    
    db = get_db()
    repo = AgentStateRepository(db)
    reason = (data or {}).get("reason", "Task completed")
    repo.set_sleep(agent_id, reason=reason)
    
    return {"status": "ok"}


# 工具服务由 Backend 组件 Tools Server 提供（api/internal_mcp.py）；Master 调 Tools Server /internal/mcp/*

# ==================== SSE Broadcast ====================

@router.post("/broadcast/new-task")
def broadcast_new_task(data: Dict[str, Any]):
    """Broadcast new task event to workers."""
    from gateway.sse.broadcaster import get_worker_broadcaster
    
    broadcaster = get_worker_broadcaster()
    if not broadcaster:
        return {"status": "ok", "broadcast": False}
    
    task_id = data.get("task_id")
    task_type = data.get("task_type")
    agent_id = data.get("agent_id")
    
    broadcaster.broadcast_new_task(
        task_id=task_id,
        agent_id=agent_id,
        task_type=task_type,
    )
    
    return {"status": "ok", "broadcast": True}


@router.post("/broadcast/chat-message")
def broadcast_chat_message(data: Dict[str, Any]):
    """Broadcast chat message to UI."""
    try:
        from main import broadcast_chat_message as _broadcast
        _broadcast(data.get("message", {}), agent_id=data.get("agent_id"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==================== Config ====================

@router.get("/config/agent/{agent_id}")
def get_agent_config(agent_id: str):
    """Get agent configuration."""
    from gateway.config.agents import get_agent_config_manager
    
    agent_mgr = get_agent_config_manager()
    agent = agent_mgr.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": agent.id,
        "name": agent.name,
        "agent_index": agent.vm.agent_index,
        "default_model": agent.default_model,
    }


@router.get("/config/ports/{agent_index}")
def get_ports_for_agent(agent_index: int):
    """
    Get port configuration for an agent by index.
    
    Pure computation based on agent_index, no database access.
    Used by Tools Server and other services.
    """
    from gateway.config.agents import allocate_ports_for_agent, GATEWAY_PORT, BASE_PORT, PORTS_PER_AGENT
    
    if agent_index < 0 or agent_index >= 100:
        raise HTTPException(status_code=400, detail="agent_index must be 0-99")
    
    ports = allocate_ports_for_agent(agent_index)
    return {
        "agent_index": agent_index,
        "gateway_port": GATEWAY_PORT,
        "base_port": BASE_PORT,
        "ports_per_agent": PORTS_PER_AGENT,
        "ports": {
            "vm": ports.vm,
            "session": ports.session,
            "local": ports.local,
            "memory": ports.memory,
            "chat": ports.chat,
            "qemudebug": ports.qemudebug,
            "vnc": ports.vnc,
            "websocket": ports.websocket,
            "ssh": ports.ssh,
        }
    }


@router.get("/config/llm")
def get_llm_config():
    """
    Get LLM configuration (API keys and models).
    
    Used by Worker processes that need to call LLM.
    Returns sanitized config (no full API keys exposed).
    """
    from gateway.config import get_config_manager
    
    config = get_config_manager().load()
    
    # Group models by api_key_id
    models_by_key = {}
    for m in config.candidate_models:
        if m.api_key_id not in models_by_key:
            models_by_key[m.api_key_id] = []
        models_by_key[m.api_key_id].append({
            "id": m.id,
            "name": m.name,
            "enabled": m.enabled,
            "is_custom": m.is_custom,
        })
    
    return {
        "default_model": config.default_model,
        "api_keys": [
            {
                "id": key.id,
                "provider": key.provider.value if hasattr(key.provider, 'value') else str(key.provider),
                "name": key.name,
                "api_base": key.api_base,
                # Only return masked key for security
                "api_key_masked": key.api_key[:8] + "..." if key.api_key else None,
                "candidate_models": models_by_key.get(key.id, [])
            }
            for key in config.api_keys
        ]
    }


@router.get("/config/llm/full")
def get_llm_config_full():
    """
    Get full LLM configuration including API keys.
    
    INTERNAL USE ONLY - includes sensitive data.
    Used by task_queue workers for LLM calls.
    
    Returns model config for the default_model, including:
    - model: model name
    - provider: openai/anthropic/google
    - api_key: full API key
    - api_base: API base URL
    """
    from gateway.config import get_config_manager
    
    config = get_config_manager().load()
    
    # Find the model config for default_model
    default_model_info = next(
        (m for m in config.candidate_models if m.name == config.default_model),
        None
    )
    
    if not default_model_info:
        return {
            "success": False,
            "error": f"Default model '{config.default_model}' not found in candidate_models",
            "default_model": config.default_model,
            "candidate_models": [m.name for m in config.candidate_models],
        }
    
    # Get the API key for this model
    api_key_entry = config.get_api_key_by_id(default_model_info.api_key_id)
    
    if not api_key_entry:
        return {
            "success": False,
            "error": f"API key not found for model '{config.default_model}'",
            "default_model": config.default_model,
        }
    
    return {
        "success": True,
        "default_model": config.default_model,
        "model_config": {
            "model": default_model_info.name,
            "provider": api_key_entry.provider.value if hasattr(api_key_entry.provider, 'value') else str(api_key_entry.provider),
            "api_key": api_key_entry.api_key,
            "api_base": api_key_entry.get_effective_base_url(),
        }
    }


def _build_llm_config_for_agent(db, agent_id: str) -> Dict[str, Any]:
    """Build LLM config for a specific agent (internal helper)."""
    
    # 1. Check agent exists (agents table may not have model_id column)
    with db.get_connection("agent", resource_id=agent_id, timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT) as conn:
        cursor = conn.execute(
            "SELECT id FROM agents WHERE id = ?",
            (agent_id,)
        )
        row = cursor.fetchone()
    
    if not row:
        return {
            "success": False,
            "error": f"Agent '{agent_id}' not found",
            "agent_id": agent_id,
        }
    
    # 2. Use default model from config (agents table doesn't have model_id column yet)
    with db.get_connection("global", timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT) as conn:
        cursor = conn.execute("SELECT value FROM config WHERE key = 'default_model'")
        default_row = cursor.fetchone()
    model_id = default_row[0].strip('"') if default_row else "gpt-4o"
    
    # 3. 从DB查询model和api_key配置
    with db.get_connection("global", timeout=ServiceConfig.DB_TRANSACTION_TIMEOUT) as conn:
        cursor = conn.execute("""
            SELECT 
                m.id as model_id,
                m.provider,
                k.provider as key_provider,
                k.api_key,
                k.api_base
            FROM candidate_models m
            JOIN api_keys k ON m.api_key_id = k.id
            WHERE m.id = ? AND m.available = 1
            LIMIT 1
        """, (model_id,))
        row = cursor.fetchone()
    
    if not row:
        return {
            "success": False,
            "error": f"Model '{model_id}' not found in candidate_models",
            "agent_id": agent_id,
            "model_id": model_id,
        }
    
    if not row[3]:  # api_key
        return {
            "success": False,
            "error": f"API key not configured for model '{model_id}'",
            "agent_id": agent_id,
            "model_id": model_id,
        }
    
    # 使用model表的provider或api_key表的provider
    provider = row[1] if row[1] else row[2]
    api_base = row[4] if row[4] else "https://api.openai.com/v1"
    
    return {
        "success": True,
        "agent_id": agent_id,
        "model": row[0],  # model_id (e.g. "kimi-k2.5")
        "provider": provider,
        "api_key": row[3],  # api_key
        "api_base": api_base,
    }


@router.get("/config/llm/agent/{agent_id}")
def get_agent_llm_config(agent_id: str):
    """
    Get LLM configuration for a specific agent.
    
    INTERNAL USE ONLY - includes sensitive data.
    Used by task_queue workers for LLM calls.
    
    Logic:
    1. If agent has model_id set, use that model
    2. Otherwise, use system default_model
    
    Returns:
    - success: bool
    - agent_id: str
    - model: model name
    - provider: openai/anthropic/google  
    - api_key: full API key
    - api_base: API base URL
    """
    db = get_db()
    return _build_llm_config_for_agent(db, agent_id)


@router.get("/config/llm/runtime/{runtime_id}")
def get_runtime_llm_config(runtime_id: str):
    """
    Get LLM configuration for a specific runtime.
    
    INTERNAL USE ONLY - includes sensitive data.
    Used by task_queue workers for LLM calls.
    
    Logic:
    1. Resolve agent_id and subagent_id from runtime_id
    2. Use agent's model_id if set, else default_model
    
    Returns:
    - success: bool
    - agent_id: str
    - subagent_id: str (e.g. "main-7b053af9")
    - model: model name
    - provider: openai/anthropic/google  
    - api_key: full API key
    - api_base: API base URL
    """
    
    db = get_db()
    runtime_ctx = get_runtime_context(runtime_id)
    agent_id = runtime_ctx.get("agent_id")
    subagent_id = runtime_ctx.get("subagent_id", "main")
    
    # Get LLM config for agent
    result = _build_llm_config_for_agent(db, agent_id)
    
    # Add subagent_id to result (needed for execution_log broadcast)
    result["subagent_id"] = subagent_id
    
    return result


# ==================== LLM Operations ====================

@router.post("/llm/compact-context")
def compact_context_with_llm(data: Dict[str, Any]):
    """
    Compact context using LLM.
    
    This endpoint calls an LLM to generate a summary of older messages.
    Used by Master's Scheduler for context compaction.
    """
    import httpx
    from gateway.config.settings import get_context_compaction_settings
    
    messages_to_compact = data.get("messages", [])
    agent_id = data.get("agent_id")
    
    if not messages_to_compact:
        return {"success": True, "summary": ""}
    
    # Get compaction settings
    settings = get_context_compaction_settings()
    
    # Get API configuration from database
    from gateway.db.repositories import ConfigRepository
    
    db = get_db()
    config_repo = ConfigRepository(db)
    
    # Get first API key from api_keys table
    row = config_repo.get_first_api_key()
    if not row:
        return {"success": False, "error": "No API keys configured"}
    
    api_key = row["api_key"]
    base_url = row["api_base"] or "https://api.openai.com/v1"
    
    # Use compaction model from settings
    model = settings.compaction_model
    
    # Format messages for compaction
    messages_text = "\n".join([
        f"[{m.get('role', 'unknown')}]: {m.get('content', '')[:ServiceConfig.TEXT_TRUNCATE_MESSAGE]}"
        for m in messages_to_compact
    ])
    
    # Build LLM request
    llm_messages = [
        {"role": "system", "content": settings.compaction_prompt},
        {"role": "user", "content": f"请压缩以下对话历史：\n\n{messages_text}"}
    ]
    
    try:
        with httpx.Client(timeout=ServiceConfig.LLM_CALL_TIMEOUT, trust_env=False) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": llm_messages,
                    "temperature": ServiceConfig.LLM_TEMPERATURE_DEFAULT,
                    "max_tokens": ServiceConfig.LLM_MAX_TOKENS_DEFAULT,
                }
            )
            response.raise_for_status()
            result = response.json()
            
            summary = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            return {
                "success": True,
                "summary": summary,
                "compacted_count": len(messages_to_compact),
            }
    except Exception as e:
        print(f"[Internal] LLM compaction failed: {e}")
        return {"success": False, "error": str(e)}


# ==================== Helpers ====================

def _runtime_to_dict(runtime) -> Dict[str, Any]:
    """Convert runtime to dictionary (v14 schema + v25 tool_ports)."""
    return {
        "runtime_id": runtime.runtime_id,
        "subagent_id": runtime.subagent_id,
        "agent_id": runtime.agent_id,
        "mcp_url": runtime.mcp_url,
        "current_round_id": runtime.current_round_id,
        "current_round_num": runtime.current_round_num,
        "phase": runtime.phase,
        "context": runtime.context,
        "pending_actions": runtime.pending_actions,
        "status": runtime.status,
        "error": runtime.error,
        "summary": runtime.summary,
        "need_rest": getattr(runtime, "need_rest", None),
        "summarized": getattr(runtime, "summarized", None),
        "is_merged": runtime.is_merged,
        "tool_ports": getattr(runtime, "tool_ports", None),
        "created_at": runtime.created_at,
        "updated_at": runtime.updated_at,
    }


def _subagent_to_dict(subagent) -> Dict[str, Any]:
    """Convert SubAgent to dictionary (v14)."""
    return {
        "subagent_id": subagent.subagent_id,
        "agent_id": subagent.agent_id,
        "type": subagent.type,
        "parent_subagent_id": subagent.parent_subagent_id,
        "status": subagent.status,
        "historical_summary": subagent.historical_summary,
        "wake_triggers": subagent.wake_triggers,
        "handoff_notes": subagent.handoff_notes,
        "created_at": subagent.created_at,
        "updated_at": subagent.updated_at,
    }


# ==================== MCP Gateway Proxy (DEPRECATED) ====================
# NOTE: MCP Gateway (FastMCP) has been replaced by Tools Server.
# The following APIs have been removed:
# - /internal/mcp/agent-shared/* 
# - /internal/mcp/runtime/*
# - /internal/mcp/aggregate/*
# - /internal/mcp/servers
# Use Tools Server APIs at /internal/runtimes/* instead.


# ==================== Health Monitor Operations (v18) ====================

@router.get("/health/stuck-sending")
def get_stuck_sending_count(timeout_seconds: int = None):
    """Get count of messages stuck in 'sending' state."""
    if timeout_seconds is None:
        timeout_seconds = ServiceConfig.STUCK_SENDING_TIMEOUT
    from gateway.db.repositories import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    count = repo.reset_stuck_sending(timeout_seconds)
    
    return {"count": count}


@router.get("/health/stuck-awaking")
def get_stuck_awaking_count(timeout_seconds: int = None):
    """Get count of SubAgents stuck in 'awaking' state."""
    if timeout_seconds is None:
        timeout_seconds = ServiceConfig.STUCK_AWAKING_TIMEOUT
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    count = repo.get_stuck_awaking_count(timeout_seconds)
    
    return {"count": count}


@router.post("/health/reset-stuck-awaking")
def reset_stuck_awaking(timeout_seconds: int = None):
    """Reset SubAgents stuck in 'awaking' state to 'sleeping'."""
    if timeout_seconds is None:
        timeout_seconds = ServiceConfig.STUCK_AWAKING_TIMEOUT
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    count = repo.reset_stuck_awaking(timeout_seconds)
    
    return {"reset_count": count}


# ==================== TaskManager API (for Tools Server) ====================

@router.post("/tasks/spawn")
def task_spawn(data: Dict[str, Any]):
    """Spawn a new task.
    
    Used by Tools Server to create background tasks.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    result = task_manager.spawn(
        task_type=data.get("task_type", "tool"),
        config=data.get("config", {}),
        label=data.get("label"),
        timeout_seconds=data.get("timeout_seconds", 0),
        notify_on=data.get("notify_on"),
        parent_session_key=data.get("parent_session_key"),
        agent_id=data.get("agent_id"),
    )
    return result


@router.post("/tasks/create-completed")
def task_create_completed(data: Dict[str, Any]):
    """Create an immediately completed task for truncated output storage.
    
    Used by Tools Server for _auto_truncate_result.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    task_id = task_manager.create_completed(
        tool_name=data.get("tool_name", "unknown"),
        truncated_result=data.get("truncated_result", ""),
        full_output=data.get("full_output", ""),
        ttl_hours=data.get("ttl_hours", 24),
        agent_id=data.get("agent_id"),
    )
    return {"task_id": task_id}


@router.get("/tasks/{task_id}")
def task_get_status(
    task_id: str,
    include_outputs: bool = False,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    tail_lines: Optional[int] = None,
):
    """Get task status by ID.
    
    Used by Tools Server for task_query tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.get_status(
        task_id=task_id,
        include_outputs=include_outputs,
        start_line=start_line,
        end_line=end_line,
        tail_lines=tail_lines,
    )


@router.get("/tasks")
def task_list(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """List tasks.
    
    Used by Tools Server for task_list tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    status_filter = [status] if status else None
    return task_manager.get_status(
        task_id=None,
        status_filter=status_filter,
        agent_id=agent_id,
    )


@router.post("/tasks/{task_id}/cancel")
def task_cancel(task_id: str, reason: Optional[str] = None):
    """Cancel a task.
    
    Used by Tools Server for task_cancel tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.cancel(task_id, reason)


@router.get("/tasks/{task_id}/result")
def task_get_result(task_id: str, format: str = "summary"):
    """Get task result.
    
    Used by Tools Server for task_result tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.get_result(task_id, format=format)


# ==================== SSH Key API (for Tools Server) ====================

@router.get("/vm/ssh/public-key")
def get_ssh_public_key():
    """Get default SSH public key.
    
    Used by Tools Server (qemudebug) to inject SSH key into VM.
    """
    from gateway.vm.ssh import get_ssh_key_manager
    
    manager = get_ssh_key_manager()
    public_key = manager.get_public_key()
    
    return {"public_key": public_key}


@router.get("/vm/ssh/private-key-path")
def get_ssh_private_key_path():
    """Get path to SSH private key file.
    
    Used by Tools Server (qemudebug) for SSH connections.
    Returns the path where Gateway has written the private key.
    """
    from gateway.vm.ssh import get_ssh_key_manager
    
    manager = get_ssh_key_manager()
    key_path = manager.get_private_key_path()
    
    return {"key_path": str(key_path)}


# ==================== Runtime Tools API ====================
# NOTE: /runtimes/list moved to line ~480 (before /runtimes/{runtime_id}) to fix route conflict.

@router.post("/runtimes/{runtime_id}/history")
def get_runtime_history(runtime_id: str, data: Dict[str, Any]):
    """Get message history for a runtime.
    
    Used by Tools Server for runtime_history tool.
    Queries runtime's context which contains the conversation history.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    
    limit = data.get("limit", ServiceConfig.MAX_RUNTIME_CONTEXT_PER_PAGE)
    offset = data.get("offset", 0)
    
    # Get runtime and its context
    runtime = repo.get_by_id(runtime_id)
    if not runtime:
        return {"messages": [], "total": 0, "error": "Runtime not found"}
    
    # Extract messages from context
    context = runtime.context or []
    messages = []
    for msg in context:
        if isinstance(msg, dict) and "role" in msg:
            content = msg.get("content", "")
            if len(content) > ServiceConfig.TEXT_TRUNCATE_MESSAGE:
                content = content[:ServiceConfig.TEXT_TRUNCATE_MESSAGE] + "..."
            messages.append({
                "role": msg.get("role"),
                "content": content,
                "timestamp": msg.get("timestamp"),
            })
    
    # Apply pagination
    total = len(messages)
    messages = messages[offset:offset + limit]
    
    return {
        "messages": messages,
        "total": total,
    }


@router.post("/runtimes/{runtime_id}/send")
def send_to_runtime(runtime_id: str, data: Dict[str, Any]):
    """Send a message to a runtime.
    
    Used by Tools Server for runtime_send tool.
    Appends the message to the runtime's context.
    """
    from gateway.db.repositories import RuntimeRepository
    from datetime import datetime
    
    db = get_db()
    repo = RuntimeRepository(db)
    
    message = data.get("message", "")
    
    # Get runtime
    runtime = repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    # Append message to runtime context
    context = runtime.context or []
    context.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat(),
    })
    
    repo.update_context(runtime_id, context)
    
    return {"success": True, "queued": True, "runtime_id": runtime_id}


# ==================== Web API (for Tools Server local tools) ====================
# NOTE: Legacy Chat API (/chat/*) removed in v15.
# Use Runtime-First API: /rt/{runtime_id}/chat/* instead.

@router.post("/web/search")
def web_search(data: Dict[str, Any]):
    """Search the web using Brave Search API.
    
    Used by Tools Server for web_search tool.
    """
    import os
    import httpx
    
    BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
    
    if not BRAVE_API_KEY:
        return {
            "error": "BRAVE_API_KEY not configured",
            "results": []
        }
    
    query = data.get("query", "")
    count = min(data.get("count", 10), 20)
    freshness = data.get("freshness")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            params = {"q": query, "count": count}
            if freshness:
                params["freshness"] = freshness
            
            response = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params=params,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_API_KEY
                }
            )
            response.raise_for_status()
            api_data = response.json()
            
            results = []
            for item in api_data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "age": item.get("age", "")
                })
            
            return {
                "results": results,
                "query": query,
                "total_count": api_data.get("web", {}).get("total", len(results))
            }
    except Exception as e:
        return {"error": str(e), "results": []}


@router.post("/web/fetch")
def web_fetch(data: Dict[str, Any]):
    """Fetch a web page and convert to markdown.
    
    Used by Tools Server for web_fetch tool.
    """
    import re
    import httpx
    
    url = data.get("url", "")
    extract_main_content = data.get("extract_main_content", True)
    max_length = data.get("max_length", 50000)
    
    try:
        with httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            
            html_content = response.text
            title = ""
            content = ""
            
            if extract_main_content:
                try:
                    from readability import Document
                    doc = Document(html_content)
                    title = doc.title()
                    html_content = doc.summary()
                except Exception:
                    pass
            
            # Convert HTML to markdown
            try:
                import html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                content = h.handle(html_content)
            except Exception:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")
                if not title:
                    title_tag = soup.find("title")
                    title = title_tag.get_text() if title_tag else ""
                content = soup.get_text(separator="\n", strip=True)
            
            if not title:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                title_tag = soup.find("title")
                title = title_tag.get_text() if title_tag else url
            
            content = re.sub(r'\n{3,}', '\n\n', content).strip()
            
            if len(content) > max_length:
                content = content[:max_length] + "\n\n... [Content truncated]"
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "word_count": len(content.split()),
                "success": True
            }
    except Exception as e:
        return {"url": url, "error": str(e), "success": False}


# ==================== Runtime-First API (v15) ====================
# NOTE: Legacy QEMU API (/vm/qemu/{agent_id}/*) removed in v15.
# Use Runtime-First API: /rt/{runtime_id}/qemu/* instead.
# All APIs accept runtime_id and resolve agent_id/subagent_id from database.
# This simplifies Tools Server tools - they only need to know runtime_id.

# ---------- Memory APIs (via runtime_id) ----------

@router.post("/rt/{runtime_id}/memory/save")
def rt_memory_save(runtime_id: str, data: Dict[str, Any]):
    """Save memory value. Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    return repo.save(
        agent_id=agent_id,
        key=data.get("key"),
        value=data.get("value"),
        namespace=data.get("namespace", "default")
    )


@router.post("/rt/{runtime_id}/memory/recall")
def rt_memory_recall(runtime_id: str, data: Dict[str, Any]):
    """Recall memory value(s). Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    return repo.recall(
        agent_id=agent_id,
        key=data.get("key"),
        namespace=data.get("namespace", "default")
    )


@router.post("/rt/{runtime_id}/memory/delete")
def rt_memory_delete(runtime_id: str, data: Dict[str, Any]):
    """Delete memory value. Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    return repo.delete(
        agent_id=agent_id,
        key=data.get("key"),
        namespace=data.get("namespace", "default")
    )


@router.get("/rt/{runtime_id}/memory/namespaces")
def rt_memory_list_namespaces(runtime_id: str):
    """List all memory namespaces. Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    namespaces = repo.list_namespaces(agent_id)
    return {"success": True, "namespaces": namespaces}


@router.post("/rt/{runtime_id}/memory/task/log")
def rt_memory_log_task(runtime_id: str, data: Dict[str, Any]):
    """Log a task action. Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    return repo.log_task(
        agent_id=agent_id,
        action=data.get("action"),
        details=data.get("details"),
        status=data.get("status", "completed")
    )


@router.post("/rt/{runtime_id}/memory/task/history")
def rt_memory_get_task_history(runtime_id: str, data: Dict[str, Any]):
    """Get task history. Agent ID resolved from runtime."""
    from gateway.db.repositories.memory import MemoryRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MemoryRepository(db)
    return repo.get_task_history(
        agent_id=agent_id,
        limit=data.get("limit", 20),
        status_filter=data.get("status_filter")
    )


# ---------- Chat APIs (via runtime_id) ----------

@router.post("/rt/{runtime_id}/chat/event")
def rt_chat_event(runtime_id: str, data: Dict[str, Any]):
    """Send a chat event. Agent ID resolved from runtime."""
    import uuid
    import asyncio
    from gateway.sse.broadcaster import get_worker_broadcaster
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    event_type = data.get("type", "AGENT_REPLY")
    event_data = data.get("data", {})
    
    # Extract content based on event type
    if event_type == "AGENT_REPLY":
        content = event_data.get("message", "")
    elif event_type == "AGENT_ASK":
        question = event_data.get("question", "")
        options = event_data.get("options")
        content = question
        if options:
            content += "\n\n选项: " + ", ".join(options)
    elif event_type == "AGENT_NOTIFY":
        content = event_data.get("message", "")
        level = event_data.get("level", "info")
        content = f"[{level}] {content}"
    elif event_type == "AGENT_IMAGE":
        image_url = event_data.get("image_url", "")
        caption = event_data.get("caption", "")
        content = f"[图片: {image_url}]"
        if caption:
            content += f"\n{caption}"
    else:
        content = event_data.get("message", "") or json.dumps(event_data)
    
    # Store message using MessageRepository
    from gateway.db.repositories.message import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    msg = repo.add_message(
        agent_id=agent_id,
        type=event_type,
        content=content,
        status="sent",  # Agent events are already confirmed, skip Monitor queue
    )
    message_id = msg["id"]
    timestamp = msg["timestamp"]
    
    # Broadcast via Worker SSE (for other workers)
    broadcaster = get_worker_broadcaster()
    if broadcaster:
        try:
            from gateway.sse.broadcaster import SSEEvent
            broadcaster.broadcast(
                event_type=SSEEvent.NEW_MESSAGE,
                data={"message_id": message_id, "agent_id": agent_id, "type": event_type, "content": content},
            )
        except Exception:
            pass
    
    # Broadcast to UI SSE subscribers (for frontend real-time display)
    # This is the key fix: _chat_subscribers is the SSE channel for frontend UI
    try:
        from main_gateway import _chat_subscribers
        
        # Build message in the format frontend expects
        ui_message = {
            "id": message_id,
            "type": event_type,
            "timestamp": timestamp,
            "agent_id": agent_id,
            # Include both 'message' and 'content' for compatibility
            "message": content,
            "content": content,
        }
        
        # Add extra fields based on event type
        if event_type == "AGENT_ASK":
            ui_message["question"] = event_data.get("question", "")
            ui_message["options"] = event_data.get("options")
            ui_message["request_id"] = event_data.get("request_id")
        elif event_type == "AGENT_NOTIFY":
            ui_message["level"] = event_data.get("level", "info")
        elif event_type == "AGENT_IMAGE":
            ui_message["image_url"] = event_data.get("image_url", "")
            ui_message["caption"] = event_data.get("caption", "")
        
        # Push to all UI SSE subscribers
        for queue in _chat_subscribers.values():
            try:
                queue.put_nowait(ui_message)
            except asyncio.QueueFull:
                pass
        
        print(f"[rt_chat_event] Broadcasted {event_type} to {len(_chat_subscribers)} UI subscribers")
    except Exception as e:
        print(f"[rt_chat_event] Failed to broadcast to UI SSE: {e}")
    
    return {"success": True, "event_type": event_type, "message_id": message_id}


@router.get("/rt/{runtime_id}/chat/history")
def rt_chat_history(
    runtime_id: str, 
    limit: int = None, 
    summary_length: int = None
):
    """Get chat history. Agent ID resolved from runtime."""
    if limit is None:
        limit = ServiceConfig.DEFAULT_CHAT_LIMIT
    if summary_length is None:
        summary_length = ServiceConfig.DEFAULT_SUMMARY_LENGTH
    from gateway.db.repositories.message import MessageRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MessageRepository(db)
    messages = repo.get_history(agent_id, limit=limit)
    
    result_messages = []
    for m in messages:
        content = m.get("content", "") or ""
        if summary_length > 0 and len(content) > summary_length:
            content = content[:summary_length] + "..."
        msg_type = m.get("type", "")
        role = "user" if msg_type == "USER_MESSAGE" else "assistant"
        result_messages.append({
            "id": m.get("id"), "role": role, "type": msg_type,
            "content": content, "timestamp": m.get("timestamp"),
        })
    
    return {"messages": result_messages, "has_more": len(messages) >= limit}


@router.get("/rt/{runtime_id}/chat/message/{message_id}")
def rt_chat_get_message(runtime_id: str, message_id: str):
    """Get full content of a chat message."""
    from gateway.db.repositories.message import MessageRepository
    
    # Validate runtime exists (also verifies access)
    resolve_runtime_ids(runtime_id)
    
    db = get_db()
    repo = MessageRepository(db)
    message = repo.get_message(message_id)
    if not message:
        return {"success": False, "error": "Message not found"}
    
    msg_type = message.get("type", "")
    role = "user" if msg_type == "USER_MESSAGE" else "assistant"
    return {
        "success": True, "id": message.get("id"), "role": role,
        "type": msg_type, "content": message.get("content"), "timestamp": message.get("timestamp"),
    }


# ---------- SubAgent APIs (via runtime_id) ----------

@router.post("/rt/{runtime_id}/subagent/spawn")
def rt_subagent_spawn(runtime_id: str, data: Dict[str, Any]):
    """Spawn a SubAgent. Agent ID and parent SubAgent ID resolved from runtime."""
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import timedelta
    import uuid
    
    _, agent_id, parent_subagent_id = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    task_description = data.get("task", "")
    share_context = data.get("share_context", False)
    timeout_minutes = data.get("timeout_minutes", 30)
    
    now = datetime.utcnow()
    timeout_at = (now + timedelta(minutes=timeout_minutes)).isoformat()
    
    # Create sub SubAgent
    subagent = subagent_repo.create_sub_subagent(
        agent_id, parent_subagent_id, task=task_description, timeout_at=timeout_at,
    )
    
    # Prepare initial context
    initial_context = []
    if share_context:
        parent_runtime = runtime_repo.get_by_id(runtime_id)
        if parent_runtime and parent_runtime.context:
            initial_context = parent_runtime.context.copy()
    
    initial_context.append({"role": "user", "content": f"[SubAgent Task]\n{task_description}"})
    
    # Set SubAgent to awaking status
    subagent_repo.try_wake(subagent.subagent_id, agent_id, target_status="awaking")
    
    # v2.1: 写入 SPAWN_SUBAGENT 消息，由 Watchdog 创建 Saga
    # Gateway 不再直接调用 Queue Service
    from gateway.db.repositories.message import MessageRepository
    import uuid
    
    trigger_id = f"spawn-{subagent.subagent_id}-{uuid.uuid4().hex[:8]}"
    message_repo = MessageRepository(db)
    
    # 写入消息，Watchdog 会监测并创建 runtime_start saga
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="SPAWN_SUBAGENT",
        content=task_description,
        status="sending",  # Watchdog 监测 sending 状态
        metadata={
            "subagent_id": subagent.subagent_id,
            "trigger_id": trigger_id,
            "initial_context": initial_context,
            "parent_subagent_id": parent_subagent_id,
        }
    )
    
    print(f"[Gateway] Created SPAWN_SUBAGENT message {msg['id']} for subagent {subagent.subagent_id}")
    
    return {
        "subagent_id": subagent.subagent_id,
        "message_id": msg["id"],
    }


@router.get("/rt/{runtime_id}/subagent/{target_subagent_id}/status")
def rt_subagent_query(runtime_id: str, target_subagent_id: str):
    """Query SubAgent status. Agent ID resolved from runtime."""
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = subagent_repo.get_by_id(target_subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    # Check timeout
    if subagent.status == SubagentStatus.RUNNING.value and subagent.timeout_at:
        try:
            timeout_at = datetime.fromisoformat(subagent.timeout_at)
            if datetime.utcnow() > timeout_at:
                subagent_repo.set_failed(target_subagent_id, agent_id, error="SubAgent timed out")
                subagent = subagent_repo.get_by_id(target_subagent_id, agent_id)
        except (ValueError, TypeError):
            pass
    
    completed = subagent.status in (
        SubagentStatus.COMPLETED.value,
        SubagentStatus.FAILED.value,
        SubagentStatus.CANCELLED.value,
        SubagentStatus.SLEEPING.value
    )
    response = {
        "subagent_id": target_subagent_id, "status": subagent.status, "completed": completed,
        "progress": getattr(subagent, "progress", None),
        "result": getattr(subagent, "result", None),
        "error": getattr(subagent, "error", None),
    }
    
    runtimes = runtime_repo.get_latest_runtimes(target_subagent_id, agent_id, limit=1)
    if runtimes:
        rt = runtimes[0]
        response["runtime_id"] = rt.runtime_id
        response["runtime_status"] = rt.status
        if not response["result"] and rt.status == RuntimeStatus.COMPLETED.value and rt.context:
            for msg in reversed(rt.context):
                if msg.get("role") == "assistant":
                    response["result"] = msg.get("content", "")
                    break
    
    return response


@router.post("/rt/{runtime_id}/subagent/{target_subagent_id}/cancel")
def rt_subagent_cancel(runtime_id: str, target_subagent_id: str):
    """Cancel a running SubAgent."""
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = subagent_repo.get_by_id(target_subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    if subagent.status != SubagentStatus.RUNNING.value:
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
    
    subagent_repo.set_cancelled(target_subagent_id, agent_id)
    
    # Cancel active runtimes
    runtime_ids = runtime_repo.get_runtime_ids_for_subagent(target_subagent_id, agent_id)
    for rid in runtime_ids:
        runtime_repo.set_status(rid, 'cancelled')
    
    return {"success": True}


# ---------- QEMU APIs (via runtime_id) ----------

@router.post("/rt/{runtime_id}/qemu/ssh-exec")
async def rt_qemu_ssh_exec(runtime_id: str, data: Dict[str, Any]):
    """Execute command via SSH on VM. Agent ID resolved from runtime."""
    import asyncio
    from gateway.vm.ssh import get_ssh_key_manager
    from gateway.config.agents import allocate_ports_for_agent, get_agent_config_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    command = data.get("command", "")
    timeout = data.get("timeout", 30)
    
    # Get agent index for port allocation
    config_mgr = get_agent_config_manager()
    agents = config_mgr.list_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.id == agent_id:
            agent_index = i
            break
    
    ports = allocate_ports_for_agent(agent_index)
    ssh_port = ports.ssh
    
    try:
        import asyncssh
        ssh_manager = get_ssh_key_manager()
        key_path = ssh_manager.get_private_key_path()
        
        async with asyncssh.connect(
            host="127.0.0.1", port=ssh_port, username="ubuntu",
            known_hosts=None, client_keys=[str(key_path)], compression_algs=None,
        ) as conn:
            result = await asyncio.wait_for(conn.run(command, check=False), timeout=timeout)
            return {
                "stdout": result.stdout, "stderr": result.stderr,
                "exit_code": result.exit_status, "success": result.exit_status == 0
            }
    except asyncio.TimeoutError:
        return {"error": f"Command timed out after {timeout}s", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


@router.get("/rt/{runtime_id}/qemu/status")
def rt_qemu_status(runtime_id: str):
    """Get QEMU VM status. Agent ID resolved from runtime."""
    import os
    from gateway.config.agents import allocate_ports_for_agent, get_agent_config_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    config_mgr = get_agent_config_manager()
    agents = config_mgr.list_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.id == agent_id:
            agent_index = i
            break
    
    ports = allocate_ports_for_agent(agent_index)
    data_dir = os.environ.get("NOVAIC_DATA_DIR", os.path.expanduser("~/.novaic"))
    pid_file = os.path.join(data_dir, "agents", agent_id, "vm", "qemu.pid")
    
    qemu_running = False
    qemu_pid = None
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                qemu_pid = int(f.read().strip())
            os.kill(qemu_pid, 0)
            qemu_running = True
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    
    return {
        "qemu_running": qemu_running, "qemu_pid": qemu_pid,
        "ports": {"ssh": ports.ssh, "vnc": ports.vnc, "websocket": ports.websocket},
        "agent_id": agent_id,
    }


@router.post("/rt/{runtime_id}/qemu/start")
def rt_qemu_start(runtime_id: str, data: Dict[str, Any]):
    """Start the QEMU VM. Agent ID resolved from runtime."""
    from gateway.vm import get_vm_manager
    from gateway.config.agents import get_agent_config_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    # Get agent index for port allocation
    config_mgr = get_agent_config_manager()
    agents = config_mgr.list_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.id == agent_id:
            agent_index = agent.vm.agent_index if hasattr(agent.vm, 'agent_index') else i
            break
    
    memory = data.get("memory", "4096")
    cpus = data.get("cpus", 4)
    
    try:
        manager = get_vm_manager()
        result = manager.start(
            agent_id=agent_id,
            agent_index=agent_index,
            memory=memory,
            cpus=cpus,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/rt/{runtime_id}/qemu/shutdown")
def rt_qemu_shutdown(runtime_id: str, data: Dict[str, Any]):
    """Shutdown the QEMU VM gracefully. Agent ID resolved from runtime."""
    from gateway.vm import get_vm_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    graceful = data.get("graceful", True)
    quick = data.get("quick", False)
    
    try:
        manager = get_vm_manager()
        result = manager.stop(
            agent_id=agent_id,
            graceful=graceful,
            quick=quick,
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/rt/{runtime_id}/qemu/restart")
def rt_qemu_restart(runtime_id: str, data: Dict[str, Any]):
    """Restart the QEMU VM (stop then start). Agent ID resolved from runtime."""
    from gateway.vm import get_vm_manager
    from gateway.config.agents import get_agent_config_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    # Get agent index for port allocation
    config_mgr = get_agent_config_manager()
    agents = config_mgr.list_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.id == agent_id:
            agent_index = agent.vm.agent_index if hasattr(agent.vm, 'agent_index') else i
            break
    
    graceful = data.get("graceful", True)
    
    try:
        manager = get_vm_manager()
        
        # Stop the VM first
        stop_result = manager.stop(
            agent_id=agent_id,
            graceful=graceful,
            quick=False,  # Use normal timeout for restart
        )
        
        # Start the VM again
        start_result = manager.start(
            agent_id=agent_id,
            agent_index=agent_index,
            memory="4096",  # Default memory
            cpus=4,         # Default CPUs
        )
        
        return {
            "success": True,
            "stop_result": stop_result,
            "start_result": start_result,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/rt/{runtime_id}/qemu/deploy-vmuse")
async def rt_qemu_deploy_vmuse(runtime_id: str, data: Dict[str, Any]):
    """
    Deploy novaic-mcp-vmuse code to VM.
    
    智能部署流程：
    1. 检查 cloud-init 是否完成（未完成则返回 wait 状态）
    2. 复制代码到 /opt/novaic-mcp-vmuse/
    3. 启动 novaic.service
    4. 验证 MCP 服务是否响应
    
    Agent ID resolved from runtime.
    """
    import os
    import asyncio
    from gateway.vm.ssh import get_ssh_key_manager
    from gateway.config.agents import allocate_ports_for_agent, get_agent_config_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    restart_service = data.get("restart_service", True)
    force = data.get("force", False)
    
    result = {
        "success": False,
        "status": "error",
        "cloudinit_complete": False,
        "cloudinit_progress": "",
        "venv_ready": False,
        "files_copied": [],
        "service_status": "unknown",
        "mcp_reachable": False,
    }
    
    # Get agent index for port allocation
    config_mgr = get_agent_config_manager()
    agents = config_mgr.list_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.id == agent_id:
            agent_index = agent.vm.agent_index if hasattr(agent.vm, 'agent_index') else i
            break
    
    ports = allocate_ports_for_agent(agent_index)
    ssh_port = ports.ssh
    mcp_port = ports.vm
    
    # 1. 找到 novaic-mcp-vmuse 路径
    # 统一路径搜索逻辑，优先级：环境变量 -> 相对于项目根目录
    from pathlib import Path
    
    vmuse_path = None
    search_paths = []
    
    # Priority 1: NOVAIC_RESOURCE_DIR environment variable (production)
    resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR")
    if resource_dir:
        candidate = os.path.join(resource_dir, "novaic-mcp-vmuse")
        search_paths.append(candidate)
        if os.path.isdir(candidate):
            vmuse_path = candidate
            print(f"[deploy_vmuse] Found vmuse via NOVAIC_RESOURCE_DIR: {vmuse_path}")
    
    # Priority 2: Relative to project root (development/packaged)
    if not vmuse_path:
        # novaic-backend/gateway/api/internal.py -> project_root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        
        # Try: project_root/novaic-vm (correct location)
        candidate = project_root / "novaic-vm"
        search_paths.append(str(candidate))
        if candidate.exists() and candidate.is_dir():
            vmuse_path = str(candidate)
            print(f"[deploy_vmuse] Found vmuse via project root: {vmuse_path}")
        
        # Fallback: Try Tauri resources directory (development build)
        if not vmuse_path:
            candidate = project_root / "novaic-app" / "src-tauri" / "resources" / "novaic-mcp-vmuse"
            search_paths.append(str(candidate))
            if candidate.exists() and candidate.is_dir():
                vmuse_path = str(candidate)
                print(f"[deploy_vmuse] Found vmuse via Tauri resources: {vmuse_path}")
    
    if not vmuse_path:
        result["error"] = f"novaic-mcp-vmuse not found. Set NOVAIC_RESOURCE_DIR environment variable or ensure project structure is correct. Searched: {search_paths}"
        return result
    
    print(f"[deploy_vmuse] Using vmuse path: {vmuse_path}")
    
    try:
        import asyncssh
        
        # 2. SSH 连接
        ssh_manager = get_ssh_key_manager()
        key_path = ssh_manager.get_private_key_path()
        
        connect_kwargs = {
            "host": "127.0.0.1",
            "port": ssh_port,
            "username": "ubuntu",
            "known_hosts": None,
            "client_keys": [str(key_path)],
            "compression_algs": None,
        }
        
        async with asyncssh.connect(**connect_kwargs) as conn:
            # 3. 检查 cloud-init 状态
            cloudinit_check = await conn.run(
                "test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
                check=False
            )
            cloudinit_done = "DONE" in cloudinit_check.stdout
            result["cloudinit_complete"] = cloudinit_done
            
            if not cloudinit_done and not force:
                # 获取 cloud-init 进度
                progress_result = await conn.run(
                    "tail -5 /var/log/cloud-init-output.log 2>/dev/null | head -1 || echo 'Initializing...'",
                    check=False
                )
                result["cloudinit_progress"] = progress_result.stdout.strip()
                result["status"] = "wait"
                result["success"] = True
                result["message"] = "Cloud-init not complete. Wait and retry, or use force=true to proceed anyway."
                return result
            
            # 4. 检查 venv 是否就绪
            venv_check = await conn.run(
                "test -d /opt/novaic-venv/bin && echo 'READY' || echo 'MISSING'",
                check=False
            )
            result["venv_ready"] = "READY" in venv_check.stdout
            
            # 5. 停止服务
            await conn.run("sudo systemctl stop novaic 2>/dev/null || true", check=False)
            
            # 6. 创建目标目录
            await conn.run("sudo mkdir -p /opt/novaic-mcp-vmuse && sudo chown -R ubuntu:ubuntu /opt/novaic-mcp-vmuse", check=False)
            
            # 7. 清理旧代码
            await conn.run("rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills", check=False)
            
            files_copied = []
            
            # 8. 复制 src/
            src_path = os.path.join(vmuse_path, "src")
            if os.path.exists(src_path):
                await asyncssh.scp(src_path, (conn, "/opt/novaic-mcp-vmuse/"), recurse=True)
                files_copied.append("src/")
            
            # 9. 复制 pyproject.toml
            pyproject_path = os.path.join(vmuse_path, "pyproject.toml")
            if os.path.exists(pyproject_path):
                await asyncssh.scp(pyproject_path, (conn, "/opt/novaic-mcp-vmuse/"))
                files_copied.append("pyproject.toml")
            
            # 10. 复制 README.md (if exists)
            readme_path = os.path.join(vmuse_path, "README.md")
            if os.path.exists(readme_path):
                await asyncssh.scp(readme_path, (conn, "/opt/novaic-mcp-vmuse/"))
                files_copied.append("README.md")
            
            result["files_copied"] = files_copied
            
            # 11. 重启服务
            service_status = "not_restarted"
            if restart_service:
                restart_result = await conn.run("sudo systemctl restart novaic", check=False)
                if restart_result.exit_status == 0:
                    service_status = "restarted"
                    # Wait a moment for service to start
                    await asyncio.sleep(2)
                else:
                    service_status = f"restart_failed: {restart_result.stderr.strip()}"
            
            result["service_status"] = service_status
            
            # 12. 验证 MCP 服务
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    mcp_response = await http_client.get(f"http://127.0.0.1:{mcp_port}/health")
                    result["mcp_reachable"] = mcp_response.status_code == 200
            except Exception:
                result["mcp_reachable"] = False
            
            result["success"] = True
            result["status"] = "deployed"
            result["source_path"] = vmuse_path
            return result
            
    except asyncio.TimeoutError:
        result["error"] = "SSH connection timed out"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


# ---------- Task APIs (via runtime_id) ----------

@router.post("/rt/{runtime_id}/tasks/spawn")
def rt_task_spawn(runtime_id: str, data: Dict[str, Any]):
    """Spawn a new task. Agent ID resolved from runtime."""
    from gateway.core.task_manager import get_task_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.spawn(
        task_type=data.get("task_type", "tool"),
        config=data.get("config", {}),
        label=data.get("label"),
        timeout_seconds=data.get("timeout_seconds", 0),
        notify_on=data.get("notify_on"),
        parent_session_key=runtime_id,  # Use runtime_id as session key
        agent_id=agent_id,
    )


@router.get("/rt/{runtime_id}/tasks")
def rt_task_list(runtime_id: str, status: Optional[str] = None):
    """List tasks. Agent ID resolved from runtime."""
    from gateway.core.task_manager import get_task_manager
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    status_filter = [status] if status else None
    return task_manager.get_status(task_id=None, status_filter=status_filter, agent_id=agent_id)


# Note: task_query, task_cancel, task_summary don't need runtime_id - they use task_id directly
