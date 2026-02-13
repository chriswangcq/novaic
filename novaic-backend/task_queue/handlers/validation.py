"""
Payload 验证模块

提供统一的 payload 验证机制：
1. validate_payload 装饰器 - 使用 Pydantic 模型验证
2. 基础验证函数 - 用于 Worker 层的通用验证

使用示例：

    from pydantic import BaseModel
    from task_queue.handlers.validation import validate_payload

    class MyPayload(BaseModel):
        agent_id: str
        subagent_id: str
        runtime_id: str

    @register_handler("my.topic")
    @validate_payload(MyPayload)
    def handle_my_topic(payload: dict, ctx: dict) -> dict:
        # payload 已经过验证，可以安全使用
        agent_id = payload["agent_id"]
        ...
"""

from functools import wraps
from typing import Type, Dict, Any, Optional

from pydantic import BaseModel, ValidationError

from task_queue.exceptions import PayloadValidationError, BusinessError


def validate_payload(model: Type[BaseModel]):
    """
    Payload 验证装饰器
    
    使用 Pydantic 模型验证 payload，验证失败抛出 PayloadValidationError。
    
    Args:
        model: Pydantic BaseModel 子类，定义 payload 的结构
    
    Returns:
        装饰器函数
    
    Example:
        class StartRuntimePayload(BaseModel):
            agent_id: str
            subagent_id: str
            runtime_id: str
            
        @register_handler("runtime.start")
        @validate_payload(StartRuntimePayload)
        def handle_runtime_start(payload: dict, ctx: dict) -> dict:
            # payload 已验证，字段一定存在
            agent_id = payload["agent_id"]
            ...
    """
    def decorator(handler):
        @wraps(handler)
        def wrapper(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
            # 基础检查
            if payload is None:
                raise PayloadValidationError(
                    "Payload is required",
                    details={"expected_model": model.__name__}
                )
            
            if not isinstance(payload, dict):
                raise PayloadValidationError(
                    f"Payload must be a dict, got {type(payload).__name__}",
                    details={"expected_model": model.__name__, "actual_type": type(payload).__name__}
                )
            
            # Pydantic 验证
            try:
                validated = model(**payload)
                # 转回 dict 传给 handler（保持接口一致）
                return handler(validated.model_dump(), ctx)
            except ValidationError as e:
                # 提取详细错误信息
                errors = e.errors()
                error_messages = []
                for err in errors:
                    loc = ".".join(str(x) for x in err["loc"])
                    msg = err["msg"]
                    error_messages.append(f"{loc}: {msg}")
                
                raise PayloadValidationError(
                    f"Invalid payload: {'; '.join(error_messages)}",
                    details={
                        "expected_model": model.__name__,
                        "validation_errors": errors,
                    }
                )
        
        return wrapper
    return decorator


def validate_basic_payload(payload: Any, topic: str) -> Dict[str, Any]:
    """
    基础 payload 验证
    
    在 Worker 层调用，确保 payload 是有效的 dict。
    
    Args:
        payload: 原始 payload
        topic: 任务 topic（用于错误信息）
    
    Returns:
        验证后的 payload（如果是 None 则返回空 dict）
    
    Raises:
        BusinessError: 如果 payload 类型无效
    """
    if payload is None:
        return {}
    
    if not isinstance(payload, dict):
        raise BusinessError(
            f"Payload must be a dict, got {type(payload).__name__} (topic: {topic})"
        )
    
    return payload


def require_fields(payload: Dict[str, Any], *fields: str) -> None:
    """
    检查必需字段是否存在
    
    简单的字段存在性检查，适用于不想定义 Pydantic 模型的场景。
    
    Args:
        payload: payload dict
        *fields: 必需的字段名
    
    Raises:
        PayloadValidationError: 如果缺少必需字段
    
    Example:
        require_fields(payload, "agent_id", "subagent_id", "runtime_id")
    """
    missing = [f for f in fields if f not in payload]
    if missing:
        raise PayloadValidationError(
            f"Missing required fields: {', '.join(missing)}",
            details={"missing_fields": missing, "provided_fields": list(payload.keys())}
        )
