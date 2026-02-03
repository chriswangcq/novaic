"""
ThinkExecutor

Executes 'think' tasks by calling LLM.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, TYPE_CHECKING

import aiohttp

from ..executor_worker import BaseExecutor, ExecutorWorker
from .llm_caller import LLMCaller, ActionType, DEFAULT_SYSTEM_PROMPT

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


@ExecutorWorker.register("think")
class ThinkExecutor(BaseExecutor):
    """
    Executor for think tasks - calls LLM and returns actions.
    """
    
    async def execute(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> Any:
        """Execute think task."""
        context = args.get("context", [])
        mcp_url = args.get("mcp_url")
        subagent_type = args.get("subagent_type", "main")
        round_id = args.get("round_id", "round-1")
        
        # Get runtime info via Gateway API (REQUIRED)
        runtime = await self.client.get_runtime(runtime_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {runtime_id}")
        
        subagent_id = runtime.get("subagent_id")
        if not subagent_id:
            raise ValueError(f"subagent_id not found in Runtime {runtime_id}")
        
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {runtime_id}")
        
        # Sanitize context to fix incomplete tool_calls sequences
        context = _sanitize_context(context)
        
        print(f"[ThinkExecutor] Processing task {task.get('id')}")
        print(f"[ThinkExecutor] Agent: {actual_agent_id}, Runtime: {runtime_id}, Round: {round_id}")
        print(f"[ThinkExecutor] Context has {len(context)} messages")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Get LLM configuration
                llm_config = await _get_llm_config(self.gateway_url, session)
                
                model = llm_config.get("model", "gpt-4o")
                api_keys = llm_config.get("api_keys", [])
                
                if not api_keys:
                    print(f"[ThinkExecutor] No API keys available")
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
                    gateway_url=self.gateway_url,
                    session=session,
                    agent_id=actual_agent_id,
                )
                await llm.initialize(
                    model=model,
                    api_key=api_key,
                    api_base=api_base,
                    provider=provider,
                    mcp_url=mcp_url,
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
                        tool_calls = msg.get("tool_calls")
                        reasoning_content = msg.get("reasoning_content")
                        if tool_calls:
                            assistant_msg = {
                                "role": "assistant",
                                "content": content or "",
                                "tool_calls": tool_calls,
                            }
                            if reasoning_content:
                                assistant_msg["reasoning_content"] = reasoning_content
                            llm.messages.append(assistant_msg)
                        else:
                            llm.add_assistant_message(content)
                    elif role == "tool_result":
                        tool_call_id = msg.get("tool_call_id") or ''
                        tool_name = msg.get("tool_name", "tool")
                        if tool_call_id:
                            try:
                                result_data = json.loads(content) if isinstance(content, str) else content
                            except (json.JSONDecodeError, TypeError):
                                result_data = content
                            llm.add_tool_result(tool_name, tool_call_id, result_data)
                    elif role == "system":
                        llm.add_user_message(f"[System] {content}")
                
                # Broadcast thinking status
                await _broadcast_log(self.gateway_url, session, actual_agent_id, {
                    "type": "status",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"message": f"🧠 Thinking (round {round_id})..."},
                })
                
                # Call LLM
                thinking_result = await llm.think()
                
                print(f"[ThinkExecutor] LLM returned {len(thinking_result.actions)} actions")
                
                # Broadcast reasoning
                if thinking_result.reasoning:
                    await _broadcast_log(self.gateway_url, session, actual_agent_id, {
                        "type": "thinking",
                        "timestamp": datetime.now().isoformat(),
                        "data": {"content": thinking_result.reasoning},
                    })
                
                # Convert actions to serializable format
                actions = []
                for action in thinking_result.actions:
                    action_dict = {
                        "type": action.type.value if hasattr(action.type, 'value') else str(action.type),
                    }
                    
                    if action.type == ActionType.TOOL_CALL:
                        action_dict["tool"] = action.tool_name
                        action_dict["args"] = action.args or {}
                        if action.tool_call_id:
                            action_dict["tool_call_id"] = action.tool_call_id
                        
                        # Broadcast tool intent
                        await _broadcast_log(self.gateway_url, session, actual_agent_id, {
                            "type": "tool_start",
                            "timestamp": datetime.now().isoformat(),
                            "data": {
                                "tool": action.tool_name,
                                "args": action.args,
                            },
                        })
                    
                    actions.append(action_dict)
                
                # If main agent has final_answer, create chat_reply tool call
                is_main_agent = subagent_type == "main"
                if thinking_result.final_answer and is_main_agent:
                    chat_reply_tool_call_id = f"call_{uuid.uuid4().hex[:24]}"
                    chat_reply_action = {
                        "type": "tool_call",
                        "tool": "chat_reply",
                        "args": {"message": thinking_result.final_answer},
                        "tool_call_id": chat_reply_tool_call_id,
                    }
                    done_idx = next((i for i, a in enumerate(actions) if a.get("type") == "done"), len(actions))
                    actions.insert(done_idx, chat_reply_action)
                    
                    await _broadcast_log(self.gateway_url, session, actual_agent_id, {
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
                    "final_answer": thinking_result.final_answer,
                    "mcp_session_id": thinking_result.mcp_session_id,
                }
                
            except Exception as e:
                print(f"[ThinkExecutor] Error: {e}")
                import traceback
                traceback.print_exc()
                
                return {
                    "success": False,
                    "error": str(e),
                    "actions": [],
                }


@ExecutorWorker.register("summarize")
class SummarizeExecutor(BaseExecutor):
    """
    Executor for summarize tasks - generates LLM summary.
    """
    
    async def execute(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> Any:
        """Execute summarize task."""
        context = args.get("context", [])
        
        # Filter out injected history for summarization
        new_messages = [
            msg for msg in context
            if not msg.get('metadata', {}).get('type') in 
               ('historical_summary', 'runtime_summary', 'compaction_summary')
        ]
        
        if not new_messages:
            return {"summary": ""}
        
        # Build summary prompt
        summary_prompt = self._build_summary_prompt(new_messages)
        
        # Call Gateway API for LLM
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.gateway_url}/internal/llm/generate",
                    json={
                        "prompt": summary_prompt,
                        "agent_id": agent_id,
                        "max_tokens": 500,
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        summary = data.get("content", "")
                        return {"summary": summary}
                    else:
                        return {"summary": self._simple_summary(new_messages)}
                        
            except Exception as e:
                print(f"[SummarizeExecutor] LLM call failed: {e}")
                return {"summary": self._simple_summary(new_messages)}
    
    def _build_summary_prompt(self, messages: list) -> str:
        """Build prompt for summary generation."""
        parts = []
        
        for msg in messages[-20:]:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'user':
                parts.append(f"User: {content[:500]}")
            elif role == 'assistant':
                tool_calls = msg.get('tool_calls', [])
                for tc in tool_calls:
                    func = tc.get('function', {})
                    name = func.get('name', '')
                    parts.append(f"Agent called: {name}")
                if not tool_calls and content:
                    parts.append(f"Agent: {content[:500]}")
            elif role == 'tool_result':
                parts.append(f"Tool result received")
        
        conversation = "\n".join(parts)
        
        return f"""Summarize this conversation in 2-3 sentences. Focus on:
