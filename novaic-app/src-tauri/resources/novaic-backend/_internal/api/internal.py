"""
Internal API for Master（Backend 组件）.

Master 通过本 API 与 Gateway（DB、任务、消息等）交互。
MCP 生命周期由 MCP Gateway（另一 Backend 组件）提供。仅内部使用。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

router = APIRouter(prefix="/internal", tags=["internal"])


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


@router.get("/runtimes/{subagent_id}")
async def get_runtime(subagent_id: str):
    """Get a single runtime by ID."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.get_by_id(subagent_id)
    
    if not runtime:
        raise HTTPException(status_code=404, detail="Runtime not found")
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes/main")
async def create_main_runtime(data: Dict[str, Any]):
    """Create a new Main Runtime."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    agent_id = data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.create_main_runtime(agent_id)
    
    return _runtime_to_dict(runtime)


@router.post("/runtimes/sub")
async def create_sub_runtime(data: Dict[str, Any]):
    """Create a new Sub Runtime."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    agent_id = data.get("agent_id")
    parent_subagent_id = data.get("parent_subagent_id")
    initial_context = data.get("initial_context", [])
    
    if not agent_id or not parent_subagent_id:
        raise HTTPException(status_code=400, detail="agent_id and parent_subagent_id required")
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.create_sub_runtime(agent_id, parent_subagent_id, initial_context)
    
    return _runtime_to_dict(runtime)


@router.patch("/runtimes/{subagent_id}")
async def update_runtime(subagent_id: str, data: Dict[str, Any]):
    """Update runtime fields."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    
    # Handle specific updates
    if "phase" in data and "pending_actions" in data:
        await repo.set_pending_actions(
            subagent_id, 
            data["pending_actions"], 
            data["phase"]
        )
    elif "phase" in data:
        await repo.set_phase(subagent_id, data["phase"])
    
    if "context" in data:
        await repo.update_context(subagent_id, data["context"])
    
    if "mcp_url" in data:
        await repo.set_mcp_url(subagent_id, data["mcp_url"])
    
    if "status" in data:
        if data["status"] == "completed":
            await repo.mark_completed(subagent_id)
        elif data["status"] == "failed":
            await repo.mark_failed(subagent_id, data.get("error", "Unknown error"))
    
    return {"status": "ok"}


@router.post("/runtimes/{subagent_id}/rest")
async def rest_runtime(subagent_id: str, data: Dict[str, Any]):
    """
    Put a runtime into resting state.
    
    Called by runtime_rest tool. This sets the runtime status to 'resting',
    which tells the Scheduler to complete the runtime instead of starting next round.
    
    Args:
        subagent_id: Runtime ID
        data: {
            "reason": str - Why the runtime is resting
            "wake_triggers": list - Conditions to wake up
            "handoff_notes": str - Notes for next activation
        }
    """
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    
    # Check if runtime exists
    runtime = await repo.get_by_id(subagent_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    # Set runtime status to 'resting'
    reason = data.get("reason", "No reason provided")
    wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
    handoff_notes = data.get("handoff_notes")
    
    # Update runtime with resting status and metadata
    await repo.set_resting(
        subagent_id,
        reason=reason,
        wake_triggers=wake_triggers,
        handoff_notes=handoff_notes
    )
    
    return {
        "success": True,
        "state": "resting",
        "reason": reason,
        "triggers_set": len(wake_triggers),
        "estimated_wake": None,
        "handoff_notes": handoff_notes,
    }


@router.post("/runtimes/{subagent_id}/wake")
async def wake_runtime(subagent_id: str):
    """Wake a sleeping runtime (atomic CAS operation).
    
    Returns success=True only if the runtime was actually woken up.
    Returns success=False if runtime was already active or not found.
    """
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    success = await repo.wake_main_runtime(subagent_id)
    
    return {"status": "ok" if success else "skipped", "success": success}


@router.post("/runtimes/{subagent_id}/advance")
async def advance_runtime_round(subagent_id: str, data: Dict[str, Any] = None):
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
    
    new_round_id = await repo.advance_round(subagent_id, expected_round_num)
    
    if new_round_id is None:
        return {"round_id": None, "success": False, "reason": "CAS conflict or runtime not found"}
    
    return {"round_id": new_round_id, "success": True}


@router.post("/runtimes/{subagent_id}/claim-phase")
async def try_claim_phase(subagent_id: str, data: Dict[str, Any]):
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
    
    # Atomic CAS: only update if phase matches expected
    cursor = await db.execute("""
        UPDATE agent_runtimes 
        SET phase = ?, updated_at = ?
        WHERE subagent_id = ? AND phase = ?
    """, (new_phase, now, subagent_id, expected_phase))
    await db.commit()
    
    return {"success": cursor.rowcount > 0}


@router.delete("/runtimes/{subagent_id}")
async def delete_runtime(subagent_id: str):
    """Delete a runtime."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    await repo.delete(subagent_id)
    
    return {"status": "ok"}


@router.get("/runtimes/main/{agent_id}")
async def get_main_runtime(agent_id: str):
    """Get main runtime for an agent."""
    from db.database import get_database
    from db.repositories import RuntimeRepository
    
    db = get_database()
    repo = RuntimeRepository(db)
    runtime = await repo.get_main_runtime(agent_id)
    
    if not runtime:
        return {"runtime": None}
    
    return {"runtime": _runtime_to_dict(runtime)}


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
    """Get unprocessed messages for an agent (for Scheduler to include in context).
    
    Note: Only checks processed=0, not read status.
    read is for frontend display, processed is for Agent processing.
    """
    from db.database import get_database
    
    db = get_database()
    rows = await db.fetchall("""
        SELECT id, type, content, metadata, timestamp 
        FROM chat_messages 
        WHERE agent_id = ? AND processed = 0 AND type = 'USER_MESSAGE'
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
    """Get count of unprocessed messages (for Monitor to detect new messages).
    
    Note: Only checks processed=0, not read status.
    read is for frontend display, processed is for Agent processing.
    """
    from db.database import get_database
    
    db = get_database()
    row = await db.fetchone("""
        SELECT COUNT(*) as count FROM chat_messages 
        WHERE agent_id = ? AND processed = 0 AND type = 'USER_MESSAGE'
    """, (agent_id,))
    
    return {"count": row["count"] if row else 0}


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
    """Mark messages as processed."""
    from db.database import get_database
    
    message_ids = data.get("message_ids", [])
    if not message_ids:
        return {"status": "ok"}
    
    db = get_database()
    placeholders = ",".join(["?"] * len(message_ids))
    await db.execute(f"""
        UPDATE chat_messages SET processed = 1 WHERE id IN ({placeholders})
    """, message_ids)
    
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
    """Convert runtime to dictionary."""
    return {
        "subagent_id": runtime.subagent_id,
        "agent_id": runtime.agent_id,
        "type": runtime.type,
        "parent_subagent_id": runtime.parent_subagent_id,
        "mcp_url": runtime.mcp_url,
        "current_round_id": runtime.current_round_id,
        "current_round_num": runtime.current_round_num,
        "phase": runtime.phase,
        "context": runtime.context,
        "pending_actions": runtime.pending_actions,
        "status": runtime.status,
        "error": runtime.error,
        "created_at": runtime.created_at,
        "updated_at": runtime.updated_at,
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
