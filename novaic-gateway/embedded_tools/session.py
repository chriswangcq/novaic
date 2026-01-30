"""
Session Tools - Agent Context and Self-Management

These tools allow the agent to manage contexts and self-schedule.
They call the Gateway's internal APIs directly (no external HTTP).
"""

import os
import httpx
from typing import Optional, List, Dict, Any

# Gateway URL for internal API calls
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")


async def _call_gateway(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Call the gateway internal API."""
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        url = f"{GATEWAY_URL}/api/internal{endpoint}"
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data or {})
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()


async def agent_context_list() -> Dict[str, Any]:
    """
    List all active agent contexts.
    
    Contexts represent independent conversation environments:
    - main: Primary conversation with user
    - subagent:xxx / task:xxx: Sub-agent or task conversations
    
    Returns:
        Dictionary with:
        - contexts: List of context info with:
            - context_key: Identifier (e.g., "main", "task:abc123")
            - type: Context type (main, subagent, task)
            - status: Current status (active, idle, completed)
            - message_count: Number of messages in history
            - parent: Parent context key (for sub-agents)
            - created_at: Creation timestamp
            - last_activity: Last activity timestamp
    
    Examples:
        agent_context_list()
        # Returns: {"contexts": [{"context_key": "main", ...}, {"context_key": "task:abc123", ...}]}
    """
    try:
        result = await _call_gateway("/sessions")
        if "sessions" in result:
            result["contexts"] = result.pop("sessions")
            for ctx in result.get("contexts", []):
                if "session_key" in ctx:
                    ctx["context_key"] = ctx.pop("session_key")
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "contexts": []}


async def agent_context_history(
    context_key: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Get message history for a specific context.
    
    Use this to see what a sub-agent has been thinking and doing,
    or to review the main conversation history.
    
    Args:
        context_key: The context to get history for (e.g., "main", "task:abc123")
        limit: Maximum number of messages to return (default: 50)
        offset: Number of messages to skip from the start (default: 0)
    
    Returns:
        Dictionary with:
        - context_key: The queried context
        - messages: List of messages with:
            - role: 'user', 'assistant', or 'system'
            - content: Message content
            - timestamp: Message timestamp
            - tool_calls: Any tool calls made (for assistant messages)
        - total: Total message count
    
    Examples:
        # Get recent history from a sub-agent
        agent_context_history(context_key="task:abc123")
        
        # Get more messages with pagination
        agent_context_history(context_key="main", limit=100, offset=50)
    """
    try:
        result = await _call_gateway(
            f"/sessions/{context_key}/history",
            method="POST",
            data={"limit": limit, "offset": offset}
        )
        result["context_key"] = context_key
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "context_key": context_key, "messages": []}


async def agent_context_send(
    context_key: str,
    message: str,
    wait_response: Optional[bool] = False,
    timeout: Optional[int] = 60
) -> Dict[str, Any]:
    """
    Send a message to another context.
    
    Use this to communicate between contexts or inject messages.
    
    Args:
        context_key: Target context key
        message: Message content to send
        wait_response: If True, wait for the context to process and respond (default: False)
        timeout: Timeout in seconds when wait_response is True (default: 60)
    
    Returns:
        Dictionary with:
        - success: Whether the message was sent successfully
        - context_key: Target context
        - response: The context's response (if wait_response=True)
        - queued: Whether message was queued for processing
    
    Examples:
        # Send a message to a sub-agent
        agent_context_send(context_key="task:abc123", message="请优先处理这个问题")
        
        # Send and wait for response
        agent_context_send(context_key="task:abc123", message="当前进度?", wait_response=True)
    """
    try:
        result = await _call_gateway(
            f"/sessions/{context_key}/send",
            method="POST",
            data={
                "message": message,
                "wait_response": wait_response,
                "timeout": timeout
            }
        )
        result["context_key"] = context_key
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "success": False, "context_key": context_key}


async def agent_inbox() -> Dict[str, Any]:
    """
    Check the inbox for pending events and messages.
    
    Use this to stay aware of new events during long-running tasks.
    Call periodically (every 3-5 iterations) to check if there are
    urgent matters that need attention.
    
    Returns:
        Dictionary with:
        - pending_count: Number of pending events
        - events: List of pending events with summaries
        - has_urgent: Whether any event is marked urgent
        - oldest_age_seconds: Age of oldest pending event
        - recommendation: Suggested action ("continue", "check_urgent", "process_all")
    
    Examples:
        agent_inbox()
        # Returns: {"pending_count": 2, "has_urgent": true, "recommendation": "check_urgent", ...}
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.get(f"{GATEWAY_URL}/api/agent/inbox")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "pending_count": 0, "events": []}


async def agent_rest(
    reason: str,
    wake_triggers: Optional[List[Dict[str, Any]]] = None,
    handoff_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Voluntarily enter rest state and set wake-up conditions.
    
    Use this when:
    - Waiting for user input or confirmation
    - Waiting for a specific time
    - No more tasks to process
    - Current task requires external action
    
    Args:
        reason: Why you are resting (displayed to user)
        wake_triggers: List of conditions that will wake you up:
            - {"type": "user_response"} - Wake when user sends any message
            - {"type": "user_message", "pattern": "..."} - Wake on matching message
            - {"type": "cron", "expr": "*/10 * * * *"} - Wake on schedule
            - {"type": "keyword", "pattern": "urgent|紧急"} - Wake on keyword
            - {"type": "timeout", "minutes": 30} - Wake after timeout
        handoff_notes: Notes about current state for when you wake up
    
    Returns:
        Dictionary with:
        - success: Whether rest was initiated
        - state: New agent state ("resting")
        - triggers_set: Number of wake triggers configured
        - estimated_wake: Estimated next wake time (if deterministic)
    
    Examples:
        # Rest until user responds
        agent_rest(
            reason="等待用户确认",
            wake_triggers=[{"type": "user_response"}],
            handoff_notes="已询问用户是否继续"
        )
        
        # Rest with timeout
        agent_rest(
            reason="等待部署完成",
            wake_triggers=[
                {"type": "timeout", "minutes": 10},
                {"type": "keyword", "pattern": "deployed|完成"}
            ],
            handoff_notes="部署脚本已启动"
        )
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/agent/rest",
                json={
                    "reason": reason,
                    "wake_triggers": wake_triggers or [{"type": "user_response"}],
                    "handoff_notes": handoff_notes
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "success": False}
