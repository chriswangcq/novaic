"""
NovAIC Gateway SDK

Python SDK for NovAIC services to interact with Gateway API.
All database operations go through Gateway API instead of direct DB access.

Usage:
    from sdk import GatewaySDK
    
    async with GatewaySDK() as sdk:
        # Pipeline tasks
        task = await sdk.pipeline.claim_task(["launcher"])
        await sdk.pipeline.mark_done(task_id, result)
        
        # Runtime
        runtime = await sdk.runtime.get(runtime_id)
        await sdk.runtime.update(runtime_id, status="completed")
        
        # SubAgent
        subagent = await sdk.subagent.get_main(agent_id)
        await sdk.subagent.set_sleeping(agent_id, subagent_id)
        
        # Messages
        messages = await sdk.messages.get_unread(agent_id)
        await sdk.messages.mark_processed(message_ids)
        
        # MCP
        await sdk.mcp.create_aggregate(agent_id, runtime_id)
        
        # LLM
        result = await sdk.llm.compact_context(agent_id, messages)
"""

from .client import GatewaySDK
from .pipeline import PipelineAPI
from .runtime import RuntimeAPI
from .subagent import SubAgentAPI
from .messages import MessagesAPI
from .mcp import McpAPI
from .llm import LlmAPI
from .exceptions import (
    GatewayError,
    GatewayConnectionError,
    GatewayTimeoutError,
    GatewayNotFoundError,
    GatewayConflictError,
)

__all__ = [
    "GatewaySDK",
    "PipelineAPI",
    "RuntimeAPI",
    "SubAgentAPI",
    "MessagesAPI",
    "McpAPI",
    "LlmAPI",
    "GatewayError",
    "GatewayConnectionError",
    "GatewayTimeoutError",
    "GatewayNotFoundError",
    "GatewayConflictError",
]
