"""
Internal API for Master（Backend 组件）.

Master 通过本 API 与 Gateway（DB、任务、消息等）交互。
MCP 生命周期由 MCP Gateway（另一 Backend 组件）提供。仅内部使用。

v14: Added SubAgent API endpoints for SubAgent state management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

router = APIRouter(prefix="/internal", tags=["internal"])


# ==================== SubAgent Operations (v14) ====================

@router.get("/subagents/{agent_id}/main")
async def get_main_subagent(agent_id: str):
    """Get the main SubAgent for an agent (creates if not exists)."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    subagent = await repo.get_or_create_main_subagent(agent_id)
    
    return _subagent_to_dict(subagent)


@router.get("/subagents/{agent_id}/{subagent_id}")
async def get_subagent(agent_id: str, subagent_id: str):
    """Get a SubAgent by ID."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    subagent = await repo.get_by_id(subagent_id, agent_id)
    
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    return _subagent_to_dict(subagent)


@router.post("/subagents/{agent_id}/{subagent_id}/wake")
async def wake_subagent(agent_id: str, subagent_id: str, target_status: str = "awake"):
    """Atomically wake a SubAgent (sleeping -> target_status).
    
    Args:
        target_status: "awaking" (intermediate) or "awake" (final)
    
    Returns success=True if wake succeeded, False if already awake/awaking.
    """
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    success = await repo.try_wake(subagent_id, agent_id, target_status=target_status)
    
    return {"success": success}


@router.post("/subagents/{agent_id}/{subagent_id}/sleeping")
async def set_subagent_sleeping(agent_id: str, subagent_id: str):
    """Set SubAgent to sleeping status."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    await repo.set_sleeping(subagent_id, agent_id)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/awake")
async def set_subagent_awake(agent_id: str, subagent_id: str):
    """Set SubAgent to awake status (after runtime created successfully)."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    await repo.set_awake(subagent_id, agent_id)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/summarizing")
async def set_subagent_summarizing(agent_id: str, subagent_id: str):
    """Set SubAgent to summarizing status."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    await repo.set_summarizing(subagent_id, agent_id)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/completed")
async def set_subagent_completed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to completed status with result."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    
    result = data.get("result") if data else None
    await repo.set_completed(subagent_id, agent_id, result=result)
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/{subagent_id}/failed")
async def set_subagent_failed(agent_id: str, subagent_id: str, data: Dict[str, Any] = None):
    """Set SubAgent to failed status with error message."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    
    error = data.get("error") if data else None
    await repo.set_failed(subagent_id, agent_id, error=error)
    
    return {"status": "ok"}


@router.patch("/subagents/{agent_id}/{subagent_id}")
async def update_subagent(agent_id: str, subagent_id: str, data: Dict[str, Any]):
    """Update SubAgent fields."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    
    if "historical_summary" in data:
        await repo.update_historical_summary(subagent_id, agent_id, data["historical_summary"])
    
    if "wake_triggers" in data or "handoff_notes" in data:
        await repo.update_wake_triggers(
            subagent_id, 
            agent_id,
            data.get("wake_triggers", [{"type": "user_response"}]),
            data.get("handoff_notes")
        )
    
    return {"status": "ok"}


