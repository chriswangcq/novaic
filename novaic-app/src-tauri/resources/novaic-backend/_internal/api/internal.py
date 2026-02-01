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
async def wake_subagent(agent_id: str, subagent_id: str):
    """Atomically wake a SubAgent (sleeping -> awake).
    
    Returns success=True if wake succeeded, False if already awake.
    """
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    success = await repo.try_wake(subagent_id, agent_id)
    
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


@router.post("/subagents/{agent_id}/{subagent_id}/summarizing")
async def set_subagent_summarizing(agent_id: str, subagent_id: str):
    """Set SubAgent to summarizing status."""
    from db.database import get_database
    from db.repositories import SubAgentRepository
    
    db = get_database()
    repo = SubAgentRepository(db)
    await repo.set_summarizing(subagent_id, agent_id)
    
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


# ==================== Task Operations ====================

@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    subagent_id: Optional[str] = None,
    ids: Optional[str] = None,  # Comma-separated IDs
):
    """Query tasks."""
    from db.database import get_database
    
    db = get_database()
    
    if ids:
        # Query by IDs
        id_list = ids.split(",")
        placeholders = ",".join(["?"] * len(id_list))
        rows = await db.fetchall(f"""
            SELECT id, agent_id, subagent_id, round_id, mcpcall_id,
                   type, action, args, status, result, error, created_at
            FROM action_tasks 
            WHERE id IN ({placeholders})
        """, id_list)
    elif status and subagent_id:
        rows = await db.fetchall("""
            SELECT id, agent_id, subagent_id, round_id, mcpcall_id,
                   type, action, args, status, result, error, created_at
            FROM action_tasks 
            WHERE status = ? AND subagent_id = ?
            ORDER BY created_at DESC
        """, (status, subagent_id))
    elif status:
        rows = await db.fetchall("""
            SELECT id, agent_id, subagent_id, round_id, mcpcall_id,
                   type, action, args, status, result, error, created_at
            FROM action_tasks 
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))
    else:
        rows = await db.fetchall("""
            SELECT id, agent_id, subagent_id, round_id, mcpcall_id,
                   type, action, args, status, result, error, created_at
            FROM action_tasks 
            ORDER BY created_at DESC
            LIMIT 100
        """)
    
    return {
        "tasks": [_task_row_to_dict(row) for row in rows]
    }


@router.post("/tasks")
async def create_task(data: Dict[str, Any]):
    """Create a new task."""
    from db.database import get_database
    
    db = get_database()
    
    task_id = data.get("id")
    agent_id = data.get("agent_id")
    subagent_id = data.get("subagent_id")
    round_id = data.get("round_id")
    mcpcall_id = data.get("mcpcall_id")
    idempotency_key = data.get("idempotency_key")
    task_type = data.get("type")
    action = data.get("action")
    args = data.get("args", {})
    status = data.get("status", "pending")
    now = datetime.utcnow().isoformat()
    
    try:
        await db.execute("""
            INSERT INTO action_tasks (
                id, agent_id, subagent_id, round_id, mcpcall_id,
                idempotency_key, type, action, args, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, agent_id, subagent_id, round_id, mcpcall_id,
            idempotency_key, task_type, action, json.dumps(args) if isinstance(args, dict) else args,
            status, now
        ))
        return {"status": "ok", "task_id": task_id}
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail="Task with this idempotency_key already exists")
        raise


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, data: Dict[str, Any]):
    """Update task status/result."""
    from db.database import get_database
    
    db = get_database()
    
    updates = []
    params = []
    
    if "status" in data:
        updates.append("status = ?")
        params.append(data["status"])
    
    if "result" in data:
        updates.append("result = ?")
        params.append(json.dumps(data["result"]) if isinstance(data["result"], dict) else data["result"])
    
    if "error" in data:
        updates.append("error = ?")
        params.append(data["error"])
    
    if not updates:
        return {"status": "ok"}
    
    params.append(task_id)
    await db.execute(f"""
        UPDATE action_tasks SET {", ".join(updates)} WHERE id = ?
    """, params)
    
    return {"status": "ok"}


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


@router.patch("/messages/mark-read")
async def mark_messages_read(data: Dict[str, Any]):
    """Mark messages as read."""
    from db.database import get_database
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_database()
    placeholders = ",".join(["?"] * len(message_ids))
    await db.execute(f"""
        UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
    """, message_ids)
    
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
    await db.execute(f"""
        UPDATE chat_messages SET read = 1 WHERE id IN ({placeholders})
    """, message_ids)
    
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
    """Create a chat message (for agent replies)."""
    from db.database import get_database
    from db.repositories.message import MessageRepository
    
    db = get_database()
    repo = MessageRepository(db)
    
    msg = await repo.add_message(
        agent_id=data["agent_id"],
        type=data["type"],
        content=data["content"],
        metadata=data.get("metadata"),
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


def _task_row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert task row to dictionary."""
    args = row.get("args")
    result = row.get("result")
    return {
        "id": row["id"],
        "agent_id": row["agent_id"],
        "subagent_id": row["subagent_id"],
        "round_id": row["round_id"],
        "mcpcall_id": row["mcpcall_id"],
        "type": row["type"],
        "action": row.get("action"),
        "args": json.loads(args) if args else {},
        "status": row["status"],
        "result": json.loads(result) if result else None,
        "error": row.get("error"),
        "created_at": row["created_at"],
    }
