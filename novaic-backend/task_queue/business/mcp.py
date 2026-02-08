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
import time

import httpx

from ..client import GatewayInternalClient
from common.config import ServiceConfig


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
        >>> mcp_biz = MCPBusiness(gateway_url="http://127.0.0.1:19997")
        >>> result = mcp_biz.create(runtime_id="rt-123", agent_id="agent-1")
        >>> if result.success:
        ...     print(f"MCP URL: {result.mcp_url}")
    """
    
    def __init__(self, gateway_url: str, client: Optional[GatewayInternalClient] = None):
        """
        Args:
            gateway_url: Gateway base URL
            client: 可复用的 GatewayInternalClient
        """
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
            # 1. 在 Tools Server 创建 runtime context（带重试）
            tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
            max_retries = 3
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    with httpx.Client(timeout=10.0, trust_env=False) as http_client:
                        resp = http_client.post(
                            f"{tools_server_url}/internal/runtimes",
                            json={
                                "runtime_id": runtime_id,
                                "agent_id": agent_id,
                                "subagent_id": subagent_id,
                                "ports": {},
                            }
                        )
                        resp.raise_for_status()
                    last_error = None
                    break  # success
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        wait = 2 ** (attempt + 1)  # 2, 4, 8
                        print(f"[MCP] Tools Server not ready, retry {attempt+1}/{max_retries} in {wait}s: {e}")
                        time.sleep(wait)
            
            if last_error:
                return MCPCreateResult(
                    success=False,
                    runtime_id=runtime_id,
                    error=f"Tools Server registration failed after {max_retries} retries: {last_error}",
                )
            
            # 2. 创建 aggregate MCP（向后兼容）
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
            # 1. 删除 Tools Server runtime context
            tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
            with httpx.Client(timeout=10.0, trust_env=False) as http_client:
                resp = http_client.delete(
                    f"{tools_server_url}/internal/runtimes/{runtime_id}"
                )
                if resp.status_code != 404:  # Ignore 404
                    resp.raise_for_status()
            
            # 2. 删除 aggregate MCP（向后兼容）
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
        执行工具 - 通过 Tools Server HTTP API
        
        幂等性：工具本身负责保证
        
        Args:
            runtime_id: Runtime ID
            tool_call_id: Tool Call ID
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            ToolExecuteResult
        """
        tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
        
        try:
            with httpx.Client(timeout=ServiceConfig.MCP_CALL_TIMEOUT, trust_env=False) as client:
                resp = client.post(
                    f"{tools_server_url}/internal/runtimes/{runtime_id}/tools/call",
                    json={"name": tool_name, "arguments": arguments}
                )
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("success"):
                    return ToolExecuteResult(
                        success=True,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        result=result.get("result"),
                        status="executed",
                    )
                else:
                    return ToolExecuteResult(
                        success=False,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        error=result.get("error", "Unknown error"),
                        status="failed",
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


class ToolsServerClient:
    """
    Tools Server HTTP 客户端
    
    用于与 Tools Server 通信，执行工具调用和获取工具列表。
    
    Example:
        >>> client = ToolsServerClient()
        >>> result = client.call_tool("rt-123", "bash", {"command": "ls"})
        >>> tools = client.list_tools("rt-123")
    """

    def __init__(self):
        self._tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", "http://127.0.0.1:19998")

    def call_tool(self, runtime_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具 - 通过 Tools Server HTTP API
        
        Args:
            runtime_id: Runtime ID
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        with httpx.Client(timeout=ServiceConfig.MCP_CALL_TIMEOUT, trust_env=False) as client:
            resp = client.post(
                f"{self._tools_server_url}/internal/runtimes/{runtime_id}/tools/call",
                json={"name": tool_name, "arguments": arguments}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("success"):
                return result.get("result")
            else:
                raise Exception(result.get("error", "Unknown error"))

    def list_tools(self, runtime_id: str) -> Dict[str, Any]:
        """
        获取工具列表 - 通过 Tools Server HTTP API
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            工具列表
        """
        with httpx.Client(timeout=ServiceConfig.MCP_CALL_TIMEOUT, trust_env=False) as client:
            resp = client.get(
                f"{self._tools_server_url}/internal/runtimes/{runtime_id}/tools"
            )
            resp.raise_for_status()
            return resp.json()
