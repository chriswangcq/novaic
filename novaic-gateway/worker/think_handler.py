"""
Think Handler

Handles "think" tasks for the Worker in Master-driven architecture.
Receives context from Master, calls LLM, returns actions.

v12: Created for Master-driven architecture.
Worker is truly stateless - just executes single think task and returns.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

import aiohttp

from .llm_caller import LLMCaller, ActionType, DEFAULT_SYSTEM_PROMPT

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def handle_think(task: Dict[str, Any], gateway_url: str = "http://localhost:9527") -> Dict[str, Any]:
    """
    Handle a "think" task from Master.
    
    This is a truly stateless operation:
    1. Receive context from task args
    2. Call LLM with context
    3. Return actions (Master will handle creating action_tasks)
    
    Args:
        task: Task data including:
            - id: Task ID
            - agent_id: Agent ID
            - subagent_id: Runtime ID
            - round_id: Current round
            - args: {context: [...]}
        gateway_url: Gateway URL for API calls
    
    Returns:
        Dict with actions list for Master to process
    """
    task_id = task.get("id")
    agent_id = task.get("agent_id")
    subagent_id = task.get("subagent_id")
    round_id = task.get("round_id")
    
    # Get context and MCP URL from task args
    args = task.get("args", {})
    if isinstance(args, str):
        args = json.loads(args)
    context = args.get("context", [])
    mcp_url = args.get("mcp_url")  # Runtime MCP URL
    
    print(f"[ThinkHandler] Processing think task {task_id}")
    print(f"[ThinkHandler] Agent: {agent_id}, Runtime: {subagent_id}, Round: {round_id}")
    print(f"[ThinkHandler] Context has {len(context)} messages")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get LLM configuration
            llm_config = await _get_llm_config(gateway_url, session)
            
            # Extract model settings
            model = llm_config.get("model", "gpt-4o")
            api_keys = llm_config.get("api_keys", [])
            
            if not api_keys:
                print(f"[ThinkHandler] No API keys available")
                return {
                    "success": False,
                    "error": "No API keys configured",
                    "actions": [],
                }
            
            # Use first available API key
            key_info = api_keys[0]
            api_key = key_info.get("api_key")
            api_base = key_info.get("api_base")
            provider = key_info.get("provider")
            
            # Initialize LLM caller
            llm = LLMCaller(
                gateway_url=gateway_url,
                session=session,
                agent_id=agent_id,
            )
            await llm.initialize(
                model=model,
                api_key=api_key,
                api_base=api_base,
                provider=provider,
                mcp_url=mcp_url,  # Pass Runtime MCP URL
            )
            
            # Set system prompt
            llm.set_system_prompt(DEFAULT_SYSTEM_PROMPT)
            
            # Add context messages to LLM
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    llm.add_user_message(content)
                elif role == "assistant":
                    # v12: assistant 消息可能包含 tool_calls
                    tool_calls = msg.get("tool_calls")
                    if tool_calls:
                        # 添加带 tool_calls 的 assistant 消息
                        llm.messages.append({
                            "role": "assistant",
                            "content": content or "",
                            "tool_calls": tool_calls,
                        })
                    else:
                        llm.add_assistant_message(content)
                elif role == "tool_result":
                    # Tool results are added differently
                    # v12: 使用 tool_call_id，不要 fallback 到 task_id
                    # task_id 是内部 ID，LLM 不认识，会报错 "tool_call_id is not found"
                    tool_call_id = msg.get("tool_call_id") or ''
                    tool_name = msg.get("tool_name", "tool")
                    if tool_call_id:  # 只有有 tool_call_id 时才添加
                        llm.add_tool_result(tool_name, tool_call_id, content)
                elif role == "system":
                    # System messages go into context as user
                    llm.add_user_message(f"[System] {content}")
            
            # Broadcast thinking status (start)
            await _broadcast_log(gateway_url, session, agent_id, {
                "type": "status",
                "timestamp": datetime.now().isoformat(),
                "data": {"message": f"🧠 Thinking (round {round_id})..."},
            })
            
            # Call LLM to think
            thinking_result = await llm.think()
            
            print(f"[ThinkHandler] LLM returned {len(thinking_result.actions)} actions")
            if thinking_result.reasoning:
                print(f"[ThinkHandler] Reasoning: {thinking_result.reasoning[:200]}...")
            
            # Broadcast reasoning (if available)
            if thinking_result.reasoning:
                await _broadcast_log(gateway_url, session, agent_id, {
                    "type": "thinking",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"content": thinking_result.reasoning},
                })
            
            # Convert actions to serializable format for Master
            actions = []
            for action in thinking_result.actions:
                action_dict = {
                    "type": action.type.value if hasattr(action.type, 'value') else str(action.type),
                }
                
                # v2.8: 所有操作都是 TOOL_CALL 或 DONE
                if action.type == ActionType.TOOL_CALL:
                    action_dict["tool"] = action.tool_name
                    action_dict["args"] = action.args or {}
                    # v12: 传递 tool_call_id，用于返回结果时匹配
                    if action.tool_call_id:
                        action_dict["tool_call_id"] = action.tool_call_id
                    
                    # Broadcast tool intent
                    await _broadcast_log(gateway_url, session, agent_id, {
                        "type": "tool_start",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "tool": action.tool_name,
                            "args": action.args,
                        },
                    })
                    
                elif action.type == ActionType.DONE:
                    pass  # Just the type is enough
                
                actions.append(action_dict)
            
            # v2.8: 如果是 Main Agent 且有 final_answer，创建 chat_reply 工具调用
            # SubAgent 的 final_answer 会作为结果返回给父 Agent
            is_main_agent = subagent_id and subagent_id.startswith("main-")
            if thinking_result.final_answer and is_main_agent:
                # 插入 chat_reply 到 done 之前
                # v13: 生成 tool_call_id，因为 LLM 返回纯文本时没有 tool_calls
                import uuid
                chat_reply_tool_call_id = f"call_{uuid.uuid4().hex[:24]}"
                chat_reply_action = {
                    "type": "tool_call",
                    "tool": "chat_reply",
                    "args": {"message": thinking_result.final_answer},
                    "tool_call_id": chat_reply_tool_call_id,  # v13: 手动生成的 tool_call_id
                }
                # 找到 done action 的位置，插入之前
                done_idx = next((i for i, a in enumerate(actions) if a.get("type") == "done"), len(actions))
                actions.insert(done_idx, chat_reply_action)
                
                # Broadcast chat_reply intent
                await _broadcast_log(gateway_url, session, agent_id, {
                    "type": "tool_start",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "tool": "chat_reply",
                        "args": {"message": thinking_result.final_answer[:100] + "..."},
                    },
                })
            
            return {
                "success": True,
                "actions": actions,
                "reasoning": thinking_result.reasoning,
                "is_final": thinking_result.is_final,
                "final_answer": thinking_result.final_answer,  # 给 SubAgent 的父 Agent 用
            }
            
        except Exception as e:
            print(f"[ThinkHandler] Error processing think task {task_id}: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "actions": [],
            }


async def _get_llm_config(gateway_url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Get LLM configuration from Gateway (internal API with full API keys)."""
    try:
        # Use internal API to get full config including API keys
        async with session.get(f"{gateway_url}/api/config/internal") as response:
            if response.status == 200:
                config = await response.json()
                return {
                    "model": config.get("default_model"),
                    "api_keys": config.get("api_keys", []),
                }
    except Exception as e:
        print(f"[ThinkHandler] Get LLM config error: {e}")
    return {}


async def _broadcast_log(
    gateway_url: str, 
    session: aiohttp.ClientSession, 
    agent_id: str, 
    log_data: Dict[str, Any]
):
    """Broadcast execution log to Gateway for UI display."""
    try:
        await session.post(
            f"{gateway_url}/api/logs/broadcast",
            json={
                "agent_id": agent_id,
                **log_data,
            },
        )
    except Exception:
        pass  # Non-critical


__all__ = ["handle_think"]