1. What the user wanted
2. What actions the agent took
3. The outcome

Conversation:
{conversation}

Summary:"""
    
    def _simple_summary(self, messages: list) -> str:
        """Generate simple summary without LLM."""
        parts = []
        
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'user' and content:
                text = content[:100]
                parts.append(f"User: {text}...")
                break
        
        tool_names = set()
        for msg in messages:
            if msg.get('role') == 'assistant':
                for tc in msg.get('tool_calls', []):
                    name = tc.get('function', {}).get('name', '')
                    if name and name not in ('runtime_rest', 'runtime_complete'):
                        tool_names.add(name)
        
        if tool_names:
            parts.append(f"Tools used: {', '.join(list(tool_names)[:5])}")
        
        return " | ".join(parts) if parts else ""


# ==================== Helper Functions ====================

async def _get_llm_config(gateway_url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Get LLM configuration from Gateway."""
    try:
        async with session.get(f"{gateway_url}/api/config/internal") as response:
            if response.status == 200:
                config = await response.json()
                return {
                    "model": config.get("default_model"),
                    "api_keys": config.get("api_keys", []),
                }
    except Exception as e:
        print(f"[ThinkExecutor] Get LLM config error: {e}")
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


def _sanitize_context(context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize context to fix incomplete tool_calls sequences.
    
    Ensures tool_results immediately follow their assistant+tool_calls.
    """
    if not context:
        return context
    
    # First pass: collect all messages and track tool_calls
    assistant_tool_calls = {}  # tc_id -> {"assistant_idx": int, "name": str}
    tool_results = {}  # tc_id -> msg
    other_messages = []  # (original_idx, msg)
    assistant_messages_with_tools = {}  # idx -> msg
    
    for idx, msg in enumerate(context):
        role = msg.get("role")
        
        if role == "assistant" and msg.get("tool_calls"):
            assistant_messages_with_tools[idx] = msg
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id")
                if tc_id:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "unknown")
                    assistant_tool_calls[tc_id] = {"assistant_idx": idx, "name": tool_name}
                    
        elif role == "tool_result":
            tc_id = msg.get("tool_call_id")
            if tc_id and tc_id in assistant_tool_calls:
                tool_results[tc_id] = msg
            elif tc_id:
                print(f"[ThinkExecutor] Removing orphan tool_result with call_id {tc_id}")
            else:
                other_messages.append((idx, msg))
        else:
            other_messages.append((idx, msg))
    
    # Second pass: build result with correct ordering
    result = []
    processed_assistant_indices = set()
    
    for orig_idx, msg in other_messages:
        for asst_idx in sorted(assistant_messages_with_tools.keys()):
            if asst_idx < orig_idx and asst_idx not in processed_assistant_indices:
                asst_msg = assistant_messages_with_tools[asst_idx]
                result.append(asst_msg)
                processed_assistant_indices.add(asst_idx)
                
                for tc in asst_msg.get("tool_calls", []):
                    tc_id = tc.get("id")
                    if tc_id:
                        if tc_id in tool_results:
                            result.append(tool_results[tc_id])
                        else:
                            func = tc.get("function", {})
                            tool_name = func.get("name", "unknown")
                            result.append({
                                "role": "tool_result",
                                "tool_call_id": tc_id,
                                "tool_name": tool_name,
                                "content": "[Execution was interrupted. Please retry if needed.]"
                            })
                            print(f"[ThinkExecutor] Added placeholder for tool_call {tc_id}")
        
        result.append(msg)
    
    # Add any remaining assistant+tool_results at the end
    for asst_idx in sorted(assistant_messages_with_tools.keys()):
        if asst_idx not in processed_assistant_indices:
            asst_msg = assistant_messages_with_tools[asst_idx]
            result.append(asst_msg)
            
            for tc in asst_msg.get("tool_calls", []):
                tc_id = tc.get("id")
                if tc_id:
                    if tc_id in tool_results:
                        result.append(tool_results[tc_id])
                    else:
                        func = tc.get("function", {})
                        tool_name = func.get("name", "unknown")
                        result.append({
                            "role": "tool_result",
                            "tool_call_id": tc_id,
                            "tool_name": tool_name,
                            "content": "[Execution was interrupted. Please retry if needed.]"
                        })
                        print(f"[ThinkExecutor] Added placeholder for tool_call {tc_id}")
    
    return result
