"""
Internal API for Master（Backend 组件）.

Master 通过本 API 与 Gateway（DB、任务、消息等）交互。
MCP 生命周期由 MCP Gateway（另一 Backend 组件）提供。仅内部使用。

v14: Added SubAgent API endpoints for SubAgent state management.
v15: Runtime-first API design - all APIs accept runtime_id and resolve agent_id/subagent_id from DB.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

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
    
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.execute(
            "SELECT runtime_id, agent_id, subagent_id FROM agent_runtimes WHERE runtime_id = ?",
            (runtime_id,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Runtime not found: {runtime_id}")
    
    return row[0], row[1], row[2]


def get_runtime_context(runtime_id: str) -> Dict[str, Any]:
    """
    Get full runtime context including agent_id, subagent_id, and runtime details.
    
    Args:
        runtime_id: Runtime ID (rt-xxx)
    
    Returns:
        Dict with runtime_id, agent_id, subagent_id, status, etc.
    """
    
    db = get_db()
    with db.get_connection() as conn:
        cursor = conn.execute(
            """SELECT runtime_id, agent_id, subagent_id, status, phase, mcp_url
               FROM agent_runtimes WHERE runtime_id = ?""",
            (runtime_id,)
        )
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Runtime not found: {runtime_id}")
    
    return {
        "runtime_id": row[0],
        "agent_id": row[1],
        "subagent_id": row[2],
        "status": row[3],
        "phase": row[4],
        "mcp_url": row[5],
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
def wake_subagent(agent_id: str, subagent_id: str, target_status: str = "awake"):
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
    from task_queue import get_saga_orchestrator
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
    
    # Trigger RuntimeStart Saga
    orchestrator = get_saga_orchestrator()
    if orchestrator:
        trigger_id = f"spawn-{subagent.subagent_id}-{uuid.uuid4().hex[:8]}"
        orchestrator.create(
            saga_type="runtime_start",
            context={
                "agent_id": agent_id,
                "subagent_id": subagent.subagent_id,
                "trigger_id": trigger_id,
                "initial_context": initial_context,
            },
            idempotency_key=f"runtime-start-{trigger_id}",
        )
    
    return {
        "subagent_id": subagent.subagent_id,
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
    if subagent.status == "running" and subagent.timeout_at:
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
    completed = subagent.status in ("completed", "failed", "cancelled", "sleeping")
    
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
        if not response["result"] and runtime.status == "completed" and runtime.context:
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
    if subagent.status != "running":
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
    
    # Set SubAgent to cancelled
    subagent_repo.set_cancelled(subagent_id, agent_id)
    
    # Cancel all active runtimes for this SubAgent
    now = datetime.utcnow().isoformat()
    with db.get_connection("agent", resource_id=agent_id, timeout=10.0) as conn:
        # Get runtime IDs for this SubAgent
        cursor = conn.execute(
            "SELECT runtime_id FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )
        runtime_ids = [row[0] for row in cursor.fetchall()]
        
        # Cancel active runtimes
        for runtime_id in runtime_ids:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'cancelled', updated_at = ?
                WHERE runtime_id = ? AND status = 'active'
            """, (now, runtime_id))
        
        conn.commit()
    
    return {"success": True}


