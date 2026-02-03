"""
Task Handlers - 幂等的原子操作

每个 Handler 对应一个 Task topic，负责执行具体的业务逻辑。
所有 Handler 必须是幂等的，能够安全地重复执行。

Handler 接口：
    async def handler(payload: dict) -> dict

幂等实现方式：
- 数据库 INSERT: idempotency_key 唯一约束
- 数据库 UPDATE: CAS（状态检查 + 乐观锁）
- 外部服务: 先检查是否存在
"""

from typing import Dict, Any, Callable, Awaitable

# Handler 类型
HandlerFunc = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

# Handler 注册表
_handlers: Dict[str, HandlerFunc] = {}


def register_handler(topic: str):
    """装饰器：注册 Handler"""
    def decorator(func: HandlerFunc) -> HandlerFunc:
        _handlers[topic] = func
        return func
    return decorator


def get_handler(topic: str) -> HandlerFunc:
    """获取 Handler"""
    handler = _handlers.get(topic)
    if not handler:
        raise ValueError(f"No handler registered for topic: {topic}")
    return handler


def get_all_topics() -> list:
    """获取所有已注册的 topic"""
    return list(_handlers.keys())


# 导入所有 handlers 以触发注册
from . import subagent_handlers
from . import runtime_handlers
from . import mcp_handlers
from . import llm_handlers
from . import tool_handlers
from . import context_handlers
from . import message_handlers
from . import saga_handlers
