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


def validate_topic_registration():
    """验证所有 handler 注册的 topic 与常量定义的一致性
    
    在启动时调用，检查是否有 topic 常量遗漏或未使用。
    
    Returns:
        dict: 验证结果
        - valid: bool - 是否一致
        - missing_in_constants: list - 已注册但未定义常量的 topics
        - unused_constants: list - 已定义常量但未注册的 topics
    """
    from ..topics import validate_topics
    
    registered_topics = set(_handlers.keys())
    validation = validate_topics(registered_topics)
    
    # 打印验证结果
    if validation["missing_in_constants"]:
        print(f"[WARNING] Topics registered but missing in constants: {validation['missing_in_constants']}")
    
    if validation["unused_constants"]:
        print(f"[INFO] Topic constants defined but not registered: {validation['unused_constants']}")
    
    is_valid = len(validation["missing_in_constants"]) == 0
    
    return {
        "valid": is_valid,
        **validation,
    }


# 导入所有 handlers 以触发注册
from . import subagent_handlers
from . import runtime_handlers
from . import mcp_handlers
from . import llm_handlers
from . import tool_handlers
from . import context_handlers
from . import message_handlers
from . import saga_handlers
from . import summary_handlers  # v24: History Merge handlers