@router.delete("/subagents/{agent_id}/{subagent_id}")
def delete_subagent(agent_id: str, subagent_id: str):
    """Delete a SubAgent and its runtimes."""
    from gateway.db.repositories import SubAgentRepository, RuntimeRepository
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    # Delete runtimes for this subagent
    with db.get_connection("agent", resource_id=agent_id, timeout=10.0) as conn:
        conn.execute(
            "DELETE FROM runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )
        conn.commit()
    
    # Delete subagent
    subagent_repo.delete(subagent_id, agent_id)
    
    return {"status": "ok"}


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
        if data["status"] == "completed":
            repo.mark_completed(runtime_id)
        elif data["status"] == "failed":
            repo.mark_failed(runtime_id, data.get("error", "Unknown error"))
        elif data["status"] == "resting":
            repo.set_resting(runtime_id)
        elif data["status"] == "active":
            repo.set_status(runtime_id, "active")
    
    if "summary" in data:
        repo.set_summary(runtime_id, data["summary"])
    
    if "is_merged" in data and data["is_merged"]:
        repo.mark_merged(runtime_id)
    
    # Handle round updates
    if "current_round_num" in data and "current_round_id" in data:
        # Directly update round fields
        now = datetime.utcnow().isoformat()
        # Extract agent_id from runtime
        runtime = runtime_repo.get_by_id(runtime_id)
        if runtime:
            with db.get_connection("agent", resource_id=runtime.agent_id, timeout=10.0) as conn:
                conn.execute("""
                    UPDATE agent_runtimes 
                    SET current_round_num = ?, current_round_id = ?, updated_at = ?
                    WHERE runtime_id = ?
                """, (data["current_round_num"], data["current_round_id"], now, runtime_id))
                conn.commit()
    
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
    with db.get_connection("agent", resource_id=runtime.agent_id, timeout=10.0) as conn:
        conn.execute(
            "UPDATE agent_runtimes SET need_rest = 1, updated_at = datetime('now') WHERE runtime_id = ?",
            (runtime_id,)
        )
        conn.commit()
    
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
    
    db = get_db()
    now = datetime.utcnow().isoformat()
    
    # Atomic CAS: only update if phase matches expected (v14: use runtime_id)
    if round_id:
        cursor = db.execute("""
            UPDATE agent_runtimes 
            SET phase = ?, current_round_id = ?, updated_at = ?
            WHERE runtime_id = ? AND phase = ?
        """, (new_phase, round_id, now, runtime_id, expected_phase))
    else:
        cursor = db.execute("""
            UPDATE agent_runtimes 
            SET phase = ?, updated_at = ?
            WHERE runtime_id = ? AND phase = ?
        """, (new_phase, now, runtime_id, expected_phase))
    db.commit()
    
    return {"success": cursor.rowcount > 0}


@router.post("/runtimes/{runtime_id}/context/append")
def append_runtime_context(runtime_id: str, data: Dict[str, Any]):
    """Append a message to runtime context with idempotency."""
    from gateway.db.repositories import RuntimeRepository

    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message required")

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
    from datetime import datetime

    expected_status = data.get("expected_status")
    new_status = data.get("new_status")
    error = data.get("error")

    if not expected_status or not new_status:
        raise HTTPException(status_code=400, detail="expected_status and new_status required")

    if isinstance(expected_status, str):
        expected_list = [expected_status]
    else:
        expected_list = expected_status

    placeholders = ",".join("?" for _ in expected_list)
    now = datetime.utcnow().isoformat()

    db = get_db()
    with db.get_connection() as conn:
        if error is not None:
            cursor = conn.execute(
                f"""
                UPDATE agent_runtimes
                SET status = ?, error = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
                """,
                (new_status, error, now, runtime_id, *expected_list),
            )
        else:
            cursor = conn.execute(
                f"""
                UPDATE agent_runtimes
                SET status = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
                """,
                (new_status, now, runtime_id, *expected_list),
            )
        conn.commit()

    if cursor.rowcount > 0:
        return {"success": True}

    # fetch current status for idempotency info
    row = db.fetchone(
        "SELECT status FROM agent_runtimes WHERE runtime_id = ?",
        (runtime_id,),
    )
    current_status = row["status"] if row else "not_found"
    return {"success": current_status == new_status, "current_status": current_status}


@router.post("/runtimes/{runtime_id}/summarized")
def set_runtime_summarized(runtime_id: str):
    """Set runtime summarized flag to 1 (idempotent)."""
    from datetime import datetime

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False}
    
    now = datetime.utcnow().isoformat()
    with db.get_connection("agent", resource_id=runtime.agent_id, timeout=10.0) as conn:
        cursor = conn.execute("""
            UPDATE agent_runtimes
            SET summarized = 1, updated_at = ?
            WHERE runtime_id = ? AND summarized = 0
        """, (now, runtime_id))
        conn.commit()

    if cursor.rowcount > 0:
        return {"success": True}

    row = db.fetchone(
        "SELECT summarized FROM agent_runtimes WHERE runtime_id = ?",
        (runtime_id,),
    )
    if not row:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": row["summarized"] == 1,
        "current_value": str(row["summarized"]),
        "message": "Already summarized" if row["summarized"] == 1 else "Update failed",
    }


