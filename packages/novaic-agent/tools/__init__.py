"""
NovAIC Agent Tools Module

工具执行器 - 通过调用 Executor API 执行操作。
不再本地执行，而是委托给 Executor 服务。
"""

from .executor import ToolExecutor

__all__ = ["ToolExecutor"]
