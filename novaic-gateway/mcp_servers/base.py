"""
Base MCP Server - 子 MCP Server 基类

所有子 MCP Server 都继承这个基类，提供统一的接口：
- 创建 FastMCP 实例
- 注册工具
- 获取 ASGI app 用于挂载
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """
    子 MCP Server 基类。
    
    每个子 MCP Server 都是一个独立的 FastMCP 实例，可以：
    1. 独立暴露 HTTP 端点
    2. 被 Gateway 聚合
    """
    
    # 子类需要定义的属性
    name: str = "base"
    description: str = "Base MCP Server"
    
    def __init__(self, agent_id: Optional[str] = None):
        """
        初始化 MCP Server。
        
        Args:
            agent_id: Agent ID，用于隔离资源 (端口、数据目录等)
        """
        self.agent_id = agent_id
        self.mcp = FastMCP(
            name=self.name,
            instructions=self._build_instructions(),
        )
        self._tools_registered = False
        self._http_app = None  # 缓存 http_app，避免重复创建
        
        logger.info(f"[{self.name}] MCP Server created (agent_id={agent_id})")
    
    def _build_instructions(self) -> str:
        """构建 MCP Server 说明。子类可以覆盖。"""
        return self.description
    
    @abstractmethod
    def _register_tools(self) -> None:
        """
        注册工具到 self.mcp。
        
        子类必须实现这个方法，使用 @self.mcp.tool() 装饰器注册工具。
        """
        pass
    
    def setup(self) -> None:
        """设置 MCP Server，注册所有工具。"""
        if self._tools_registered:
            return
        
        self._register_tools()
        self._tools_registered = True
        
        logger.info(f"[{self.name}] Tools registered")
    
    def get_asgi_app(self, path: str = "/"):
        """
        获取 ASGI app 用于挂载到 FastAPI。
        
        注意：http_app 只创建一次并缓存，确保 lifespan 正确工作。
        
        Args:
            path: MCP 端点路径
        
        Returns:
            Starlette ASGI application
        """
        if self._http_app is None:
            self._http_app = self.mcp.http_app(path=path)
        return self._http_app
    
    def get_stats(self) -> Dict[str, Any]:
        """获取 Server 统计信息。"""
        return {
            "name": self.name,
            "description": self.description,
            "tools_registered": self._tools_registered,
        }
