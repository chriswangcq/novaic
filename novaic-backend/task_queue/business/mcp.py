"""
MCP Business - MCP Server 管理

业务逻辑：
- 创建 MCP Server
- 销毁 MCP Server
- 执行工具
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

from mcp_gateway.mcp_client import MCPServerConnection
from ..client import GatewayInternalClient


@dataclass
class MCPCreateResult:
    """MCP 创建结果"""
    success: bool
    runtime_id: str
    mcp_url: str = ""
    created: bool = False
    message: str = ""
    error: str = ""


@dataclass
class MCPDestroyResult:
    """MCP 销毁结果"""
    success: bool
    runtime_id: str
    destroyed: bool = False
    message: str = ""
    error: str = ""


@dataclass
class ToolExecuteResult:
    """工具执行结果"""
    success: bool
    tool_call_id: str
    tool_name: str
    result: Any = None
    error: str = ""
    status: str = ""  # executed / failed


class MCPBusiness:
    """
    MCP 业务逻辑
    
    所有方法都是幂等的。
    
    Example:
        >>> from task_queue.business import MCPBusiness
        >>> mcp_biz = MCPBusiness(db, mcp_manager, mcp_client)
        >>> result = mcp_biz.create(runtime_id="rt-123", agent_id="agent-1")
        >>> if result.success:
        ...     print(f"MCP URL: {result.mcp_url}")
    """
    
    def __init__(self, gateway_url: str, mcp_client=None, client: Optional[GatewayInternalClient] = None):
        """
        Args:
            gateway_url: Gateway base URL
            mcp_client: MCP 客户端（用于工具调用）
            client: 可复用的 GatewayInternalClient
        """
        self.mcp_client = mcp_client
        self.client = client or GatewayInternalClient(gateway_url)


    def create(
        self,
        runtime_id: str,
        agent_id: str,
    ) -> MCPCreateResult:
        """
        创建 MCP Server
        
        幂等性：检查是否已存在
        
        Args:
            runtime_id: Runtime ID
            agent_id: Agent ID
            
        Returns:
            MCPCreateResult
        """
        runtime = self.client.get_runtime(runtime_id)
        if not runtime:
            return MCPCreateResult(
                success=False,
                runtime_id=runtime_id,
                error="Runtime not found",
            )

        if runtime.get("mcp_url"):
            return MCPCreateResult(
                success=True,
                runtime_id=runtime_id,
                mcp_url=runtime.get("mcp_url", ""),
                created=False,
                message="MCP already exists",
            )

        subagent_id = runtime.get("subagent_id")
        if not subagent_id:
            return MCPCreateResult(
                success=False,
                runtime_id=runtime_id,
                error="SubAgent not found",
            )

        try:
            resp = self.client.create_aggregate_mcp(
                agent_id=agent_id,
                runtime_id=runtime_id,
                subagent_id=subagent_id,
            )
            mcp_url = resp.get("mcp_url") or f"/mcp/aggregate/{runtime_id}/"
            self.client.update_runtime(runtime_id, {"mcp_url": mcp_url})
        except Exception as e:
            return MCPCreateResult(
                success=False,
                runtime_id=runtime_id,
                error=str(e),
            )

        return MCPCreateResult(
            success=True,
            runtime_id=runtime_id,
            mcp_url=mcp_url,
            created=True,
        )
    
    def destroy(self, runtime_id: str) -> MCPDestroyResult:
        """
        销毁 MCP Server
        
        幂等性：检查是否已不存在
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            MCPDestroyResult
        """
        runtime = self.client.get_runtime(runtime_id)
        if not runtime:
            return MCPDestroyResult(
                success=True,
                runtime_id=runtime_id,
                message="Runtime not found, nothing to destroy",
            )

        if not runtime.get("mcp_url"):
            return MCPDestroyResult(
                success=True,
                runtime_id=runtime_id,
                destroyed=False,
                message="MCP already destroyed",
            )

        agent_id = runtime.get("agent_id")
        try:
            self.client.destroy_aggregate_mcp(agent_id, runtime_id)
        except Exception as e:
            if "not found" not in str(e).lower():
                return MCPDestroyResult(
                    success=False,
                    runtime_id=runtime_id,
                    error=str(e),
                )

        self.client.update_runtime(runtime_id, {"mcp_url": None})

        return MCPDestroyResult(
            success=True,
            runtime_id=runtime_id,
            destroyed=True,
        )
    
    def execute_tool(
        self,
        runtime_id: str,
        tool_call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> ToolExecuteResult:
        """
        执行工具
        
        幂等性：工具本身负责保证
        
        Args:
            runtime_id: Runtime ID
            tool_call_id: Tool Call ID
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            ToolExecuteResult
        """
        if not self.mcp_client:
            return ToolExecuteResult(
                success=False,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                error="MCP client not configured",
                status="failed",
            )
        
        runtime = self.client.get_runtime(runtime_id)
        mcp_url = runtime.get("mcp_url") if runtime else None
        if not mcp_url:
            return ToolExecuteResult(
                success=False,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                error="Runtime MCP not found",
                status="failed",
            )
        
        try:
            # 执行工具
            result = self.mcp_client.call_tool(
                mcp_url=mcp_url,
                tool_name=tool_name,
                arguments=arguments,
            )
            
            return ToolExecuteResult(
                success=True,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                result=result,
                status="executed",
            )
            
        except Exception as e:
            return ToolExecuteResult(
                success=False,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                error=str(e),
                status="failed",
            )
    
    def get_mcp_url(self, runtime_id: str) -> Optional[str]:
        """
        获取 Runtime 的 MCP URL
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            MCP URL 或 None
        """
        runtime = self.client.get_runtime(runtime_id)
        return runtime.get("mcp_url") if runtime else None


class MCPGatewayClient:
    """HTTP client for MCP aggregate gateways."""

    def __init__(self):
        self._connections: Dict[str, MCPServerConnection] = {}

    def _normalize_url(self, mcp_url: str) -> str:
        url = mcp_url.strip()
        if url.startswith("/"):
            base = os.environ.get("NOVAIC_MCP_GATEWAY_URL", "http://127.0.0.1:19998")
            url = f"{base.rstrip('/')}{url}"
        if not url.endswith("/"):
            url = f"{url}/"
        return url

    def _get_connection(self, mcp_url: str) -> MCPServerConnection:
        url = self._normalize_url(mcp_url)
        conn = self._connections.get(url)
        if not conn:
            conn = MCPServerConnection(name=f"aggregate-{len(self._connections)}", port=0)
            conn.url = url
            self._connections[url] = conn
        return conn

    def call_tool(self, mcp_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """同步调用工具（包装async方法）"""
        import asyncio
        conn = self._get_connection(mcp_url)
        
        # 同步包装async方法
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行的loop，创建新的
            return asyncio.run(conn.call_tool(name=tool_name, arguments=arguments))
        else:
            # 有运行的loop，使用run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    conn.call_tool(name=tool_name, arguments=arguments)
                )
                return future.result()

    def list_tools(self, mcp_url: str, use_cache: bool = True) -> Dict[str, Any]:
        """同步获取工具列表（包装async方法）"""
        import asyncio
        conn = self._get_connection(mcp_url)
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(conn.list_tools(use_cache=use_cache))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    conn.list_tools(use_cache=use_cache)
                )
                return future.result()


