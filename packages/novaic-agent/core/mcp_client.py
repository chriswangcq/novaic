"""
MCP Client - 连接 MCP Server，统一管理工具

Agent 通过 MCP Client 发现和调用工具，不绑定具体实现。
"""

from typing import Dict, List, Any, Optional
import httpx


class MCPServer:
    """
    MCP Server 客户端（HTTP 实现）
    未来可以扩展支持 stdio MCP
    """
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            # 明确设置各类超时：connect=10s, read=120s, write=30s
            # navigate 等操作可能需要较长时间（页面加载+JS渲染）
            timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        client = await self._get_client()
        resp = await client.get(f"{self.base_url}/mcp/tools")
        resp.raise_for_status()
        data = resp.json()
        tools = data.get("tools", [])
        # 添加 server 标识
        for tool in tools:
            tool["_server"] = self.name
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        client = await self._get_client()
        resp = await client.post(
            f"{self.base_url}/mcp/tools/call",
            json={
                "name": name,
                "arguments": arguments
            }
        )
        resp.raise_for_status()
        return resp.json()
    
    async def close(self):
        """关闭资源"""
        if self._client:
            await self._client.aclose()
            self._client = None


class MCPClient:
    """
    MCP Client - 管理多个 MCP Server，统一工具发现和调用
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
    
    async def register_server(self, name: str, base_url: str):
        """注册 MCP Server"""
        server = MCPServer(name, base_url)
        self.servers[name] = server
        # 清除工具缓存
        self._tools_cache = None
        print(f"[MCPClient] Registered server: {name} at {base_url}")
    
    async def list_all_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        从所有 Server 收集工具
        
        Args:
            use_cache: 是否使用缓存（默认 True）
        """
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        all_tools = []
        for server_name, server in self.servers.items():
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
                print(f"[MCPClient] Discovered {len(tools)} tools from {server_name}")
            except Exception as e:
                print(f"[MCPClient] Failed to list tools from {server_name}: {e}")
        
        self._tools_cache = all_tools
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具（自动路由到对应 Server）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        # 查找工具对应的 Server
        server = self._find_server_for_tool(tool_name)
        if server is None:
            raise ValueError(f"Tool '{tool_name}' not found in any registered server")
        
        return await server.call_tool(tool_name, arguments)
    
    def _find_server_for_tool(self, tool_name: str) -> Optional[MCPServer]:
        """查找工具对应的 Server"""
        # 如果工具缓存中有 server 标识，直接使用
        if self._tools_cache:
            for tool in self._tools_cache:
                if tool.get("name") == tool_name:
                    server_name = tool.get("_server")
                    if server_name and server_name in self.servers:
                        return self.servers[server_name]
        
        # 否则尝试所有 Server（性能较差，但兼容性更好）
        # 实际使用中应该通过工具缓存中的 _server 字段路由
        for server in self.servers.values():
            # 这里可以优化：先检查工具是否在该 Server 的列表中
            # 简化版：直接尝试调用（如果失败会抛出异常）
            return server
        
        return None
    
    def to_llm_tools_format(self, tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        转换为 LLM 工具格式（OpenAI/Doubao）
        
        Args:
            tools: 工具列表（如果为 None，使用缓存的工具）
        
        Returns:
            LLM 格式的工具列表
        """
        if tools is None:
            tools = self._tools_cache or []
        
        llm_tools = []
        for tool in tools:
            llm_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        return llm_tools
    
    def clear_cache(self):
        """清除工具缓存"""
        self._tools_cache = None
    
    async def close(self):
        """关闭所有 Server 连接"""
        for server in self.servers.values():
            await server.close()
        self.servers.clear()
        self._tools_cache = None

