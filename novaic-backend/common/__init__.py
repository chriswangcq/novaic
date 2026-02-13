"""
NovAIC Backend Common Library

公共基础设施代码，供多个服务共享使用。
"""

__version__ = "1.0.0"

# 导出常用异常类
from .exceptions import (
    BusinessError,
    ValidationError,
    NotFoundError,
    StateConflictError,
    ConfigurationError,
)