@router.post("/subagents/{agent_id}/spawn")
async def spawn_subagent(agent_id: str, data: Dict[str, Any]):
    """
    Spawn a new SubAgent and its Runtime (async mode).
    
    Creates a sub SubAgent, a Runtime, and the initial runtime_launcher task.
    Returns the subagent_id immediately. Use /status to poll for completion.
    
    Args (JSON body):
        task: Task description for the SubAgent
        share_context: If True, copy context from parent runtime
        parent_subagent_id: Parent SubAgent (defaults to main)
        timeout_minutes: Timeout in minutes (default 30)
    
    Returns:
        subagent_id: Use this to query status
        runtime_id: Runtime ID
    """
    from db.database import get_database
    from db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime, timedelta
    import uuid
    
    db = get_database()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    # Get parent subagent_id (defaults to main)
    parent_subagent_id = data.get("parent_subagent_id")
    if not parent_subagent_id:
        main_subagent = await subagent_repo.get_or_create_main_subagent(agent_id)
        parent_subagent_id = main_subagent.subagent_id
    
    # Parse parameters
    task_description = data.get("task", "")
    share_context = data.get("share_context", False)
    timeout_minutes = data.get("timeout_minutes", 30)
    
    # Calculate timeout
    now = datetime.utcnow()
    timeout_at = (now + timedelta(minutes=timeout_minutes)).isoformat()
    
    # Create sub SubAgent with async fields
    subagent = await subagent_repo.create_sub_subagent(
        agent_id, 
        parent_subagent_id,
        task=task_description,
        timeout_at=timeout_at,
    )
    
    # Prepare initial context
    initial_context = []
    
    # If sharing context, copy from parent's active runtime
    if share_context:
        parent_runtime = await runtime_repo.get_active_runtime(parent_subagent_id, agent_id)
        if parent_runtime and parent_runtime.context:
            # Copy context but mark it as inherited
            initial_context = parent_runtime.context.copy()
    
    # Add task as user message
    initial_context.append({
        "role": "user",
        "content": f"[SubAgent Task]\n{task_description}"
    })
    
    # Create Runtime
    runtime = await runtime_repo.create_runtime(
        subagent.subagent_id, 
        agent_id,
        initial_context
    )
    
    # Set SubAgent to running status (not just awake)
    await subagent_repo.set_running(subagent.subagent_id, agent_id)
    
    # Create runtime_launcher task via pipeline_tasks
    stage_id = f"stage-{uuid.uuid4().hex[:8]}"
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    now_str = now.isoformat()
    
    async with db.get_connection() as conn:
        await conn.execute("""
            INSERT INTO pipeline_tasks (
                id, task_type, task_subtype, runtime_id, stage_id, agent_id,
                status, args, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            "launcher",
            "runtime_launcher",
            runtime.runtime_id,
            stage_id,
            agent_id,
            "pending",
            "{}",
            now_str,
            now_str,
        ))
        await conn.commit()
    
    return {
        "subagent_id": subagent.subagent_id,
        "runtime_id": runtime.runtime_id,
    }


@router.get("/subagents/{agent_id}/{subagent_id}/status")
async def get_subagent_status(agent_id: str, subagent_id: str):
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
    from db.database import get_database
    from db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime
    
    db = get_database()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = await subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    # Check timeout
    if subagent.status == "running" and subagent.timeout_at:
        try:
            timeout_at = datetime.fromisoformat(subagent.timeout_at)
            if datetime.utcnow() > timeout_at:
                # Mark as failed due to timeout
                await subagent_repo.set_failed(
                    subagent_id, agent_id, 
                    error="SubAgent timed out"
                )
                subagent = await subagent_repo.get_by_id(subagent_id, agent_id)
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
    runtimes = await runtime_repo.get_latest_runtimes(subagent_id, agent_id, limit=1)
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
async def cancel_subagent(agent_id: str, subagent_id: str):
    """
    Cancel a running SubAgent.
    
    Sets status to 'cancelled' and cancels all pending tasks.
    """
    from db.database import get_database
    from db.repositories import SubAgentRepository, RuntimeRepository
    from datetime import datetime
    
    db = get_database()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    subagent = await subagent_repo.get_by_id(subagent_id, agent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail="SubAgent not found")
    
    # Only cancel if running
    if subagent.status != "running":
        return {"success": False, "reason": f"SubAgent is not running (status: {subagent.status})"}
    
    # Set SubAgent to cancelled
    await subagent_repo.set_cancelled(subagent_id, agent_id)
    
    # Cancel all pending pipeline_tasks for this SubAgent's runtimes
    now = datetime.utcnow().isoformat()
    async with db.get_connection() as conn:
        # Get runtime IDs for this SubAgent
        cursor = await conn.execute(
            "SELECT runtime_id FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )
        runtime_ids = [row[0] for row in await cursor.fetchall()]
        
        # Cancel pending tasks
        for runtime_id in runtime_ids:
            await conn.execute("""
                UPDATE pipeline_tasks 
                SET status = 'cancelled', updated_at = ?
                WHERE runtime_id = ? AND status IN ('pending', 'claimed')
            """, (now, runtime_id))
            
            # Also update runtime status
            await conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'cancelled', updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
        
        await conn.commit()
    
    return {"success": True}


@router.delete("/subagents/{agent_id}/{subagent_id}")
async def delete_subagent(agent_id: str, subagent_id: str):
    """Delete a SubAgent and its runtimes."""
    from db.database import get_database
    from db.repositories import SubAgentRepository, RuntimeRepository
    
    db = get_database()
    subagent_repo = SubAgentRepository(db)
    runtime_repo = RuntimeRepository(db)
    
    # Delete runtimes for this subagent
    async with db.get_connection() as conn:
        await conn.execute(
            "DELETE FROM runtimes WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id)
        )
        await conn.commit()
    
    # Delete subagent
    await subagent_repo.delete(subagent_id, agent_id)
    
    return {"status": "ok"}


# ==================== Runtime Operations ====================

@router.get("/runtimes/active")
async def get_active_runtimes():
    """Get all active runtimes."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtimes = await repo.get_all_active_runtimes()
    
    return {
        "runtimes": [_runtime_to_dict(r) for r in runtimes]
    }


@router.get("/runtimes/{runtime_id}")
async def get_runtime(runtime_id: str):
    """Get a single runtime by ID."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.get_by_id(runtime_id)
    
    if not runtime:
        raise HTTPException(status_code=404, detail="Runtime not found")
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes")
async def create_runtime(data: Dict[str, Any]):
    """Create a new Runtime for a SubAgent (v14)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    agent_id = data.get("agent_id")
    subagent_id = data.get("subagent_id", "main")
    initial_context = data.get("initial_context", [])
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.create_runtime(subagent_id, agent_id, initial_context)
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes/main")
async def create_main_runtime(data: Dict[str, Any]):
    """Create a new Main Runtime (deprecated, use POST /runtimes)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository, SubAgentRepository
    
    agent_id = data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    db = get_database()
    # v14: Get actual main subagent_id (now has format main-{agent_id[:8]})
    subagent_repo = SubAgentRepository(db)
    main_subagent = await subagent_repo.get_or_create_main_subagent(agent_id)
    
    repo = RuntimeRepository(db)
    runtime = await repo.create_runtime(main_subagent.subagent_id, agent_id)
    
    return _runtime_to_dict(runtime)


@router.patch("/runtimes/{runtime_id}")
async def update_runtime(runtime_id: str, data: Dict[str, Any]):
    """Update runtime fields."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    
    # Handle specific updates
    if "phase" in data and "pending_actions" in data:
        await repo.set_pending_actions(
            runtime_id, 
            data["pending_actions"], 
            data["phase"]
        )
    elif "phase" in data:
        await repo.set_phase(runtime_id, data["phase"])
    
    if "context" in data:
        await repo.update_context(runtime_id, data["context"])
    
    if "mcp_url" in data:
        await repo.set_mcp_url(runtime_id, data["mcp_url"])
    
    if "status" in data:
        if data["status"] == "completed":
            await repo.mark_completed(runtime_id)
        elif data["status"] == "failed":
            await repo.mark_failed(runtime_id, data.get("error", "Unknown error"))
        elif data["status"] == "resting":
            await repo.set_resting(runtime_id)
        elif data["status"] == "active":
            await repo.set_status(runtime_id, "active")
    
    if "summary" in data:
        await repo.set_summary(runtime_id, data["summary"])
    
    if "is_merged" in data and data["is_merged"]:
        await repo.mark_merged(runtime_id)
    
    # Handle round updates
    if "current_round_num" in data and "current_round_id" in data:
        # Directly update round fields
        now = datetime.utcnow().isoformat()
        async with db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET current_round_num = ?, current_round_id = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (data["current_round_num"], data["current_round_id"], now, runtime_id))
            await conn.commit()
    
    return {"status": "ok"}


