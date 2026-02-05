"""
Tool Handlers - 工具执行

Topics:
- tool.execute: 执行工具

使用：
- task_queue.business.MCPBusiness 业务逻辑层
- task_queue.utils 广播和结果处理

v2 变更：
- need_rest 由 MCP 工具内部设置（runtime_rest 工具）
- done/final 等工具在 ReactThink 阶段被转换为 runtime_rest
"""

import json
from typing import Dict, Any
from . import register_handler
from ..business import MCPBusiness
from ..utils import sync_broadcast_log, BroadcastType


@register_handler("tool.execute")
def handle_tool_execute(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    执行工具
    
    功能：
    1. 执行 MCP 工具
    2. done/reset 执行时设置 runtime status=resting (v2)
    3. 广播 tool 事件到前端（执行前 running，执行后 complete）
    
    幂等性：工具本身负责保证幂等性
    
    Payload:
        runtime_id: str
        round_id: str
        tool_call_id: str
        tool_name: str
        arguments: str | dict
        agent_id: str (可选，用于广播)
    """
    runtime_id = payload["runtime_id"]
    round_id = payload["round_id"]
    tool_call_id = payload["tool_call_id"]
    tool_name = payload["tool_name"]
    arguments = payload["arguments"]
    agent_id = payload.get("agent_id")
    subagent_id = "main"
    
    # 解析 arguments
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            pass
    
    # 如果没有 agent_id，从 runtime 获取
    from ..client import GatewayInternalClient
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    if not agent_id:
        runtime = client.get_runtime(runtime_id)
        if runtime:
            agent_id = runtime.get("agent_id")
            subagent_id = runtime.get("subagent_id", "main")
    else:
        # 即使有 agent_id，也尝试获取 subagent_id
        runtime = client.get_runtime(runtime_id)
        if runtime:
            subagent_id = runtime.get("subagent_id", "main")
    
    # 事件标识
    tool_event_key = f"tool:{runtime_id}:{tool_call_id}"
    
    # 广播 tool running 事件（执行前）
    if agent_id:
        sync_broadcast_log(
            ctx,
            agent_id,
            subagent_id=subagent_id,
            kind="tool",
            status="running",
            event_key=tool_event_key,
            data={"type": "tool"},
            input_data={"tool": tool_name, "args": arguments},
        )
    
    # 使用业务逻辑层执行工具
    # 注：need_rest 由 MCP runtime_reset 工具内部设置
    biz = MCPBusiness(
        gateway_url=ctx["gateway_url"],
        client=ctx.get("gateway_client"),
    )
    
    result = biz.execute_tool(
        runtime_id=runtime_id,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
        arguments=arguments,
    )
    
    # 广播 tool complete 事件（执行后）
    if agent_id:
        if result.success:
            sync_broadcast_log(
                ctx,
                agent_id,
                subagent_id=subagent_id,
                kind="tool",
                status="complete",
                event_key=tool_event_key,
                data={"type": "tool"},
                result_data={"result": result.result},
            )
        else:
            sync_broadcast_log(
                ctx,
                agent_id,
                subagent_id=subagent_id,
                kind="tool",
                status="complete",
                event_key=tool_event_key,
                data={"type": "tool"},
                result_data={"error": result.error if result.error else "Unknown error"},
            )
    
    # 返回结果
    return {
        "success": result.success,
        "status": result.status,
        "runtime_id": runtime_id,
        "round_id": round_id,
        "tool_call_id": result.tool_call_id,
        "tool_name": result.tool_name,
        "result": result.result,
        "error": result.error if result.error else None,
    }