@router.post("/runtimes/{runtime_id}/need-rest")
def set_runtime_need_rest(runtime_id: str, data: Dict[str, Any]):
    """Set runtime need_rest flag with CAS (idempotent)."""
    from datetime import datetime

    value = bool(data.get("value", True))
    target = 1 if value else 0
    expected = 0 if value else 1
    now = datetime.utcnow().isoformat()

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "cas_failed": False}
    
    with db.get_connection("agent", resource_id=runtime.agent_id, timeout=10.0) as conn:
        cursor = conn.execute("""
            UPDATE agent_runtimes
            SET need_rest = ?, updated_at = ?
            WHERE runtime_id = ? AND need_rest = ?
        """, (target, now, runtime_id, expected))
        conn.commit()

    if cursor.rowcount > 0:
        return {"success": True, "current_value": str(target)}

    row = db.fetchone(
        "SELECT need_rest FROM agent_runtimes WHERE runtime_id = ?",
        (runtime_id,),
    )
    if not row:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    return {
        "success": row["need_rest"] == target,
        "current_value": str(row["need_rest"]),
        "message": f"Already need_rest={target}" if row["need_rest"] == target else "Update failed",
    }


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
    
    db = get_db()
    rows = db.fetchall("""
        SELECT id, type, content, metadata, timestamp 
        FROM chat_messages 
        WHERE agent_id = ? AND read = 0 AND type = 'USER_MESSAGE'
        ORDER BY timestamp ASC
    """, (agent_id,))
    
    return {
        "messages": [
            {
                "id": row["id"],
                "type": row["type"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row.get("metadata") else {},
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    }


@router.get("/messages/unread-sent/{agent_id}")
def get_unread_sent_messages(agent_id: str):
    """Get unread sent user messages for an agent."""

    db = get_db()
    rows = db.fetchall("""
        SELECT id, content, timestamp
        FROM chat_messages
        WHERE agent_id = ? AND type = 'USER_MESSAGE' AND status = 'sent' AND read = 0
        ORDER BY created_at ASC
    """, (agent_id,))

    return {
        "messages": [
            {"id": row["id"], "content": row["content"], "timestamp": row["timestamp"]}
            for row in rows
        ]
    }


@router.get("/messages/unread-count/{agent_id}")
def get_unread_count(agent_id: str):
    """Get count of unread messages (for Monitor to detect new messages).
    
    Uses read=0 to find messages that haven't been processed yet.
    """
    
    db = get_db()
    row = db.fetchone("""
        SELECT COUNT(*) as count FROM chat_messages 
        WHERE agent_id = ? AND read = 0 AND type = 'USER_MESSAGE'
    """, (agent_id,))
    
    return {"count": row["count"] if row else 0}


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
    
    db = get_db()
    with db.get_connection() as conn:
        # Atomically claim one sending message (sending → sent)
        # Note: read 字段由 context.read 设置，这里不改变
        cursor = conn.execute("""
            UPDATE chat_messages
            SET status = 'sent'
            WHERE id = (
                SELECT id FROM chat_messages 
                WHERE status = 'sending' 
                ORDER BY created_at ASC 
                LIMIT 1
            )
            RETURNING id, agent_id, type, content, metadata, timestamp
        """)
        row = cursor.fetchone()
        cursor.close()  # ← 必须先关闭cursor
        conn.commit()
        
        if not row:
            return {"message": None}
        
        return {"message": {
            "id": row[0],
            "agent_id": row[1],
            "type": row[2],
            "content": row[3],
            "metadata": row[4],
            "timestamp": row[5],
        }}


@router.post("/messages/{message_id}/claim")
def claim_message(message_id: str):
    """
    Claim a message (sending -> sent) with CAS.
    
    Uses FIFO lock (sharded by message_id) to ensure fair ordering.
    """
    db = get_db()
    
    # Use message-specific lock (sharded for better concurrency)
    with db.get_connection("message", resource_id=message_id, timeout=10.0) as conn:
        cursor = conn.execute("""
            UPDATE chat_messages
            SET status = 'sent'
            WHERE id = ? AND status = 'sending'
        """, (message_id,))
        conn.commit()

    if cursor.rowcount > 0:
        return {"success": True, "message_id": message_id, "claimed": True}

    row = db.fetchone(
        "SELECT status FROM chat_messages WHERE id = ?",
        (message_id,),
    )
    current_status = row["status"] if row else "not_found"
    return {
        "success": current_status == "sent",
        "message_id": message_id,
        "claimed": False,
        "current_status": current_status,
    }


@router.get("/messages/has-new/{agent_id}")
def has_new_messages(agent_id: str):
    """Check if agent has new sent unread user messages."""

    db = get_db()
    row = db.fetchone("""
        SELECT COUNT(*) as cnt FROM chat_messages
        WHERE agent_id = ? AND type = 'USER_MESSAGE' AND status = 'sent' AND read = 0
    """, (agent_id,))
    has_new = row["cnt"] > 0 if row else False
    return {"has_new_messages": has_new}


@router.patch("/messages/mark-read")
def mark_messages_read(data: Dict[str, Any]):
    """Mark messages as read."""
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_db()
    placeholders = ",".join(["?"] * len(message_ids))
    # For batch updates, use global lock
    with db.get_connection("global", timeout=15.0) as conn:
        conn.execute(f"""
            UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
        """, tuple(message_ids))
        conn.commit()
    
    return {"status": "ok"}


@router.patch("/messages/mark-processed")
def mark_messages_processed(data: Dict[str, Any]):
    """Mark messages as read and broadcast status update to SSE.
    
    Note: 'processed' concept is merged into 'read'. Once read=1, message is considered processed.
    """
    from datetime import datetime
    import uuid as uuid_module
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_db()
    placeholders = ",".join(["?"] * len(message_ids))
    
    # Mark as read (read=1 means processed)
    # For batch updates, use global lock
    with db.get_connection("global", timeout=15.0) as conn:
        conn.execute(f"""
            UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
        """, tuple(message_ids))
        conn.commit()
    
    # Broadcast STATUS_UPDATE to SSE for each message
    # Import here to avoid circular import
    try:
        from main import _chat_subscribers
        for msg_id in message_ids:
            status_update = {
                "id": str(uuid_module.uuid4())[:8],
                "type": "STATUS_UPDATE",
                "message_id": msg_id,
                "status": "read",
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
    
    db = get_db()
    rows = db.fetchall(
        "SELECT id FROM agents WHERE setup_complete = 1"
    )
    
    return {"agent_ids": [row["id"] for row in rows]}


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


# MCP 生命周期由 Backend 组件 MCP Gateway 提供（api/internal_mcp.py）；Master 调 MCP Gateway /internal/mcp/*

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
    Used by MCP Gateway and other services.
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
            "enabled": m.available,
            "available": m.available,
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
    
    # 1. Get agent's model_id
    cursor = db.execute(
        "SELECT model_id FROM agents WHERE id = ?",
        (agent_id,)
    )
    row = cursor.fetchone()
    
    if not row:
        return {
            "success": False,
            "error": f"Agent '{agent_id}' not found",
            "agent_id": agent_id,
        }
    
    model_id = row["model_id"]
    
    # 2. If no model selected, use default from config
    if not model_id:
        default_row = db.fetchone("SELECT value FROM config WHERE key = 'default_model'")
        model_id = default_row[0].strip('"') if default_row else "gpt-4o"
    
    # 3. 从DB查询model和api_key配置
    cursor = db.execute("""
        SELECT 
            m.name as model_name,
            m.provider,
            k.provider as key_provider,
            k.api_key,
            k.api_base
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.name = ? AND m.available = 1
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
        "model": row[0],  # model_name
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
    1. Resolve agent_id from runtime_id
    2. Use agent's model_id if set, else default_model
    """
    
    db = get_db()
    runtime_ctx = get_runtime_context(runtime_id)
    agent_id = runtime_ctx.get("agent_id")
    
    return _build_llm_config_for_agent(db, agent_id)


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
    
    db = get_db()
    
    # Get first API key from api_keys table
    row = db.fetchone("SELECT api_key, api_base FROM api_keys LIMIT 1")
    if not row:
        return {"success": False, "error": "No API keys configured"}
    
    api_key = row["api_key"]
    base_url = row["api_base"] or "https://api.openai.com/v1"
    
    # Use compaction model from settings
    model = settings.compaction_model
    
    # Format messages for compaction
    messages_text = "\n".join([
        f"[{m.get('role', 'unknown')}]: {m.get('content', '')[:500]}"
        for m in messages_to_compact
    ])
    
    # Build LLM request
    llm_messages = [
        {"role": "system", "content": settings.compaction_prompt},
        {"role": "user", "content": f"请压缩以下对话历史：\n\n{messages_text}"}
    ]
    
    try:
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": llm_messages,
                    "temperature": 0.3,
                    "max_tokens": 2000,
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
    """Convert runtime to dictionary (v14 schema)."""
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


# ==================== MCP Gateway Proxy ====================
# All MCP management operations go through Gateway
# Services should NOT call MCP Gateway directly

import os
import httpx

MCP_GATEWAY_URL = os.environ.get("NOVAIC_MCP_GATEWAY_URL", "http://127.0.0.1:19998")


@router.get("/mcp/agent-shared/{agent_id}/exists")
def mcp_has_agent_shared(agent_id: str):
    """Check if agent has shared MCP server."""
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared/{agent_id}/exists")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/agent-shared")
def mcp_create_agent_shared(data: Dict[str, Any]):
    """Create agent shared MCP server.
    
    Gateway adds 'ports' from config before forwarding to MCP Gateway.
    """
    from gateway.config.agents import allocate_ports_for_agent
    
    # Get ports from config (Gateway is the only source of config)
    agent_index = data.get("agent_index", 0)
    ports = allocate_ports_for_agent(agent_index)
    
    # Add ports to request
    data["ports"] = ports.model_dump()
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/agent-shared/{agent_id}")
def mcp_delete_agent_shared(agent_id: str):
    """Delete agent shared MCP server."""
    with httpx.Client(timeout=10.0) as client:
        resp = client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared/{agent_id}")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/runtime")
def mcp_create_runtime(data: Dict[str, Any]):
    """Create runtime MCP server.
    
    Gateway adds 'ports' from config before forwarding to MCP Gateway.
    """
    from gateway.config.agents import allocate_ports_for_agent
    
    # Get ports from config (Gateway is the only source of config)
    agent_index = data.get("agent_index", 0)
    ports = allocate_ports_for_agent(agent_index)
    
    # Add ports to request
    data["ports"] = ports.model_dump()
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{MCP_GATEWAY_URL}/internal/mcp/runtime", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/runtime/{agent_id}/{runtime_id}")
def mcp_delete_runtime(agent_id: str, runtime_id: str):
    """Delete runtime MCP server."""
    with httpx.Client(timeout=10.0) as client:
        resp = client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/runtime/{agent_id}/{runtime_id}")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/aggregate")
def mcp_create_aggregate(data: Dict[str, Any]):
    """Create aggregate MCP server.
    
    Gateway adds 'ports' from config before forwarding to MCP Gateway.
    """
    from gateway.config.agents import allocate_ports_for_agent
    
    # Get ports from config (Gateway is the only source of config)
    agent_index = data.get("agent_index", 0)
    ports = allocate_ports_for_agent(agent_index)
    
    # Add ports to request
    data["ports"] = ports.model_dump()
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(f"{MCP_GATEWAY_URL}/internal/mcp/aggregate", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/aggregate/{agent_id}/{runtime_id}")
def mcp_delete_aggregate(agent_id: str, runtime_id: str):
    """Delete aggregate MCP server."""
    with httpx.Client(timeout=10.0) as client:
        resp = client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/aggregate/{agent_id}/{runtime_id}")
        resp.raise_for_status()
        return resp.json()


@router.get("/mcp/servers")
def mcp_list_servers():
    """List all active MCP servers."""
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{MCP_GATEWAY_URL}/internal/mcp/servers")
        resp.raise_for_status()
        return resp.json()


# ==================== Health Monitor Operations (v18) ====================

@router.get("/health/stuck-sending")
def get_stuck_sending_count(timeout_seconds: int = 30):
    """Get count of messages stuck in 'sending' state."""
    from gateway.db.repositories import MessageRepository
    
    db = get_db()
    repo = MessageRepository(db)
    count = repo.reset_stuck_sending(timeout_seconds)
    
    return {"count": count}


@router.get("/health/stuck-awaking")
def get_stuck_awaking_count(timeout_seconds: int = 60):
    """Get count of SubAgents stuck in 'awaking' state."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    count = repo.get_stuck_awaking_count(timeout_seconds)
    
    return {"count": count}


@router.post("/health/reset-stuck-awaking")
def reset_stuck_awaking(timeout_seconds: int = 60):
    """Reset SubAgents stuck in 'awaking' state to 'sleeping'."""
    from gateway.db.repositories import SubAgentRepository
    
    db = get_db()
    repo = SubAgentRepository(db)
    count = repo.reset_stuck_awaking(timeout_seconds)
    
    return {"reset_count": count}


# ==================== TaskManager API (for MCP Gateway) ====================

@router.post("/tasks/spawn")
def task_spawn(data: Dict[str, Any]):
    """Spawn a new task.
    
    Used by MCP Gateway to create background tasks.
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
    
    Used by MCP Gateway for _auto_truncate_result.
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
    
    Used by MCP Gateway for task_query tool.
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
    
    Used by MCP Gateway for task_list tool.
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
    
    Used by MCP Gateway for task_cancel tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.cancel(task_id, reason)


@router.get("/tasks/{task_id}/result")
def task_get_result(task_id: str, format: str = "summary"):
    """Get task result.
    
    Used by MCP Gateway for task_result tool.
    """
    from gateway.core.task_manager import get_task_manager
    
    task_manager = get_task_manager()
    if not task_manager:
        raise HTTPException(status_code=503, detail="TaskManager not available")
    
    return task_manager.get_result(task_id, format=format)


# ==================== SSH Key API (for MCP Gateway) ====================

@router.get("/vm/ssh/public-key")
def get_ssh_public_key():
    """Get default SSH public key.
    
    Used by MCP Gateway (qemudebug) to inject SSH key into VM.
    """
    from gateway.vm.ssh import get_ssh_key_manager
    
    manager = get_ssh_key_manager()
    public_key = manager.get_public_key()
    
    return {"public_key": public_key}


@router.get("/vm/ssh/private-key-path")
def get_ssh_private_key_path():
    """Get path to SSH private key file.
    
    Used by MCP Gateway (qemudebug) for SSH connections.
    Returns the path where Gateway has written the private key.
    """
    from gateway.vm.ssh import get_ssh_key_manager
    
    manager = get_ssh_key_manager()
    key_path = manager.get_private_key_path()
    
    return {"key_path": str(key_path)}


# ==================== Runtime List API (for MCP Gateway runtime tools) ====================
# NOTE: Legacy Memory API (/memory/{agent_id}/*) removed in v15.
# Use Runtime-First API: /rt/{runtime_id}/memory/* instead.

@router.get("/runtimes/list")
def list_active_runtimes_for_mcp():
    """List all active runtimes.
    
    Used by MCP Gateway for runtime_list tool.
    """
    
    db = get_db()
    
    # Query all active runtimes
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT runtime_id, agent_id, subagent_id, status, created_at
            FROM agent_runtimes 
            WHERE status IN ('active', 'resting')
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
    
    return {
        "runtimes": [
            {
                "runtime_id": row[0],
                "agent_id": row[1],
                "subagent_id": row[2],
                "type": "main" if row[2] and row[2].startswith("main-") else "subagent",
                "status": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]
    }


@router.post("/runtimes/{runtime_id}/history")
def get_runtime_history(runtime_id: str, data: Dict[str, Any]):
    """Get message history for a runtime.
    
    Used by MCP Gateway for runtime_history tool.
    Queries runtime's context which contains the conversation history.
    """
    from gateway.db.repositories import RuntimeRepository
    
    db = get_db()
    repo = RuntimeRepository(db)
    
    limit = data.get("limit", 50)
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
            if len(content) > 500:
                content = content[:500] + "..."
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
    
    Used by MCP Gateway for runtime_send tool.
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


# ==================== Web API (for MCP Gateway local tools) ====================
# NOTE: Legacy Chat API (/chat/*) removed in v15.
# Use Runtime-First API: /rt/{runtime_id}/chat/* instead.

@router.post("/web/search")
def web_search(data: Dict[str, Any]):
    """Search the web using Brave Search API.
    
    Used by MCP Gateway for web_search tool.
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
    
    Used by MCP Gateway for web_fetch tool.
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
# This simplifies MCP Gateway tools - they only need to know runtime_id.

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
    
    # Store message
    db = get_db()
    message_id = str(uuid.uuid4())[:11]
    timestamp = datetime.now().isoformat()
    
    with db.get_connection("message", resource_id=message_id, timeout=10.0) as conn:
        conn.execute("""
            INSERT INTO chat_messages (id, agent_id, type, content, timestamp, status)
            VALUES (?, ?, ?, ?, ?, 'sent')
        """, (message_id, agent_id, event_type, content, timestamp))
        conn.commit()
    
    # Broadcast via SSE
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
    
    return {"success": True, "event_type": event_type, "message_id": message_id}


@router.get("/rt/{runtime_id}/chat/history")
def rt_chat_history(runtime_id: str, limit: int = 20, summary_length: int = 50):
    """Get chat history. Agent ID resolved from runtime."""
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
    from task_queue import get_saga_orchestrator
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
    
    # Trigger RuntimeStart Saga
    orchestrator = get_saga_orchestrator()
    if orchestrator:
        trigger_id = f"spawn-{subagent.subagent_id}-{uuid.uuid4().hex[:8]}"
        orchestrator.create(
            saga_type="runtime_start",
            context={
                "agent_id": agent_id,
                "subagent_id": subagent.subagent_id,
                "trigger_id": trigger_id,
                "initial_context": initial_context,
            },
            idempotency_key=f"runtime-start-{trigger_id}",
        )
    
    return {"subagent_id": subagent.subagent_id}


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
    if subagent.status == "running" and subagent.timeout_at:
        try:
            timeout_at = datetime.fromisoformat(subagent.timeout_at)
            if datetime.utcnow() > timeout_at:
                subagent_repo.set_failed(target_subagent_id, agent_id, error="SubAgent timed out")
                subagent = subagent_repo.get_by_id(target_subagent_id, agent_id)
        except (ValueError, TypeError):
            pass
    
    completed = subagent.status in ("completed", "failed", "cancelled", "sleeping")
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
        if not response["result"] and rt.status == "completed" and rt.context:
            for msg in reversed(rt.context):
                if msg.get("role") == "assistant":
                    response["result"] = msg.get("content", "")
                    break
    
    return response


@router.post("/rt/{runtime_id}/subagent/{target_subagent_id}/cancel")
def rt_subagent_cancel(runtime_id: str, target_subagent_id: str):
    """Cancel a running SubAgent."""
    from gateway.db.repositories import SubAgentRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    db = get_db()
    subagent_repo = SubAgentRepository(db)
    
    subagent = subagent_repo.get_by_id(target_subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    if subagent.status != "running":
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
    
    subagent_repo.set_cancelled(target_subagent_id, agent_id)
    
    # Cancel active runtimes
    now = datetime.utcnow().isoformat()
    with db.get_connection("agent", resource_id=agent_id, timeout=10.0) as conn:
        cursor = conn.execute(
            "SELECT runtime_id FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
            (target_subagent_id, agent_id)
        )
        runtime_ids = [row[0] for row in cursor.fetchall()]
        for rid in runtime_ids:
            conn.execute("""
                UPDATE agent_runtimes SET status = 'cancelled', updated_at = ?
                WHERE runtime_id = ? AND status = 'active'
            """, (now, rid))
        conn.commit()
    
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
    agents = config_mgr.get_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.agent_id == agent_id:
            agent_index = i
            break
    
    ports = allocate_ports_for_agent(agent_index)
    ssh_port = ports.ssh
    
    try:
        import asyncssh
        ssh_manager = get_ssh_key_manager()
        key_path = ssh_manager.get_private_key_path()
        
        async with asyncssh.connect(
            host="127.0.0.1", port=ssh_port, username="novaic",
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
    agents = config_mgr.get_agents()
    agent_index = 0
    for i, agent in enumerate(agents):
        if agent.agent_id == agent_id:
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
