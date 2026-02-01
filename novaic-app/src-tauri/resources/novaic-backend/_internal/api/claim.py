"""
Claim API Routes

Handles Worker task claiming and result submission for the multi-process
architecture. Workers use these endpoints to:
- Claim messages for processing (Agent role)
- Claim tasks for execution (Executor role)
- Submit actions (Agent thinking results)
- Submit execution results (Executor results)

v11: Created for multi-process architecture.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from db import get_database
from db.repositories import (
    ActionTaskRepository,
    MCPExecutionRepository,
    ChatRepository,
)
from sse import get_worker_broadcaster, SSEEvent


router = APIRouter(prefix="/api", tags=["claim"])


# ==================== Request/Response Models ====================

class ClaimRequest(BaseModel):
    """Request to claim a message or task."""
    worker_id: str = Field(..., description="Worker ID making the claim")


class ClaimMessageResponse(BaseModel):
    """Response for message claim."""
    claimed: bool
    message: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ClaimTaskResponse(BaseModel):
    """Response for task claim."""
    claimed: bool
    task: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    reason: Optional[str] = None


class ActionRequest(BaseModel):
    """Request to submit an Agent action (thinking result)."""
    message_id: str = Field(..., description="Associated message ID")
    subagent_id: str = Field(..., description="Runtime instance ID")
    round_id: str = Field(..., description="ReACT round ID")
    mcpcall_id: str = Field(..., description="MCP call ID")
    type: str = Field(..., description="Action type: tool_call, reply, wait, done")
    action: Optional[str] = Field(None, description="MCP tool name (for tool_call)")
    args: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action arguments")


class ActionResponse(BaseModel):
    """Response for action submission."""
    action_id: str
    status: str
    idempotency_key: str


class ResultRequest(BaseModel):
    """Request to submit execution result."""
    status: str = Field(..., description="Result status: done, failed, timeout")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")


class ResultResponse(BaseModel):
    """Response for result submission."""
    accepted: bool
    message: Optional[str] = None


# ==================== Dependencies ====================

async def get_chat_repo() -> ChatRepository:
    """Get ChatRepository instance."""
    db = get_database()
    return ChatRepository(db)


async def get_action_task_repo() -> ActionTaskRepository:
    """Get ActionTaskRepository instance."""
    db = get_database()
    return ActionTaskRepository(db)


async def get_mcp_execution_repo() -> MCPExecutionRepository:
    """Get MCPExecutionRepository instance."""
    db = get_database()
    return MCPExecutionRepository(db)


# ==================== Message Claiming ====================

@router.post("/claim/message/{message_id}", response_model=ClaimMessageResponse)
async def claim_message(
    message_id: str,
    request: ClaimRequest,
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Atomically claim a message for processing.
    
    Used by Workers acting as Agents to claim unread messages.
    
    Args:
        message_id: Message ID to claim
        request: Contains worker_id
    
    Returns:
        - 200 with claimed=True: Successfully claimed, includes message data
        - 200 with claimed=False: Already claimed by another Worker
        - 404: Message not found
    """
    db = get_database()
    claimed_at = datetime.now().isoformat()
    
    # Atomic claim: UPDATE ... WHERE claimed_by IS NULL AND read = 0 (unread = not processed)
    cursor = await db.execute(
        """UPDATE chat_messages 
           SET claimed_by = ?, claimed_at = ?
           WHERE id = ? AND claimed_by IS NULL AND read = 0""",
        (request.worker_id, claimed_at, message_id)
    )
    await db.commit()
    
    if cursor.rowcount > 0:
        # Successfully claimed, fetch message
        message = await chat_repo.get_message(message_id)
        if message:
            return ClaimMessageResponse(
                claimed=True,
                message=message,
            )
    
    # Check if message exists
    message = await chat_repo.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Already claimed or processed
    return ClaimMessageResponse(
        claimed=False,
        reason="Already claimed" if message.get("claimed_by") else "Already processed",
    )


