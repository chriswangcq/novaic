"""
业务异常类定义

用于区分业务逻辑错误和基础设施错误：
- BusinessError: 业务逻辑错误，不应重试（如参数验证失败、业务规则冲突）
- 基础设施错误: 网络超时、连接失败等，应该重试

使用场景：
- Handler 中遇到明确的业务错误时，抛出 BusinessError
- TaskWorker 捕获后不重试，直接标记任务失败
"""


class BusinessError(Exception):
    """
    业务逻辑错误基类
    
    抛出此异常表示错误是由业务逻辑导致的，重试不会改变结果。
    例如：
    - 参数验证失败
    - 业务规则冲突
    - 资源不存在（且不会自动创建）
    - 权限不足
    """
    pass


class ValidationError(BusinessError):
    """
    参数验证错误
    
    当 payload 参数不符合预期时抛出。
    例如：
    - 必填字段缺失
    - 字段类型错误
    - 字段值不在允许范围内
    """
    pass


class NotFoundError(BusinessError):
    """
    资源不存在错误
    
    当请求的资源不存在且无法自动创建时抛出。
    例如：
    - Runtime 不存在
    - SubAgent 不存在
    - Agent 不存在
    """
    pass


class StateConflictError(BusinessError):
    """
    状态冲突错误
    
    当资源状态不符合操作前提条件时抛出。
    例如：
    - CAS 操作失败（expected_status 不匹配）
    - 资源已被删除
    - 并发修改冲突
    """
    pass


class ConfigurationError(BusinessError):
    """
    配置错误
    
    当系统配置不正确导致无法执行时抛出。
    例如：
    - 未知的 saga_type
    - 未注册的 handler topic
    - 缺少必要的环境变量
    """
    pass
