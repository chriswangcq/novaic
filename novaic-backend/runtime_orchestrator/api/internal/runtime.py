"""
Runtime internal APIs — canonical implementation owned by Runtime Orchestrator.

RO owns the runtime domain. Gateway forwards /internal/runtimes* requests here.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import timedelta

from common.enums import RuntimeStatus
from common.utils.time import utc_now, utc_now_iso
from common.config import ServiceConfig
from runtime_orchestrator.db import get_db
from runtime_orchestrator.db.repositories import RuntimeRepository, SubAgentRepository
from .helpers import _runtime_to_dict

runtime_state_router = APIRouter(tags=["internal"])
router = runtime_state_router

# ==================== Runtime Operations ====================


@runtime_state_router.get("/runtimes/active")
async def get_active_runtimes():
    """Get all active runtimes."""
    db = get_db()
    repo = RuntimeRepository(db)
    runtimes = repo.get_all_active_runtimes()

    return {
        "runtimes": [_runtime_to_dict(r) for r in runtimes]
    }


@runtime_state_router.get("/runtimes/list")
async def list_active_runtimes_for_mcp():
    """List all active runtimes.
    
    Used by Tools Server for runtime_list tool.
    NOTE: Must be defined BEFORE /runtimes/{runtime_id} to avoid route conflict.
    """
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


@runtime_state_router.post("/runtimes/batch")
async def get_runtimes_batch(data: Dict[str, Any]):
    """Get multiple runtimes by IDs (for context building).
    
    Request body:
        runtime_ids: List[str] - List of runtime IDs to fetch
        
    Returns:
        runtimes: List of runtime dicts with summaries, in input order
    """
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


@runtime_state_router.get("/runtimes/with-tools")
async def get_runtimes_with_tools():
    """Get all active runtimes that have tool_ports registered.
    
    Used by Tools Server on startup to restore runtime tool contexts.
    Returns only runtimes with status = 'active' AND tool_ports IS NOT NULL.
    
    NOTE: Must be defined BEFORE /runtimes/{runtime_id} to avoid route conflict.
    """
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


@runtime_state_router.get("/runtimes/{runtime_id}")
async def get_runtime(runtime_id: str):
    """Get a single runtime by ID."""
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_by_id(runtime_id)

    if not runtime:
        raise HTTPException(status_code=404, detail="Runtime not found")

    return _runtime_to_dict(runtime)


@runtime_state_router.post("/runtimes")
async def create_runtime(data: Dict[str, Any]):
    """Create a new Runtime for a SubAgent (v14)."""
    agent_id = data.get("agent_id")
    subagent_id = data.get("subagent_id", "main")
    initial_context = data.get("initial_context", [])

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.create_runtime(subagent_id, agent_id, initial_context)

    return _runtime_to_dict(runtime)


@runtime_state_router.post("/runtimes/get-or-create")
async def get_or_create_runtime(data: Dict[str, Any]):
    """原子操作：获取或创建 active runtime。
    
    如果已有 active runtime，返回它；否则创建新的。
    用于替代 awaking 状态，保证同一时间只有一个 active runtime。
    
    Request body:
        agent_id: str - Agent ID
        subagent_id: str - SubAgent ID (default: "main")
        initial_context: List[Dict] - 新创建时的初始 context (optional)
        
    Returns:
        runtime: Runtime dict
        just_created: bool - 是否新创建的
    """
    agent_id = data.get("agent_id")
    subagent_id = data.get("subagent_id", "main")
    initial_context = data.get("initial_context", [])
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")
    
    db = get_db()
    repo = RuntimeRepository(db)
    runtime, just_created = repo.get_or_create_active_runtime(
        subagent_id, agent_id, initial_context
    )
    
    result = _runtime_to_dict(runtime)
    result["just_created"] = just_created
    return result


@runtime_state_router.post("/runtimes/main")
async def create_main_runtime(data: Dict[str, Any]):
    """Create a new Main Runtime (deprecated, use POST /runtimes)."""
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


@runtime_state_router.patch("/runtimes/{runtime_id}")
async def update_runtime(runtime_id: str, data: Dict[str, Any]):
    """Update runtime fields."""
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


@runtime_state_router.post("/runtimes/{runtime_id}/rest")
async def rest_runtime(runtime_id: str, data: Dict[str, Any]):
    """
    Set runtime need_rest flag and update SubAgent wake triggers.
    
    Called by runtime_rest tool. Sets need_rest=1 on runtime and
    updates the SubAgent's wake_triggers for scheduled wake.
    
    Args:
        runtime_id: Runtime ID
        data: {
            "reason": str - Why the runtime needs rest
            "wake_triggers": list - Conditions to wake up
            "handoff_notes": str - Notes for next activation
        }
    """
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    subagent_repo = SubAgentRepository(db)
    
    # Check if runtime exists
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    # Set need_rest=1 (不再设置 status='resting')
    runtime_repo.set_need_rest(runtime_id, True)
    
    # Update SubAgent's wake triggers and schedule (v26)
    reason = data.get("reason", "No reason provided")
    wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
    handoff_notes = data.get("handoff_notes")
    rest_duration = data.get("rest_duration_minutes", 30)
    rest_duration = max(1, min(1440, rest_duration))  # clamp 1min - 24h
    
    wake_at = (utc_now() + timedelta(minutes=rest_duration)).isoformat()
    
    subagent_repo.update_wake_info(
        runtime.subagent_id,
        runtime.agent_id,
        wake_triggers=wake_triggers,
        wake_at=wake_at,
        handoff_notes=handoff_notes,
    )
    
    return {
        "success": True,
        "state": "need_rest",
        "reason": reason,
        "triggers_set": len(wake_triggers),
        "estimated_wake": wake_at,
        "rest_duration_minutes": rest_duration,
        "handoff_notes": handoff_notes,
    }


@runtime_state_router.post("/runtimes/{runtime_id}/wake")
async def wake_runtime(runtime_id: str):
    """Wake a sleeping runtime (deprecated in v14, use SubAgent wake).
    
    Returns success=True only if the runtime was actually woken up.
    Returns success=False if runtime was already active or not found.
    """
    db = get_db()
    repo = RuntimeRepository(db)
    success = repo.wake_main_runtime(runtime_id)
    
    return {"status": "ok" if success else "skipped", "success": success}


@runtime_state_router.post("/runtimes/{runtime_id}/advance")
async def advance_runtime_round(runtime_id: str, data: Dict[str, Any] = None):
    """Advance runtime to next round (with optional CAS).
    
    Args:
        data: Optional dict with 'expected_round_num' for CAS operation
    """
    db = get_db()
    repo = RuntimeRepository(db)
    
    expected_round_num = None
    if data:
        expected_round_num = data.get("expected_round_num")
    
    new_round_id = repo.advance_round(runtime_id, expected_round_num)
    
    if new_round_id is None:
        return {"round_id": None, "success": False, "reason": "CAS conflict or runtime not found"}
    
    return {"round_id": new_round_id, "success": True}


@runtime_state_router.post("/runtimes/{runtime_id}/context/append")
async def append_runtime_context(runtime_id: str, data: Dict[str, Any]):
    """Append a message to runtime context with idempotency."""
    message = data.get("message")
    # 检查 message 是否为 None 或空字典（空字典视为无效消息）
    if message is None:
        raise HTTPException(status_code=400, detail="message required")
    # 空字典 {} 也视为无效消息
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

    # 注意：不在这里处理图片分离！
    # 保持原始 tool result（包含完整图片数据）
    # 图片提取由 task_queue/utils/context.py:process_multimodal_messages 在 LLM 调用时处理

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


@runtime_state_router.post("/runtimes/{runtime_id}/set-status")
async def set_runtime_status(runtime_id: str, data: Dict[str, Any]):
    """Set runtime status with CAS on expected status list."""
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


@runtime_state_router.post("/runtimes/{runtime_id}/summarized")
async def set_runtime_summarized(runtime_id: str, data: Dict[str, Any] = None):
    """Set runtime summarized flag to 1 (idempotent)."""
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


@runtime_state_router.post("/runtimes/{runtime_id}/hot-cold-summary")
async def set_runtime_hot_cold_summary(runtime_id: str, data: Dict[str, Any]):
    """Set both hot and cold summaries for a runtime (v24).
    
    Hot summary: Earlier rounds summarized + last 3 rounds full content
    Cold summary: All rounds summarized by LLM
    """
    hot_summary = data.get("hot_summary", "")
    cold_summary = data.get("cold_summary", "")

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}
    
    runtime_repo.set_hot_cold_summary(runtime_id, hot_summary, cold_summary)

    return {"success": True, "runtime_id": runtime_id}


@runtime_state_router.post("/runtimes/{runtime_id}/need-rest")
async def set_runtime_need_rest(runtime_id: str, data: Dict[str, Any]):
    """Set runtime need_rest flag (idempotent).
    
    Note: 使用非 CAS 版本的 set_need_rest，因为：
    1. 这个操作本身是幂等的（设置为固定值）
    2. 不需要检查当前值
    """
    value = bool(data.get("value", True))
    target = 1 if value else 0

    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    # 直接设置 need_rest 标志（幂等操作）
    runtime_repo.set_need_rest(runtime_id, target)

    # 验证设置是否成功
    runtime = runtime_repo.get_by_id(runtime_id)
    if not runtime:
        return {"success": False, "message": "Runtime not found", "current_value": "not_found"}
    
    return {
        "success": runtime.need_rest == target,
        "current_value": str(runtime.need_rest),
        "message": "OK" if runtime.need_rest == target else "Update failed",
    }


@runtime_state_router.post("/runtimes/{runtime_id}/tool-ports")
async def set_runtime_tool_ports(runtime_id: str, data: Dict[str, Any]):
    """Save Tools Server MCP ports for a runtime.
    
    Called by Tools Server when registering/unregistering a runtime.
    Enables recovery after Tools Server restart.
    
    Request body:
        ports: dict - MCP ports (e.g. {"vmuse": 8080}), or null to clear
    """
    ports = data.get("ports")
    
    db = get_db()
    runtime_repo = RuntimeRepository(db)
    
    if ports is not None:
        runtime_repo.set_tool_ports(runtime_id, ports)
    else:
        runtime_repo.clear_tool_ports(runtime_id)
    
    return {"success": True, "runtime_id": runtime_id}


@runtime_state_router.delete("/runtimes/{runtime_id}")
async def delete_runtime(runtime_id: str):
    """Delete a runtime."""
    db = get_db()
    repo = RuntimeRepository(db)
    repo.delete(runtime_id)
    
    return {"status": "ok"}


@runtime_state_router.get("/runtimes/main/{agent_id}")
async def get_main_runtime(agent_id: str):
    """Get active main runtime for an agent (v14: from main SubAgent)."""
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_active_runtime("main", agent_id)

    if not runtime:
        return {"runtime": None}

    return {"runtime": _runtime_to_dict(runtime)}


@runtime_state_router.get("/runtimes/subagent/{agent_id}/{subagent_id}")
async def get_subagent_runtime(agent_id: str, subagent_id: str):
    """Get active runtime for a SubAgent (v14)."""
    db = get_db()
    repo = RuntimeRepository(db)
    runtime = repo.get_active_runtime(subagent_id, agent_id)

    if not runtime:
        return {"runtime": None}

    return {"runtime": _runtime_to_dict(runtime)}


@runtime_state_router.get("/runtimes/latest/{agent_id}/{subagent_id}")
async def get_latest_runtimes(
    agent_id: str, subagent_id: str, limit: int = 30
):
    """Get latest completed runtimes for a SubAgent (for context preparation, v14)."""
    db = get_db()
    repo = RuntimeRepository(db)
    runtimes = repo.get_latest_runtimes(subagent_id, agent_id, limit)

    return {"runtimes": [_runtime_to_dict(r) for r in runtimes]}


@runtime_state_router.get("/agents/{agent_id}/subagents/{subagent_id}/has-active-runtime")
async def has_active_runtime(agent_id: str, subagent_id: str):
    """Check if SubAgent has an active runtime (status = active)."""
    db = get_db()
    repo = RuntimeRepository(db)
    has_active = repo.has_active_runtime(subagent_id, agent_id)

    return {"has_active_runtime": has_active}


@runtime_state_router.post("/runtimes/{runtime_id}/history")
async def get_runtime_history(runtime_id: str, data: Dict[str, Any]):
    """Get message history for a runtime.
    
    Used by Tools Server for runtime_history tool.
    Queries runtime's context which contains the conversation history.
    """
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


@runtime_state_router.post("/runtimes/{runtime_id}/send")
async def send_to_runtime(runtime_id: str, data: Dict[str, Any]):
    """Send a message to a runtime.
    
    Used by Tools Server for runtime_send tool.
    Appends the message to the runtime's context.
    """
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
        "timestamp": utc_now_iso(),
    })
    
    repo.update_context(runtime_id, context)
    
    return {"success": True, "queued": True, "runtime_id": runtime_id}
