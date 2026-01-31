"""
MCP API Routes

Provides endpoints for MCP execution management:
- Callback API for async MCP task completion
- Idempotency query API for execution status lookup
- Execution management endpoints

v11: Created for multi-process architecture.
"""

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from db import get_database
from db.repositories import MCPExecutionRepository, ActionTaskRepository
from sse import get_worker_broadcaster, SSEEvent


router = APIRouter(prefix="/api/mcp", tags=["mcp"])


# ==================== Request/Response Models ====================

class MCPCallbackRequest(BaseModel):
    """Request for MCP callback (async task completion)."""
    idempotency_key: str = Field(..., description="Execution idempotency key")
    status: str = Field(..., description="Execution status: done, failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")


class MCPCallbackResponse(BaseModel):
    """Response for MCP callback."""
    accepted: bool
    message: str


class MCPExecutionResponse(BaseModel):
    """Response for MCP execution query."""
    idempotency_key: str
    agent_id: str
    subagent_id: str
    round_id: str
    mcpcall_id: str
    tool_name: str
    args: Optional[Dict[str, Any]]
    status: str
    result: Optional[Any]
    error: Optional[str]
    created_at: str
    executed_at: Optional[str]


class MCPCreateRequest(BaseModel):
    """Request to create MCP execution record."""
    idempotency_key: str
    agent_id: str
    subagent_id: str
    round_id: str
    mcpcall_id: str
    tool_name: str
    args: Optional[Dict[str, Any]] = None


# ==================== Dependencies ====================

async def get_mcp_repo() -> MCPExecutionRepository:
    """Get MCPExecutionRepository instance."""
    db = get_database()
    return MCPExecutionRepository(db)


async def get_task_repo() -> ActionTaskRepository:
    """Get ActionTaskRepository instance."""
    db = get_database()
    return ActionTaskRepository(db)


# ==================== Callback API ====================

