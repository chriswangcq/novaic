"""
Task Queue 异常定义

定义可重试的基础设施异常类型，用于 TaskWorker 和 SagaWorker 判断是否重试。
"""

import httpx

# 从 common.exceptions 导入业务异常
from common.exceptions import (
    BusinessError,
    ValidationError,
    NotFoundError,
    StateConflictError,
    ConfigurationError,
)


# Task Queue 特定异常
class RetryableError(Exception):
    """可重试的错误（基础设施错误）"""
    pass


class TaskNotFoundError(Exception):
    """Task 不存在"""
    pass


class SagaError(Exception):
    """Saga 执行错误"""
    pass


class TaskQueueError(Exception):
    """Task Queue 通用错误"""
    pass


class PayloadValidationError(BusinessError):
    """Payload 验证错误，包含详细信息"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

# 可重试的基础设施异常类型
# 这些异常通常是临时性的，重试可能成功
RETRYABLE_EXCEPTIONS = (
    # httpx 网络相关异常
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.NetworkError,
    # Python 内置网络异常
    ConnectionError,
    TimeoutError,
    OSError,  # 包含网络相关的 socket 错误
)

# 可重试的错误关键词（用于检查错误消息）
RETRYABLE_KEYWORDS = [
    "timeout",
    "connection",
    "network",
    "socket",
    "temporarily unavailable",
    "service unavailable",
    "too many requests",
    "rate limit",
]


def is_retryable_error(error: Exception) -> bool:
    """
    判断是否是可重试的基础设施错误
    
    Args:
        error: 捕获的异常
        
    Returns:
        True 如果是可重试错误，False 如果是业务错误或未知错误
    """
    # 1. 检查是否是已知的可重试异常类型
    if isinstance(error, RETRYABLE_EXCEPTIONS):
        return True
    
    # 2. 检查错误消息中是否包含可重试的关键词
    error_msg = str(error).lower()
    return any(keyword in error_msg for keyword in RETRYABLE_KEYWORDS)