@router.post("/runtimes/{runtime_id}/rest")
async def rest_runtime(runtime_id: str, data: Dict[str, Any]):
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
    from db.database import get_database
    from db.repositories import RuntimeRepository, SubAgentRepository
    
    db = get_database()
    runtime_repo = RuntimeRepository(db)
    subagent_repo = SubAgentRepository(db)
    
    # Check if runtime exists
    runtime = await runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    # Set runtime status to 'resting'
    await runtime_repo.set_resting(runtime_id)
    
    # Update SubAgent's wake triggers (v14)
    reason = data.get("reason", "No reason provided")
    wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
    handoff_notes = data.get("handoff_notes")
    
    await subagent_repo.update_wake_triggers(
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
async def wake_runtime(runtime_id: str):
    """Wake a sleeping runtime (deprecated in v14, use SubAgent wake).
    
    Returns success=True only if the runtime was actually woken up.
    Returns success=False if runtime was already active or not found.
    """
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    success = await repo.wake_main_runtime(runtime_id)
    
    return {"status": "ok" if success else "skipped", "success": success}


@router.post("/runtimes/{runtime_id}/advance")
async def advance_runtime_round(runtime_id: str, data: Dict[str, Any] = None):
    """Advance runtime to next round (with optional CAS).
    
    Args:
        data: Optional dict with 'expected_round_num' for CAS operation
    """
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    
    expected_round_num = None
    if data:
        expected_round_num = data.get("expected_round_num")
    
    new_round_id = await repo.advance_round(runtime_id, expected_round_num)
    
    if new_round_id is None:
        return {"round_id": None, "success": False, "reason": "CAS conflict or runtime not found"}
    
    return {"round_id": new_round_id, "success": True}


@router.post("/runtimes/{runtime_id}/claim-phase")
async def try_claim_phase(runtime_id: str, data: Dict[str, Any]):
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
    from db.database import get_database
    from datetime import datetime
    
    expected_phase = data.get("expected_phase")
    new_phase = data.get("new_phase")
    
    if not expected_phase or not new_phase:
        raise HTTPException(status_code=400, detail="expected_phase and new_phase required")
    
    db = get_database()
    now = datetime.utcnow().isoformat()
    
    # Atomic CAS: only update if phase matches expected (v14: use runtime_id)
    cursor = await db.execute("""
        UPDATE agent_runtimes 
        SET phase = ?, updated_at = ?
        WHERE runtime_id = ? AND phase = ?
    """, (new_phase, now, runtime_id, expected_phase))
    await db.commit()
    
    return {"success": cursor.rowcount > 0}


@router.delete("/runtimes/{runtime_id}")
async def delete_runtime(runtime_id: str):
    """Delete a runtime."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    await repo.delete(runtime_id)
    
    return {"status": "ok"}


@router.get("/runtimes/main/{agent_id}")
async def get_main_runtime(agent_id: str):
    """Get active main runtime for an agent (v14: from main SubAgent)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.get_active_runtime("main", agent_id)
    
    if not runtime:
        return {"runtime": None}
    
    return {"runtime": _runtime_to_dict(runtime)}


@router.get("/runtimes/subagent/{agent_id}/{subagent_id}")
async def get_subagent_runtime(agent_id: str, subagent_id: str):
    """Get active runtime for a SubAgent (v14)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.get_active_runtime(subagent_id, agent_id)
    
    if not runtime:
        return {"runtime": None}
    
    return {"runtime": _runtime_to_dict(runtime)}


@router.get("/runtimes/latest/{agent_id}/{subagent_id}")
async def get_latest_runtimes(agent_id: str, subagent_id: str, limit: int = 30):
    """Get latest completed runtimes for a SubAgent (for context preparation, v14)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtimes = await repo.get_latest_runtimes(subagent_id, agent_id, limit)
    
    return {"runtimes": [_runtime_to_dict(r) for r in runtimes]}


@router.get("/agents/{agent_id}/subagents/{subagent_id}/has-active-runtime")
async def has_active_runtime(agent_id: str, subagent_id: str):
    """Check if SubAgent has an active runtime (active/resting status)."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    has_active = await repo.has_active_runtime(subagent_id, agent_id)
    
    return {"has_active_runtime": has_active}


# ==================== Message Operations ====================

@router.get("/messages/unread/{agent_id}")
async def get_unread_messages(agent_id: str):
    """Get unread messages for an agent (for Scheduler to include in context).
    
    Uses read=0 to find messages that haven't been processed yet.
    """
    from db.database import get_database
    
    db = get_database()
    rows = await db.fetchall("""
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


@router.get("/messages/unread-count/{agent_id}")
async def get_unread_count(agent_id: str):
    """Get count of unread messages (for Monitor to detect new messages).
    
    Uses read=0 to find messages that haven't been processed yet.
    """
    from db.database import get_database
    
    db = get_database()
    row = await db.fetchone("""
        SELECT COUNT(*) as count FROM chat_messages 
        WHERE agent_id = ? AND read = 0 AND type = 'USER_MESSAGE'
    """, (agent_id,))
    
    return {"count": row["count"] if row else 0}


@router.get("/messages/unread-grouped")
async def get_unread_messages_grouped(agent_id: Optional[str] = None):
    """Get unread messages grouped by agent_id (v14 for Monitor).
    
    Returns all agents with unread USER_MESSAGE messages.
    Uses read=0 to find messages that haven't been processed yet.
    """
    from db.database import get_database
    
    db = get_database()
    
    # Get all unread messages with their agent_id
    rows = await db.fetchall("""
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


@router.post("/messages/claim-sending")
async def claim_sending_message():
    """CAS claim a sending message (sending → sent).
    
    Used by Monitor service to consume the message queue.
    
    Returns:
        {"message": {...}} if claimed, {"message": null} if queue is empty
    """
    from db.database import get_database
    from db.repositories import MessageRepository
    
    db = get_database()
    repo = MessageRepository(db)
    message = await repo.claim_sending()
    
    return {"message": message}


@router.patch("/messages/mark-read")
async def mark_messages_read(data: Dict[str, Any]):
    """Mark messages as read."""
    from db.database import get_database
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_database()
    placeholders = ",".join(["?"] * len(message_ids))
    async with db.get_connection() as conn:
        await conn.execute(f"""
            UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
        """, tuple(message_ids))
        await conn.commit()
    
    return {"status": "ok"}


@router.patch("/messages/mark-processed")
async def mark_messages_processed(data: Dict[str, Any]):
    """Mark messages as read and broadcast status update to SSE.
    
    Note: 'processed' concept is merged into 'read'. Once read=1, message is considered processed.
    """
    from db.database import get_database
    from datetime import datetime
    import uuid as uuid_module
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_database()
    placeholders = ",".join(["?"] * len(message_ids))
    
    # Mark as read (read=1 means processed)
    async with db.get_connection() as conn:
        await conn.execute(f"""
            UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
        """, tuple(message_ids))
        await conn.commit()
    
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
async def create_message(data: Dict[str, Any]):
    """Create a chat message (for agent replies).
    
    Agent replies use status='sent' directly (no Monitor processing needed).
    """
    from db.database import get_database
    from db.repositories.message import MessageRepository
    
    db = get_database()
    repo = MessageRepository(db)
    
    msg = await repo.add_message(
        agent_id=data["agent_id"],
        type=data["type"],
        content=data["content"],
        metadata=data.get("metadata"),
        status="sent",  # v18: Agent replies skip Monitor queue
    )
    
    return msg


# ==================== Agent Operations ====================

@router.get("/agents/setup-complete")
async def get_setup_complete_agents():
    """Get all agents with setup complete."""
    from db.database import get_database
    
    db = get_database()
    rows = await db.fetchall(
        "SELECT id FROM agents WHERE setup_complete = 1"
    )
    
    return {"agent_ids": [row["id"] for row in rows]}


@router.post("/agents/{agent_id}/awake")
async def set_agent_awake(agent_id: str):
    """Set agent state to awake."""
    from db.database import get_database
    from db.repositories import AgentStateRepository
    
    db = get_database()
    repo = AgentStateRepository(db)
    await repo.set_awake(agent_id)
    
    return {"status": "ok"}


@router.post("/agents/{agent_id}/sleep")
async def set_agent_sleep(agent_id: str, data: Dict[str, Any] = None):
    """Set agent state to sleep."""
    from db.database import get_database
    from db.repositories import AgentStateRepository
    
    db = get_database()
    repo = AgentStateRepository(db)
    reason = (data or {}).get("reason", "Task completed")
    await repo.set_sleep(agent_id, reason=reason)
    
    return {"status": "ok"}


# MCP 生命周期由 Backend 组件 MCP Gateway 提供（api/internal_mcp.py）；Master 调 MCP Gateway /internal/mcp/*

# ==================== SSE Broadcast ====================

@router.post("/broadcast/new-task")
async def broadcast_new_task(data: Dict[str, Any]):
    """Broadcast new task event to workers."""
    from sse.broadcaster import get_worker_broadcaster
    
    broadcaster = get_worker_broadcaster()
    if not broadcaster:
        return {"status": "ok", "broadcast": False}
    
    task_id = data.get("task_id")
    task_type = data.get("task_type")
    agent_id = data.get("agent_id")
    
    await broadcaster.broadcast_new_task(
        task_id=task_id,
        agent_id=agent_id,
        task_type=task_type,
    )
    
    return {"status": "ok", "broadcast": True}


@router.post("/broadcast/chat-message")
async def broadcast_chat_message(data: Dict[str, Any]):
    """Broadcast chat message to UI."""
    try:
        from main import broadcast_chat_message as _broadcast
        await _broadcast(data.get("message", {}), agent_id=data.get("agent_id"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==================== Config ====================

@router.get("/config/agent/{agent_id}")
async def get_agent_config(agent_id: str):
    """Get agent configuration."""
    from config.agents import get_agent_config_manager
    
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


# ==================== LLM Operations ====================

@router.post("/llm/compact-context")
async def compact_context_with_llm(data: Dict[str, Any]):
    """
    Compact context using LLM.
    
    This endpoint calls an LLM to generate a summary of older messages.
    Used by Master's Scheduler for context compaction.
    """
    import httpx
    from config.settings import get_context_compaction_settings
    
    messages_to_compact = data.get("messages", [])
    agent_id = data.get("agent_id")
    
    if not messages_to_compact:
        return {"success": True, "summary": ""}
    
    # Get compaction settings
    settings = get_context_compaction_settings()
    
    # Get API configuration from database
    from db.database import get_database
    
    db = get_database()
    
    # Get first API key from api_keys table
    row = await db.fetchone("SELECT api_key, api_base FROM api_keys LIMIT 1")
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
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
            response = await client.post(
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


# ==================== Pipeline Tasks API (Three-Task Architecture) ====================

@router.post("/pipeline/tasks/claim")
async def claim_pipeline_task(data: Dict[str, Any]):
    """
    Atomically claim a pending pipeline task.
    
    Body:
        task_types: List of task types to claim (launcher, collector, async)
        task_subtypes: Optional list of subtypes (e.g., think_launcher, tool_call)
        worker_id: Worker ID claiming the task
        collector_ready_only: If True and claiming collector, only claim when all tasks done
    
    Returns:
        task: The claimed task dict, or null if no task available
    """
    from db.database import get_database
    
    db = get_database()
    
    task_types = data.get("task_types", [])
    task_subtypes = data.get("task_subtypes")
    worker_id = data.get("worker_id", "unknown")
    collector_ready_only = data.get("collector_ready_only", False)
    
    if not task_types:
        raise HTTPException(status_code=400, detail="task_types required")
    
    # Build type filter
    type_placeholders = ",".join([f"'{t}'" for t in task_types])
    type_filter = f"task_type IN ({type_placeholders})"
    
    # Build subtype filter
    subtype_filter = ""
    if task_subtypes:
        subtype_placeholders = ",".join([f"'{s}'" for s in task_subtypes])
        subtype_filter = f"AND task_subtype IN ({subtype_placeholders})"
    
    # For collector, optionally check if all tasks done
    collector_filter = ""
    if collector_ready_only and "collector" in task_types:
        collector_filter = "AND (task_type != 'collector' OR completed_tasks >= expected_tasks)"
    
    sql = f"""
        UPDATE pipeline_tasks 
        SET status = 'claimed', 
            claimed_by = :worker_id,
            claimed_at = datetime('now'),
            heartbeat_at = datetime('now'),
            updated_at = datetime('now')
        WHERE id = (
            SELECT id FROM pipeline_tasks 
            WHERE status = 'pending' 
              AND {type_filter}
              {subtype_filter}
              {collector_filter}
            ORDER BY created_at
            LIMIT 1
        )
        RETURNING *
    """
    
    cursor = await db.execute(sql, {"worker_id": worker_id})
    row = await cursor.fetchone()
    await db.commit()
    
    if row:
        return {"task": _pipeline_task_to_dict(dict(row))}
    return {"task": None}


@router.post("/pipeline/tasks")
async def create_pipeline_task(data: Dict[str, Any]):
    """
    Create a new pipeline task.
    
    Uses idempotency_key to prevent duplicates.
    
    Returns:
        task_id: Created task ID, or null if idempotency conflict
        exists: True if task already exists with same idempotency_key
    """
    from db.database import get_database
    import uuid
    
    db = get_database()
    
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    task_type = data.get("task_type")
    task_subtype = data.get("task_subtype")
    runtime_id = data.get("runtime_id")
    stage_id = data.get("stage_id")
    agent_id = data.get("agent_id")
    args = data.get("args", {})
    idempotency_key = data.get("idempotency_key")
    expected_tasks = data.get("expected_tasks", 0)
    
    if not all([task_type, task_subtype, runtime_id, stage_id, agent_id]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    args_json = json.dumps(args) if isinstance(args, dict) else args
    
    try:
        cursor = await db.execute("""
            INSERT INTO pipeline_tasks (
                id, task_type, task_subtype,
                runtime_id, stage_id, agent_id,
                args, idempotency_key, expected_tasks,
                status, created_at
            ) VALUES (
                :id, :task_type, :task_subtype,
                :runtime_id, :stage_id, :agent_id,
                :args, :idempotency_key, :expected_tasks,
                'pending', datetime('now')
            )
        """, {
            "id": task_id,
            "task_type": task_type,
            "task_subtype": task_subtype,
            "runtime_id": runtime_id,
            "stage_id": stage_id,
            "agent_id": agent_id,
            "args": args_json,
            "idempotency_key": idempotency_key,
            "expected_tasks": expected_tasks,
        })
        await db.commit()
        return {"task_id": task_id, "exists": False}
    except Exception as e:
        # Check if it's a unique constraint violation
        if "UNIQUE constraint" in str(e) and idempotency_key:
            # Return existing task ID instead of None
            cursor = await db.execute("""
                SELECT id FROM pipeline_tasks WHERE idempotency_key = :key
            """, {"key": idempotency_key})
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(
                    status_code=500,
                    detail=f"UNIQUE constraint violated but task not found for key: {idempotency_key}"
                )
            return {"task_id": row["id"], "exists": True}
        raise


@router.patch("/pipeline/tasks/{task_id}/done")
async def mark_pipeline_task_done(task_id: str, data: Dict[str, Any]):
    """Mark a pipeline task as done with result."""
    from db.database import get_database
    
    db = get_database()
    result = data.get("result")
    result_json = json.dumps(result) if result else None
    
    await db.execute("""
        UPDATE pipeline_tasks 
        SET status = 'done', 
            result = :result,
            updated_at = datetime('now')
        WHERE id = :task_id
    """, {"task_id": task_id, "result": result_json})
    await db.commit()
    
    return {"status": "ok"}


@router.patch("/pipeline/tasks/{task_id}/failed")
async def mark_pipeline_task_failed(task_id: str, data: Dict[str, Any]):
    """Mark a pipeline task as failed with error."""
    from db.database import get_database
    
    db = get_database()
    error = data.get("error", "Unknown error")
    
    await db.execute("""
        UPDATE pipeline_tasks 
        SET status = 'failed', 
            error = :error,
            updated_at = datetime('now')
        WHERE id = :task_id
    """, {"task_id": task_id, "error": error})
    await db.commit()
    
    return {"status": "ok"}


@router.patch("/pipeline/tasks/{task_id}/heartbeat")
async def update_pipeline_task_heartbeat(task_id: str):
    """Update heartbeat timestamp for a claimed task."""
    from db.database import get_database
    
    db = get_database()
    
    await db.execute("""
        UPDATE pipeline_tasks 
        SET heartbeat_at = datetime('now')
        WHERE id = :task_id AND status = 'claimed'
    """, {"task_id": task_id})
    await db.commit()
    
    return {"status": "ok"}


@router.patch("/pipeline/tasks/{task_id}/release")
async def release_pipeline_task(task_id: str):
    """
    Release a claimed task back to pending for retry.
    
    Used when a launcher fails but should be retried (e.g., MCP creation failed).
    Clears claimed_by/claimed_at so the task can be re-claimed.
    """
    from db.database import get_database
    
    db = get_database()
    
    await db.execute("""
        UPDATE pipeline_tasks 
        SET status = 'pending', 
            claimed_by = NULL,
            claimed_at = NULL,
            heartbeat_at = NULL,
            updated_at = datetime('now')
        WHERE id = :task_id AND status = 'claimed'
    """, {"task_id": task_id})
    await db.commit()
    
    return {"status": "ok"}


@router.post("/pipeline/tasks/recover-stale")
async def recover_stale_pipeline_tasks(data: Dict[str, Any]):
    """
    Recover stale tasks (heartbeat timeout).
    
    Resets claimed tasks back to pending if heartbeat is too old.
    """
    from db.database import get_database
    
    db = get_database()
    
    task_type = data.get("task_type")
    timeout_seconds = data.get("timeout_seconds", 60)
    
    type_filter = ""
    if task_type:
        type_filter = f"AND task_type = '{task_type}'"
    
    cursor = await db.execute(f"""
        UPDATE pipeline_tasks 
        SET status = 'pending', 
            claimed_by = NULL,
            claimed_at = NULL,
            heartbeat_at = NULL,
            updated_at = datetime('now')
        WHERE status = 'claimed'
          {type_filter}
          AND heartbeat_at < datetime('now', '-{timeout_seconds} seconds')
        RETURNING id
    """)
    
    rows = await cursor.fetchall()
    await db.commit()
    
    recovered_count = len(rows) if rows else 0
    return {"recovered_count": recovered_count}


@router.post("/pipeline/stages/{stage_id}/increment-completed")
async def increment_stage_completed(stage_id: str):
    """
    Atomically increment completed_tasks count for a stage's collector.
    
    Returns whether all tasks are now complete.
    """
    from db.database import get_database
    
    db = get_database()
    
    cursor = await db.execute("""
        UPDATE pipeline_tasks 
        SET completed_tasks = completed_tasks + 1,
            updated_at = datetime('now')
        WHERE stage_id = :stage_id 
          AND task_type = 'collector'
          AND status = 'pending'
        RETURNING id, expected_tasks, completed_tasks
    """, {"stage_id": stage_id})
    
    row = await cursor.fetchone()
    await db.commit()
    
    if row:
        row_dict = dict(row)
        expected = row_dict.get("expected_tasks", 0)
        completed = row_dict.get("completed_tasks", 0)
        return {
            "expected": expected,
            "completed": completed,
            "all_done": completed >= expected,
        }
    
    return {"expected": 0, "completed": 0, "all_done": False}


@router.get("/pipeline/tasks/by-stage/{stage_id}")
async def get_tasks_by_stage(stage_id: str):
    """Get all tasks for a stage."""
    from db.database import get_database
    
    db = get_database()
    
    cursor = await db.execute("""
        SELECT * FROM pipeline_tasks 
        WHERE stage_id = :stage_id
        ORDER BY created_at
    """, {"stage_id": stage_id})
    
    rows = await cursor.fetchall()
    tasks = [_pipeline_task_to_dict(dict(row)) for row in rows] if rows else []
    
    return {"tasks": tasks}


@router.get("/pipeline/tasks/{task_id}")
async def get_pipeline_task(task_id: str):
    """Get a single pipeline task by ID."""
    from db.database import get_database
    
    db = get_database()
    
    cursor = await db.execute("""
        SELECT * FROM pipeline_tasks WHERE id = :task_id
    """, {"task_id": task_id})
    
    row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return _pipeline_task_to_dict(dict(row))


def _pipeline_task_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert pipeline_tasks row to dictionary."""
    args = row.get("args")
    result = row.get("result")
    return {
        "id": row["id"],
        "task_type": row["task_type"],
        "task_subtype": row["task_subtype"],
        "runtime_id": row["runtime_id"],
        "stage_id": row["stage_id"],
        "agent_id": row["agent_id"],
        "args": json.loads(args) if args and isinstance(args, str) else args or {},
        "result": json.loads(result) if result and isinstance(result, str) else result,
        "error": row.get("error"),
        "status": row["status"],
        "claimed_by": row.get("claimed_by"),
        "claimed_at": row.get("claimed_at"),
        "heartbeat_at": row.get("heartbeat_at"),
        "idempotency_key": row.get("idempotency_key"),
        "expected_tasks": row.get("expected_tasks", 0),
        "completed_tasks": row.get("completed_tasks", 0),
        "created_at": row["created_at"],
        "updated_at": row.get("updated_at"),
    }


# ==================== MCP Gateway Proxy ====================
# All MCP management operations go through Gateway
# Services should NOT call MCP Gateway directly

import os
import httpx

MCP_GATEWAY_URL = os.environ.get("NOVAIC_MCP_GATEWAY_URL", "http://127.0.0.1:19998")


@router.get("/mcp/agent-shared/{agent_id}/exists")
async def mcp_has_agent_shared(agent_id: str):
    """Check if agent has shared MCP server."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared/{agent_id}/exists")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/agent-shared")
async def mcp_create_agent_shared(data: Dict[str, Any]):
    """Create agent shared MCP server."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/agent-shared/{agent_id}")
async def mcp_delete_agent_shared(agent_id: str):
    """Delete agent shared MCP server."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/agent-shared/{agent_id}")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/runtime")
async def mcp_create_runtime(data: Dict[str, Any]):
    """Create runtime MCP server."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{MCP_GATEWAY_URL}/internal/mcp/runtime", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/runtime/{agent_id}/{runtime_id}")
async def mcp_delete_runtime(agent_id: str, runtime_id: str):
    """Delete runtime MCP server."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/runtime/{agent_id}/{runtime_id}")
        resp.raise_for_status()
        return resp.json()


@router.post("/mcp/aggregate")
async def mcp_create_aggregate(data: Dict[str, Any]):
    """Create aggregate MCP server."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{MCP_GATEWAY_URL}/internal/mcp/aggregate", json=data)
        resp.raise_for_status()
        return resp.json()