@router.post("/callback", response_model=MCPCallbackResponse)
async def mcp_callback(
    request: MCPCallbackRequest,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
    task_repo: ActionTaskRepository = Depends(get_task_repo),
):
    """
    Receive callback for async MCP task completion.
    
    Called by MCP servers when an async operation completes.
    Updates the execution record and notifies waiting Workers.
    
    Args:
        request: Callback data with status and result
    
    Returns:
        Acceptance confirmation
    """
    key = request.idempotency_key
    
    # Get existing execution
    existing = await mcp_repo.get(key)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {key}"
        )
    
    # Update based on status
    if request.status == "done":
        # Check if already done (idempotent)
        if existing["status"] == "done":
            return MCPCallbackResponse(
                accepted=True,
                message="Already completed (idempotent)",
            )
        
        # Update or handle late result
        if existing["status"] == "timeout":
            await mcp_repo.update_late_result(key, request.result)
        else:
            await mcp_repo.complete(key, request.result)
        
    elif request.status == "failed":
        if existing["status"] not in ("done", "failed"):
            await mcp_repo.fail(key, request.error or "Unknown error")
    
    # Find and update associated task
    task = await task_repo.get_by_idempotency_key(key)
    if task:
        if request.status == "done":
            await task_repo.complete(task["id"], request.result)
        elif request.status == "failed":
            await task_repo.fail(task["id"], request.error or "Unknown error")
        
        # Broadcast result
        broadcaster = get_worker_broadcaster()
        await broadcaster.broadcast_task_result(
            task_id=task["id"],
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
    
    return MCPCallbackResponse(
        accepted=True,
        message=f"Callback processed for {key}",
    )


# ==================== Idempotency Query API ====================

@router.get("/execution/{idempotency_key}", response_model=MCPExecutionResponse)
async def get_mcp_execution(
    idempotency_key: str,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    Query MCP execution status by idempotency key.
    
    Used for:
    - Checking if a tool call has already been executed
    - Retrieving results of timed-out executions
    - Debugging and auditing
    
    Args:
        idempotency_key: Combined key (agent_id-subagent_id-round_id-mcpcall_id)
    
    Returns:
        Execution record with status and result
    """
    execution = await mcp_repo.get(idempotency_key)
    
    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {idempotency_key}"
        )
    
    return MCPExecutionResponse(**execution)


@router.get("/execution/{idempotency_key}/status")
async def get_execution_status(
    idempotency_key: str,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    Quick check of execution status.
    
    Args:
        idempotency_key: Execution key
    
    Returns:
        {"status": str, "is_done": bool}
    """
    execution = await mcp_repo.get(idempotency_key)
    
    if not execution:
        return {
            "status": "not_found",
            "is_done": False,
            "exists": False,
        }
    
    return {
        "status": execution["status"],
        "is_done": execution["status"] in ("done", "failed"),
        "exists": True,
    }


# ==================== Execution Management ====================

@router.post("/execution", response_model=MCPExecutionResponse)
async def create_mcp_execution(
    request: MCPCreateRequest,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    Create an MCP execution record.
    
    Called by Executors before calling the actual MCP tool
    to register the execution for idempotency.
    
    If the execution already exists:
    - If done: returns existing result
    - If executing: returns executing status
    - If failed/timeout: allows retry
    
    Args:
        request: Execution details
    
    Returns:
        Execution record (new or existing)
    """
    execution, was_created = await mcp_repo.get_or_create(
        idempotency_key=request.idempotency_key,
        agent_id=request.agent_id,
        subagent_id=request.subagent_id,
        round_id=request.round_id,
        mcpcall_id=request.mcpcall_id,
        tool_name=request.tool_name,
        args=request.args,
    )
    
    return MCPExecutionResponse(**execution)


@router.post("/execution/{idempotency_key}/complete")
async def complete_execution(
    idempotency_key: str,
    result: Optional[Dict[str, Any]] = None,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    Mark an execution as complete.
    
    Args:
        idempotency_key: Execution key
        result: Execution result
    
    Returns:
        {"success": bool}
    """
    success = await mcp_repo.complete(idempotency_key, result)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {idempotency_key}"
        )
    
    return {"success": True}


@router.post("/execution/{idempotency_key}/fail")
async def fail_execution(
    idempotency_key: str,
    error: str,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    Mark an execution as failed.
    
    Args:
        idempotency_key: Execution key
        error: Error message
    
    Returns:
        {"success": bool}
    """
    success = await mcp_repo.fail(idempotency_key, error)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Execution not found: {idempotency_key}"
        )
    
    return {"success": True}


# ==================== Listing ====================

@router.get("/executions")
async def list_executions(
    agent_id: Optional[str] = None,
    subagent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    List MCP executions with optional filters.
    
    Args:
        agent_id: Filter by agent ID
        subagent_id: Filter by subagent ID
        status: Filter by status
        limit: Maximum number of results
    
    Returns:
        {"executions": [...]}
    """
    if not agent_id:
        # For now, require agent_id to avoid listing all
        raise HTTPException(
            status_code=400,
            detail="agent_id is required"
        )
    
    executions = await mcp_repo.get_by_agent(
        agent_id=agent_id,
        subagent_id=subagent_id,
        status=status,
        limit=limit,
    )
    
    return {"executions": executions}


@router.get("/executions/stale")
async def list_stale_executions(
    timeout_minutes: int = 10,
    mcp_repo: MCPExecutionRepository = Depends(get_mcp_repo),
):
    """
    List executions that have been executing for too long.
    
    Useful for monitoring and debugging.
    
    Args:
        timeout_minutes: Threshold for considering execution as stale
    
    Returns:
        {"executions": [...]}
    """
    executions = await mcp_repo.get_executing(timeout_minutes=timeout_minutes)
    return {"executions": executions}


# Note: Workers should call MCP servers DIRECTLY, not through Gateway API.
# See executor_handler.py and llm_caller.py for correct implementation.
