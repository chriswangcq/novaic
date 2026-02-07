"""
Broadcast Utils - 事件广播工具

用于向前端广播执行状态和日志。

支持的广播类型：
- status: 状态更新（如 "🧠 Thinking..."）
- thinking: 推理过程
- tool_start: 工具开始执行
- tool_end: 工具执行完成
- error: 错误信息
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Protocol


class BroadcastType(str, Enum):
    """广播消息类型"""
    STATUS = "status"           # 状态更新
    THINKING = "thinking"       # 推理过程
    TOOL_START = "tool_start"   # 工具开始
    TOOL_END = "tool_end"       # 工具结束
    ERROR = "error"             # 错误信息
    INFO = "info"               # 普通信息


class Broadcaster(Protocol):
    """广播器协议 - 定义广播接口"""
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """广播消息"""
        ...


async def broadcast_log(
    ctx: dict,
    agent_id: str,
    log_type: BroadcastType | str,
    data: Dict[str, Any],
    *,
    broadcaster_key: str = "broadcaster",
) -> bool:
    """
    广播日志到前端
    
    Args:
        ctx: 上下文（包含 broadcaster）
        agent_id: Agent ID
        log_type: 日志类型
        data: 日志数据
        broadcaster_key: ctx 中 broadcaster 的键名
        
    Returns:
        是否广播成功
        
    Example:
        >>> from task_queue.utils import broadcast_log, BroadcastType
        >>> await broadcast_log(ctx, "agent-123", BroadcastType.STATUS, {
        ...     "message": "🧠 Thinking..."
        ... })
        True
    """
    broadcaster = ctx.get(broadcaster_key)
    if not broadcaster:
        return False
    
    # 处理枚举类型
    if isinstance(log_type, BroadcastType):
        log_type = log_type.value
    
    try:
        await broadcaster.broadcast({
            "agent_id": agent_id,
            "type": log_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        })
        return True
    except Exception:
        return False  # 广播失败不影响主流程


# ==================== 便捷方法 ====================

async def broadcast_status(ctx: dict, agent_id: str, message: str) -> bool:
    """广播状态更新"""
    return await broadcast_log(ctx, agent_id, BroadcastType.STATUS, {"message": message})


async def broadcast_thinking(ctx: dict, agent_id: str, content: str, *, max_length: int = 500) -> bool:
    """广播推理过程"""
    if len(content) > max_length:
        content = content[:max_length] + "..."
    return await broadcast_log(ctx, agent_id, BroadcastType.THINKING, {"content": content})


async def broadcast_tool_start(ctx: dict, agent_id: str, tool: str, args: Dict[str, Any]) -> bool:
    """广播工具开始执行"""
    return await broadcast_log(ctx, agent_id, BroadcastType.TOOL_START, {
        "tool": tool,
        "args": args,
    })


async def broadcast_tool_end(
    ctx: dict, 
    agent_id: str, 
    tool: str, 
    success: bool, 
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """广播工具执行完成"""
    data = {"tool": tool, "success": success}
    if result:
        data["result"] = result
    if error:
        data["error"] = error[:100]
    return await broadcast_log(ctx, agent_id, BroadcastType.TOOL_END, data)


async def broadcast_error(ctx: dict, agent_id: str, message: str, *, max_length: int = 200) -> bool:
    """广播错误信息"""
    if len(message) > max_length:
        message = message[:max_length] + "..."
    return await broadcast_log(ctx, agent_id, BroadcastType.ERROR, {"message": message})


# ==================== 同步广播（供 Task Worker 同步调用） ====================

def sync_broadcast_log(
    ctx: dict,
    agent_id: str,
    log_type: BroadcastType | str = None,
    data: Dict[str, Any] = None,
    *,
    gateway_client_key: str = "gateway_client",
    subagent_id: str = "main",
    kind: str = None,
    status: str = "complete",
    event_key: str = None,
    input_data: Dict[str, Any] = None,
    result_data: Dict[str, Any] = None,
) -> bool:
    """
    同步向 Gateway 发送执行日志（POST /api/logs/broadcast）。
    Task Worker 为同步进程，ctx 中没有 broadcaster，需通过 gateway_client 直接 POST。
    
    Args:
        ctx: 上下文（包含 gateway_client）
        agent_id: Agent ID
        log_type: 日志类型（保留兼容）
        data: 日志数据（保留兼容）
        gateway_client_key: ctx 中 gateway_client 的键名
        subagent_id: SubAgent ID，默认 "main"
        kind: 事件类型（think/tool/message 等）
        status: 状态（running/complete）
        event_key: 事件唯一标识
        input_data: 输入数据
        result_data: 结果数据
    """
    client = ctx.get(gateway_client_key)
    if not client or not getattr(client, "broadcast_log", None):
        return False
    if isinstance(log_type, BroadcastType):
        log_type = log_type.value
    try:
        result = client.broadcast_log(
            agent_id=agent_id,
            log_type=log_type,
            data=data,
            subagent_id=subagent_id,
            kind=kind,
            status=status,
            event_key=event_key,
            input_data=input_data,
            result_data=result_data,
        )
        # 打印日志（限制长度避免大图片卡死）
        result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        print(f"[broadcast] sync_broadcast_log: agent={agent_id}, kind={kind}, status={status}, result={result_preview}")
        return result
    except Exception as e:
        import traceback
        print(f"[broadcast] ERROR sync_broadcast_log: agent={agent_id}, kind={kind}, status={status}, error={e}")
        traceback.print_exc()
        return False
