"""
MCP Client - 简单 HTTP 实现

直接使用 HTTP POST 发送 JSON-RPC 请求，兼容 FastMCP 的 streamable-http transport。
不依赖复杂的 MCP SDK 流机制，更可靠。
"""

from typing import Dict, List, Any, Optional
import logging
import json
import httpx

logger = logging.getLogger(__name__)


class MCPServerConnection:
    """
    单个 MCP Server 的连接管理
    
    使用简单的 HTTP POST 请求调用 MCP Server。
    """
    
    def __init__(self, name: str, url: str):
        """
        初始化 MCP Server 连接
        
        Args:
            name: Server 名称
            url: MCP 端点 URL（如 http://127.0.0.1:8080/mcp）
        """
        self.name = name
        self.url = url
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._request_id = 0
        self._session_id: Optional[str] = None
        self._protocol_version = "2024-11-05"
    
    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    def _create_client(self) -> httpx.AsyncClient:
        """创建不走代理的 HTTP 客户端"""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0),
            transport=httpx.AsyncHTTPTransport(proxy=None),
            trust_env=False,
        )
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送 JSON-RPC 请求
        
        Args:
            method: MCP 方法名
            params: 方法参数
        
        Returns:
            响应结果
        """
        request_id = self._next_request_id()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id,
        }
        if params:
            payload["params"] = params
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        
        async with self._create_client() as client:
            print(f"[MCP] POST {self.url} method={method}")
            response = await client.post(self.url, json=payload, headers=headers)
            print(f"[MCP] Response status: {response.status_code}")
            
            # 保存 session ID
            if "mcp-session-id" in response.headers:
                self._session_id = response.headers["mcp-session-id"]
            
            # 解析响应（可能是 SSE 格式）
            content_type = response.headers.get("content-type", "")
            text = response.text
            print(f"[MCP] Content-Type: {content_type}, Body length: {len(text)}")
            
            if "text/event-stream" in content_type:
                # 解析 SSE 响应
                return self._parse_sse_response(text, request_id)
            else:
                # 普通 JSON 响应
                return response.json()
    
    def _parse_sse_response(self, text: str, request_id: int) -> Dict[str, Any]:
        """解析 SSE 格式的响应"""
        for line in text.split("\n"):
            if line.startswith("data: "):
                data = line[6:]
                if data:
                    try:
                        parsed = json.loads(data)
                        if parsed.get("id") == request_id:
                            return parsed
                    except json.JSONDecodeError:
                        continue
        return {"error": {"message": "No valid response in SSE stream"}}
    
    async def initialize(self, max_retries: int = 3, retry_delay: float = 2.0) -> bool:
        """初始化 MCP 连接（带重试）"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                result = await self._send_request("initialize", {
                    "protocolVersion": self._protocol_version,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "novaic-agent",
                        "version": "0.1.0"
                    }
                })
                
                if "result" in result:
                    print(f"[MCP] Connected to {self.name}: {result['result'].get('serverInfo', {})}")
                    
                    # 发送 initialized 通知
                    await self._send_notification("notifications/initialized", {})
                    return True
                else:
                    print(f"[MCP] Init failed for {self.name}: {result.get('error', {})}")
                    
            except Exception as e:
                print(f"[MCP] Failed to initialize {self.name} (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 重试前等待
            if attempt < max_retries - 1:
                print(f"[MCP] Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
        
        return False
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """发送通知（无响应）"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            payload["params"] = params
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        
        try:
            async with self._create_client() as client:
                await client.post(self.url, json=payload, headers=headers)
        except Exception:
            pass  # 通知不需要响应
    
    async def list_tools(self, use_cache: bool = True, max_retries: int = 3) -> List[Dict[str, Any]]:
        """获取工具列表（带重试）"""
        import asyncio
        
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        for attempt in range(max_retries):
            try:
                # 先初始化
                if not self._session_id:
                    print(f"[MCP] Initializing connection to {self.name} at {self.url}...")
                    if not await self.initialize():
                        print(f"[MCP] Failed to initialize {self.name}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2.0)
                            continue
                        return []
                    print(f"[MCP] Initialized {self.name}, session_id: {self._session_id}")
                
                print(f"[MCP] Listing tools from {self.name}...")
                result = await self._send_request("tools/list", {})
                print(f"[MCP] tools/list response: {str(result)[:500]}")
                
                if "result" in result:
                    tools = result["result"].get("tools", [])
                    self._tools_cache = tools
                    print(f"[MCP] Discovered {len(tools)} tools from {self.name}")
                    return tools
                else:
                    print(f"[MCP] List tools failed: {result.get('error', {})}")
                    
            except Exception as e:
                print(f"[MCP] Failed to list tools from {self.name} (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 重试前重置 session
            self._session_id = None
            if attempt < max_retries - 1:
                await asyncio.sleep(2.0)
        
        return []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        try:
            # 确保已初始化
            if not self._session_id:
                if not await self.initialize():
                    return {"success": False, "error": "Failed to initialize MCP connection"}
            
            result = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments
            })
            
            if "result" in result:
                return self._convert_tool_result(result["result"])
            else:
                error = result.get("error", {})
                return {"success": False, "error": error.get("message", "Unknown error")}
                
        except Exception as e:
            logger.error(f"[MCP] Failed to call tool {name}: {e}")
            return {"success": False, "error": str(e)}
    
    def _convert_tool_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """转换 MCP 工具结果为标准格式"""
        if result.get("isError"):
            content = result.get("content", [])
            error_msg = ""
            for item in content:
                if item.get("type") == "text":
                    error_msg += item.get("text", "")
            return {"success": False, "error": error_msg or "Tool execution failed"}
        
        output = {"success": True}
        content = result.get("content", [])
        
        for item in content:
            item_type = item.get("type", "")
            if item_type == "text":
                text = item.get("text", "")
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        output.update(parsed)
                    else:
                        output["observation"] = parsed
                except (json.JSONDecodeError, ValueError):
                    if "observation" in output:
                        output["observation"] += "\n" + text
                    else:
                        output["observation"] = text
            elif item_type == "image":
                output["screenshot"] = item.get("data", "")
                output["mime_type"] = item.get("mimeType", "image/png")
        
        return output
    
    def clear_cache(self):
        """清除缓存"""
        self._tools_cache = None


class MCPClient:
    """MCP Client - 管理多个 MCP Server"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConnection] = {}
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tool_server_map: Dict[str, str] = {}
    
    async def register_server(self, name: str, base_url: str):
        """注册 MCP Server"""
        mcp_url = base_url.rstrip("/")
        if not mcp_url.endswith("/mcp"):
            mcp_url += "/mcp"
        
        server = MCPServerConnection(name, mcp_url)
        self.servers[name] = server
        self._tools_cache = None
        self._tool_server_map.clear()
        
        logger.info(f"[MCPClient] Registered server: {name} at {mcp_url}")
    
    async def list_all_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """从所有 Server 收集工具"""
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        all_tools = []
        self._tool_server_map.clear()
        
        for server_name, server in self.servers.items():
            tools = await server.list_tools(use_cache=use_cache)
            for tool in tools:
                tool_dict = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
                    "_server": server_name
                }
                all_tools.append(tool_dict)
                self._tool_server_map[tool["name"]] = server_name
        
        self._tools_cache = all_tools
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        server_name = self._tool_server_map.get(tool_name)
        
        if server_name is None:
            await self.list_all_tools(use_cache=False)
            server_name = self._tool_server_map.get(tool_name)
        
        if server_name is None:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        server = self.servers.get(server_name)
        if server is None:
            return {"success": False, "error": f"Server '{server_name}' not found"}
        
        return await server.call_tool(tool_name, arguments)
    
    def to_llm_tools_format(self, tools: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """转换为 LLM 工具格式"""
        if tools is None:
            tools = self._tools_cache or []
        
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            for tool in tools
        ]
    
    def clear_cache(self):
        """清除缓存"""
        self._tools_cache = None
        self._tool_server_map.clear()
        for server in self.servers.values():
            server.clear_cache()
    
    async def close(self):
        """关闭"""
        self.servers.clear()
        self._tools_cache = None
        self._tool_server_map.clear()
