"""
Context Stack — Recall Tool Router

Fix #3: Closes the tool routing gap.

The problem: Engine gives tool definitions to the AgentExecutor,
but the host must manually intercept memory_expand/memory_search
calls and route them to engine.handle_recall_tool(). 

Solution: RecallToolRouter wraps an AgentExecutor and intercepts
recall tool calls transparently. The host just wraps its executor
once and forgets about routing.

Usage:
    engine = ContextEngine(executor=my_executor, ...)
    # The engine automatically wraps the executor during recall
    # OR: manually wrap for custom tool dispatch
    router = RecallToolRouter(my_executor, engine.recall)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .context.types import Message, MessageRole
from .skill.builtins.recall import RecallSkill

logger = logging.getLogger("context_stack.tool_router")

RECALL_TOOL_NAMES = frozenset({"memory_expand", "memory_search"})


class RecallToolRouter:
    """
    Wraps an AgentExecutor to intercept recall tool calls.
    
    When the agent calls memory_expand or memory_search, this router
    executes them via RecallSkill and injects the results as TOOL messages
    back into the conversation — then lets the agent continue.
    
    The host's AgentExecutor doesn't need to know about recall tools at all.
    """

    def __init__(self, executor, recall_skill: RecallSkill):
        """
        Args:
            executor: the host's AgentExecutor (implements execute())
            recall_skill: RecallSkill instance (from engine.recall)
        """
        self._executor = executor
        self._recall = recall_skill

    def execute(
        self,
        messages: List[Message],
        extra_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Message]:
        """
        Execute the agent loop with recall tool interception.
        
        Delegates to the wrapped executor, but if the executor returns
        messages containing recall tool calls, intercepts and resolves them.
        """
        result = self._executor.execute(
            messages=messages,
            extra_tools=extra_tools,
        )
        
        # Resolve any pending recall tool calls
        result = self._resolve_recall_calls(result)
        return result

    def _resolve_recall_calls(self, messages: List[Message]) -> List[Message]:
        """
        Scan messages for unresolved recall tool calls and resolve them.
        
        A recall tool call is an ASSISTANT message with tool_name in RECALL_TOOL_NAMES
        that is NOT followed by a corresponding TOOL response.
        """
        resolved = list(messages)
        i = 0
        injected = 0
        
        while i < len(resolved):
            msg = resolved[i]
            
            # Check if this is a recall tool call from assistant
            if (msg.role == MessageRole.ASSISTANT
                and msg.tool_name in RECALL_TOOL_NAMES):
                
                # Check if next message is already a TOOL response for it
                has_response = (
                    i + 1 < len(resolved)
                    and resolved[i + 1].role == MessageRole.TOOL
                    and resolved[i + 1].tool_name == msg.tool_name
                )
                
                if not has_response:
                    # Resolve the tool call
                    import json
                    try:
                        args = json.loads(msg.tool_input or "{}")
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    
                    result = self._recall.execute_tool(msg.tool_name, args)
                    
                    tool_response = Message(
                        role=MessageRole.TOOL,
                        content=result,
                        tool_name=msg.tool_name,
                        metadata={"recall_routed": True},
                    )
                    
                    # Insert the response right after the call
                    resolved.insert(i + 1, tool_response)
                    injected += 1
                    logger.debug(
                        "Routed recall tool: %s → %d chars",
                        msg.tool_name, len(result),
                    )
            i += 1
        
        if injected:
            logger.info("RecallToolRouter: resolved %d recall tool calls", injected)
        
        return resolved