@router.delete("/mcp/aggregate/{agent_id}/{runtime_id}")
async def mcp_delete_aggregate(agent_id: str, runtime_id: str):
    """Delete aggregate MCP server."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.delete(f"{MCP_GATEWAY_URL}/internal/mcp/aggregate/{agent_id}/{runtime_id}")
        resp.raise_for_status()
        return resp.json()


@router.get("/mcp/servers")
async def mcp_list_servers():
    """List all active MCP servers."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{MCP_GATEWAY_URL}/internal/mcp/servers")
        resp.raise_for_status()
        return resp.json()


# ==================== Health Monitor Operations (v18) ====================

@router.get("/health/stuck-sending")
async def get_stuck_sending_count(timeout_seconds: int = 30):
    """Get count of messages stuck in 'sending' state."""
    from db.database import get_database
    from db.repositories import MessageRepository
    
    db = get_database()
    repo = MessageRepository(db)
    count = await repo.reset_stuck_sending(timeout_seconds)
    
    return {"count": count}


@router.get("/health/stuck-awaking")
async def get_stuck_awaking_count(timeout_seconds: int = 60):
    """Get count of SubAgents stuck in 'awaking' state."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    count = await repo.get_stuck_awaking_count(timeout_seconds)
    
    return {"count": count}


@router.post("/health/reset-stuck-awaking")
async def reset_stuck_awaking(timeout_seconds: int = 60):
    """Reset SubAgents stuck in 'awaking' state to 'sleeping'."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    count = await repo.reset_stuck_awaking(timeout_seconds)
    
    return {"reset_count": count}