@router.post("/claim/message/{message_id}/release")
async def release_message(
    message_id: str,
    request: ClaimRequest,
):
    """
    Release a claimed message back to pending.
    
    Used when a Worker cannot complete processing.
    
    Args:
        message_id: Message ID to release
        request: Contains worker_id (must match current claimer)
    """
    db = get_database()
    
    cursor = await db.execute(
        """UPDATE chat_messages 
           SET claimed_by = NULL, claimed_at = NULL
           WHERE id = ? AND claimed_by = ?""",
        (message_id, request.worker_id)
    )
    await db.commit()
    
    if cursor.rowcount > 0:
        return {"released": True}
    
    return {"released": False, "reason": "Message not claimed by this worker"}


# ==================== Task Claiming ====================

@router.post("/claim/task/{task_id}", response_model=ClaimTaskResponse)
async def claim_task(
    task_id: str,
    request: ClaimRequest,
    task_repo: ActionTaskRepository = Depends(get_action_task_repo),
):
    """
    Atomically claim a task for execution.
    
    Used by Workers acting as Executors to claim pending tasks.
    
    Args:
        task_id: Task ID to claim
        request: Contains worker_id
    
    Returns:
        - 200 with claimed=True: Successfully claimed, includes task data and idempotency_key
        - 200 with claimed=False: Already claimed by another Worker
        - 404: Task not found
    """
    # Attempt atomic claim
    task = await task_repo.claim(task_id, request.worker_id)
    
    if task:
        return ClaimTaskResponse(
            claimed=True,
            task=task,
            idempotency_key=task.get("idempotency_key"),
        )
    
    # Check if task exists
    existing = await task_repo.get(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Already claimed or not pending
    return ClaimTaskResponse(
        claimed=False,
        reason=f"Task status is '{existing.get('status')}'" if existing.get("status") != "pending" else "Already claimed",
    )


@router.post("/claim/task/{task_id}/release")
async def release_task(
    task_id: str,
    request: ClaimRequest,
    task_repo: ActionTaskRepository = Depends(get_action_task_repo),
):
    """
    Release a claimed task back to pending.
    
    Used when a Worker cannot complete execution.
    """
    # Check if this worker owns the task
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.get("claimed_by") != request.worker_id:
        return {"released": False, "reason": "Task not claimed by this worker"}
    
    released = await task_repo.release(task_id)
    
    if released:
        # Broadcast that task is available again
        broadcaster = get_worker_broadcaster()
        await broadcaster.broadcast_new_task(
            task_id=task_id,
            agent_id=task["agent_id"],
            task_type=task["type"],
            action=task.get("action"),
            idempotency_key=task.get("idempotency_key"),
        )
    
    return {"released": released}


# ==================== Action Submission ====================

@router.post("/action", response_model=ActionResponse)
async def submit_action(
    request: ActionRequest,
    task_repo: ActionTaskRepository = Depends(get_action_task_repo),
):
    """
    Submit an Agent action (thinking result).
    
    Called by Workers after LLM thinking to submit actions:
    - tool_call: Schedule tool execution
    - reply: Schedule message reply
    - wait: Waiting for async result
    - done: Processing complete
    
    Args:
        request: Action details including subagent_id, round_id, mcpcall_id
    
    Returns:
        Created action task ID and idempotency_key
    """
    # Generate task ID
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    
    # Determine agent_id from message
    db = get_database()
    cursor = await db.execute(
        "SELECT agent_id FROM chat_messages WHERE id = ?",
        (request.message_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Message not found")
    
    agent_id = row["agent_id"]
    
    # Determine initial status
    initial_status = "pending"
    if request.type == "done":
        # Mark message as read (read=1 means processed)
        await db.execute(
            "UPDATE chat_messages SET read = 1 WHERE id = ?",
            (request.message_id,)
        )
        await db.commit()
        
        return ActionResponse(
            action_id=task_id,
            status="processed",
            idempotency_key=f"{agent_id}-{request.subagent_id}-{request.round_id}-{request.mcpcall_id}",
        )
    
    # Create action task
    task = await task_repo.create(
        id=task_id,
        agent_id=agent_id,
        subagent_id=request.subagent_id,
        round_id=request.round_id,
        mcpcall_id=request.mcpcall_id,
        type=request.type,
        action=request.action,
        args=request.args,
        message_id=request.message_id,
        status=initial_status,
    )
    
    # Broadcast new task event
    broadcaster = get_worker_broadcaster()
    await broadcaster.broadcast_new_task(
        task_id=task_id,
        agent_id=agent_id,
        task_type=request.type,
        action=request.action,
        idempotency_key=task["idempotency_key"],
    )
    
    return ActionResponse(
        action_id=task_id,
        status="queued",
        idempotency_key=task["idempotency_key"],
    )


# ==================== Result Submission ====================

@router.post("/result/{task_id}", response_model=ResultResponse)
async def submit_result(
    task_id: str,
    request: ResultRequest,
    task_repo: ActionTaskRepository = Depends(get_action_task_repo),
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_execution_repo),
):
    """
    Submit execution result for a task.
    
    Called by Workers after executing an action to submit results.
    
    Args:
        task_id: Task ID
        request: Result details (status, result, error)
    
    Returns:
        Acceptance confirmation
    """
    # Get task
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task status
    if request.status == "done":
        await task_repo.complete(task_id, request.result)
    elif request.status == "failed":
        await task_repo.fail(task_id, request.error or "Unknown error")
    elif request.status == "timeout":
        await task_repo.timeout(task_id)
    else:
        await task_repo.update_status(task_id, request.status, request.result, request.error)
    
    # Update MCP execution record if exists
    idempotency_key = task.get("idempotency_key")
    if idempotency_key:
        if request.status == "done":
            await mcp_repo.complete(idempotency_key, request.result)
        elif request.status == "failed":
            await mcp_repo.fail(idempotency_key, request.error or "Unknown error")
        elif request.status == "timeout":
            await mcp_repo.timeout(idempotency_key)
    
    # Unblock dependent tasks
    if request.status in ("done", "failed", "timeout"):
        await task_repo.unblock_dependents(task_id)
    
    # Broadcast result
    broadcaster = get_worker_broadcaster()
    await broadcaster.broadcast_task_result(
        task_id=task_id,
        status=request.status,
        result=request.result,
        error=request.error,
    )
    
    # Check if round is complete
    subagent_id = task.get("subagent_id")
    round_id = task.get("round_id")
    if subagent_id and round_id:
        is_complete = await task_repo.is_round_complete(subagent_id, round_id)
        if is_complete:
            await broadcaster.broadcast_round_complete(subagent_id, round_id)
    
    return ResultResponse(
        accepted=True,
        message=f"Result for task {task_id} accepted",
    )


# ==================== Batch Operations ====================

@router.get("/pending/messages")
async def get_pending_messages(
    agent_id: Optional[str] = None,
    limit: int = 50,
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Get pending (unclaimed, unread) messages.
    
    Used by Workers to discover available work.
    read=0 means the message hasn't been processed yet.
    """
    db = get_database()
    
    if agent_id:
        rows = await db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE agent_id = ? AND claimed_by IS NULL AND read = 0
               ORDER BY timestamp ASC LIMIT ?""",
            (agent_id, limit)
        )
    else:
        rows = await db.fetchall(
            """SELECT * FROM chat_messages 
               WHERE claimed_by IS NULL AND read = 0
               ORDER BY timestamp ASC LIMIT ?""",
            (limit,)
        )
    
    return {"messages": [dict(row) for row in rows]}


@router.get("/pending/tasks")
async def get_pending_tasks(
    agent_id: Optional[str] = None,
    limit: int = 50,
    task_repo: ActionTaskRepository = Depends(get_action_task_repo),
):
    """
    Get pending (unclaimed) tasks.
    
    Used by Workers to discover available work.
    """
    tasks = await task_repo.get_pending_tasks(agent_id=agent_id, limit=limit)
    return {"tasks": tasks}
