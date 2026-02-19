"""
业务异常类定义

用于区分业务逻辑错误和基础设施错误：
- BusinessError: 业务逻辑错误，不应重试（如参数验证失败、业务规则冲突）
- 基础设施错误: 网络超时、连接失败等，应该重试
"""


class BusinessError(Exception):
    """业务逻辑错误基类。"""


class ValidationError(BusinessError):
    """参数验证错误。"""


class NotFoundError(BusinessError):
    """资源不存在错误。"""


class StateConflictError(BusinessError):
    """状态冲突错误。"""


class ConfigurationError(BusinessError):
    """配置错误。"""
