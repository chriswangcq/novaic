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
