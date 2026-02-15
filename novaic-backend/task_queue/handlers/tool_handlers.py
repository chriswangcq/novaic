"""
Tool Handlers - 工具执行

Topics:
- tool.execute: 执行工具

使用：
- task_queue.business.MCPBusiness 业务逻辑层
- task_queue.utils 广播和结果处理

v2 变更：
- need_rest 由 MCP 工具内部设置（runtime_rest 工具）
- done/final 等工具在 ReactThink 阶段被转换为 runtime_complete
"""

import json
from typing import Dict, Any
from . import register_handler
from ..business import MCPBusiness
from ..utils import sync_broadcast_log, BroadcastType
from ..topics import TaskTopics
from common.exceptions import ValidationError


@register_handler(TaskTopics.TOOL_EXECUTE)
def handle_tool_execute(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    执行工具
    
    功能：
    1. 执行 MCP 工具
    2. 广播 tool 事件到前端（执行前 running，执行后 complete）
    
    幂等性：工具本身负责保证幂等性
    
    Payload:
        runtime_id: str
        round_id: str
        tool_call_id: str
        tool_name: str
        arguments: str | dict
        agent_id: str (可选，用于广播)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    if not payload.get("round_id"):
        raise ValidationError("Missing required field: round_id")
    if not payload.get("tool_call_id"):
        raise ValidationError("Missing required field: tool_call_id")
    if not payload.get("tool_name"):
        raise ValidationError("Missing required field: tool_name")
    
    runtime_id = payload["runtime_id"]
    round_id = payload["round_id"]
    tool_call_id = payload["tool_call_id"]
    tool_name = payload["tool_name"]
    arguments = payload.get("arguments", {})
    
    # ✅ 修改：优先从 payload 获取
    agent_id = payload.get("agent_id")
    subagent_id = payload.get("subagent_id")  # 优先从 payload 获取
    
    # 解析 arguments
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            pass
    
    # 如果 payload 中没有，从 runtime 获取（兼容旧逻辑）
    if not subagent_id or not agent_id:
        from ..client import GatewayInternalClient
        import logging
        
        gateway_url = ctx.get("gateway_url")
        client = ctx.get("gateway_client") or GatewayInternalClient(gateway_url)
        
        try:
            runtime = client.get_runtime(runtime_id)
            if not runtime:
                logging.warning(
                    f"[tool_handlers] Runtime not found: {runtime_id}, "
                    f"using defaults (agent_id={agent_id}, subagent_id={subagent_id or 'main'})"
                )
                subagent_id = subagent_id or "main"
            else:
                if not subagent_id:
                    subagent_id = runtime.get("subagent_id", "main")
                if not agent_id:
                    agent_id = runtime.get("agent_id")
        except Exception as e:
            logging.error(
                f"[tool_handlers] Failed to get runtime {runtime_id}: {e}, "
                f"using defaults (agent_id={agent_id}, subagent_id={subagent_id or 'main'})"
            )
            subagent_id = subagent_id or "main"
    else:
        # Payload 中已有完整信息，记录日志（可选）
        import logging
        logging.debug(f"[tool_handlers] Using subagent_id from payload: {subagent_id}")
    
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
    # 必须成功且有 result_id
    if agent_id:
        if result.success and result.result_id:
            sync_broadcast_log(
                ctx,
                agent_id,
                subagent_id=subagent_id,
                kind="tool",
                status="complete",
                event_key=tool_event_key,
                data={"type": "tool"},
                result_data={"result_id": result.result_id},
            )
        else:
            error_msg = result.error if result.error else "Tool execution failed or no result_id"
            sync_broadcast_log(
                ctx,
                agent_id,
                subagent_id=subagent_id,
                kind="tool",
                status="complete",
                event_key=tool_event_key,
                data={"type": "tool"},
                result_data={"error": error_msg},
            )
    
    # 返回结果（只返回 result_id）
    return {
        "success": result.success,
        "status": result.status,
        "runtime_id": runtime_id,
        "round_id": round_id,
        "tool_call_id": result.tool_call_id,
        "tool_name": result.tool_name,
        "result_id": result.result_id if result.success else None,
        "error": result.error if result.error else None,
    }
