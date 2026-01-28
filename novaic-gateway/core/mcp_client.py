"""
MCP Client - VSOCK 实现

通过 VSOCK (AF_VSOCK) 与 VM 内的 MCP Server 通信。
无需端口转发，每个 VM 通过唯一 CID 标识。

特性:
- VSOCK 通信: 高性能虚拟机套接字
- 自动重试: 网络错误时自动重试
- Session 恢复: Session 失效时自动重新初始化
- 健康检查: 定期检查连接状态
"""

from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
import socket

logger = logging.getLogger(__name__)

# Check if VSOCK is supported
VSOCK_SUPPORTED = hasattr(socket, 'AF_VSOCK')
if VSOCK_SUPPORTED:
    AF_VSOCK = socket.AF_VSOCK
    VMADDR_CID_HOST = 2
else:
    AF_VSOCK = None
    VMADDR_CID_HOST = 2

# 常见的 Session 失效错误消息
SESSION_ERROR_MESSAGES = [
    "session not found",
    "session expired",
    "invalid session",
    "unknown session",
    "session_id",
]


class VSockTransport:
    """
    VSOCK 传输层
    
    通过 AF_VSOCK 与 VM 内的 MCP Server 通信。
    """
    
    def __init__(self, cid: int, port: int = 8080):
        """
        初始化 VSOCK 传输
        
        Args:
            cid: VM 的 Context ID (通常是 3+)
            port: VSOCK 端口 (默认 8080)
        """
        self.cid = cid
        self.port = port
    
    @staticmethod
    def is_supported() -> bool:
        """检查系统是否支持 VSOCK"""
        return VSOCK_SUPPORTED
    
    async def send_request(self, data: bytes, timeout: float = 60.0) -> bytes:
        """
        发送请求并接收响应
        
        通过 VSOCK 发送 HTTP 请求格式（VM 内代理转发到 MCP Server）
        """
        if not VSOCK_SUPPORTED:
            raise RuntimeError("VSOCK not supported on this system")
        
        sock = None
        try:
            sock = socket.socket(AF_VSOCK, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.cid, self.port))
            
            # 发送 HTTP 请求
            sock.sendall(data)
            
            # 接收响应
            response = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                response += chunk
                # 检查是否收到完整的 HTTP 响应
                if b"\r\n\r\n" in response:
                    header_end = response.find(b"\r\n\r\n")
                    headers = response[:header_end].decode('utf-8', errors='ignore')
                    body_start = header_end + 4
                    
                    content_length = 0
                    for line in headers.split("\r\n"):
                        if line.lower().startswith("content-length:"):
                            content_length = int(line.split(":")[1].strip())
                            break
                    
                    if len(response) >= body_start + content_length:
                        break
            
            return response
            
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass


class MCPServerConnection:
    """
    单个 MCP Server 的连接管理
    
    通过 VSOCK 与 VM 内的 MCP Server 通信。
    """
    
    def __init__(self, name: str, vsock_cid: int, vsock_port: int = 8080):
        """
        初始化 MCP Server 连接
        
        Args:
            name: Server 名称
            vsock_cid: VSOCK CID
            vsock_port: VSOCK 端口 (默认 8080)
        """
        self.name = name
        self.vsock_cid = vsock_cid
        self.vsock_port = vsock_port
        
        # VSOCK 传输
        self._vsock_transport = VSockTransport(vsock_cid, vsock_port)
        
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._request_id = 0
        self._session_id: Optional[str] = None
        self._protocol_version = "2024-11-05"
    
    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送 JSON-RPC 请求 (通过 VSOCK)
        
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
        
        # 构建 HTTP 请求（VM 内代理会转发到 MCP Server）
        body = json.dumps(payload).encode('utf-8')
        
        headers_list = [
            "POST /mcp HTTP/1.1",
            "Host: localhost",
            "Content-Type: application/json",
            "Accept: application/json, text/event-stream",
            f"Content-Length: {len(body)}",
        ]
        if self._session_id:
            headers_list.append(f"mcp-session-id: {self._session_id}")
        headers_list.append("")
        headers_list.append("")
        
        request = "\r\n".join(headers_list).encode('utf-8') + body
        
        print(f"[MCP] VSOCK CID={self.vsock_cid}:{self.vsock_port} method={method}")
        
        try:
            response = await self._vsock_transport.send_request(request)
            
            # 解析 HTTP 响应
            response_str = response.decode('utf-8', errors='ignore')
            
            if "\r\n\r\n" in response_str:
                header_part, body_part = response_str.split("\r\n\r\n", 1)
            else:
                return {"error": {"message": "Invalid HTTP response"}}
            
            # 提取 session ID
            for line in header_part.split("\r\n"):
                if line.lower().startswith("mcp-session-id:"):
                    self._session_id = line.split(":", 1)[1].strip()
            
            print(f"[MCP] Response body length: {len(body_part)}")
            
            # 检查 content type
            content_type = ""
            for line in header_part.split("\r\n"):
                if line.lower().startswith("content-type:"):
                    content_type = line.split(":", 1)[1].strip()
            
            if "text/event-stream" in content_type:
                return self._parse_sse_response(body_part, request_id)
            else:
                return json.loads(body_part)
                
        except Exception as e:
            logger.error(f"[MCP] VSOCK request failed: {e}")
            return {"error": {"message": str(e)}}
    
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
    
    def _is_session_error(self, result: Dict[str, Any]) -> bool:
        """检查是否是 Session 相关错误"""
        error = result.get("error", {})
        error_msg = str(error.get("message", "")).lower()
        error_code = error.get("code", 0)
        
        # 检查常见的 session 错误
        for msg in SESSION_ERROR_MESSAGES:
            if msg in error_msg:
                return True
        
        # HTTP 401/403 通常也表示 session 问题
        if error_code in [-32001, -32002, 401, 403]:
            return True
        
        return False
    
    async def health_check(self, timeout: float = 5.0) -> bool:
        """
        检查 MCP 连接是否健康
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._session_id:
            return False
        
        try:
            # 使用较短的超时时间
            old_timeout = None
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=timeout, read=timeout, write=timeout, pool=timeout),
                transport=httpx.AsyncHTTPTransport(proxy=None),
                trust_env=False,
            ) as client:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": self._session_id,
                }
                # 发送一个简单的 tools/list 请求作为健康检查
                payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": self._next_request_id(),
                    "params": {}
                }
                response = await client.post(self.url, json=payload, headers=headers)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"[MCP] Health check failed for {self.name}: {e}")
            return False
    
    async def ensure_connected(self) -> bool:
        """
        确保连接可用，必要时重新初始化
        
        Returns:
            True if connected, False otherwise
        """
        if self._session_id and await self.health_check():
            return True
        
        # Session 不存在或不健康，重新初始化
        logger.info(f"[MCP] Reconnecting to {self.name}...")
        self._session_id = None
        return await self.initialize()

    async def initialize(self, max_retries: int = 3, retry_delay: float = 2.0) -> bool:
        """初始化 MCP 连接（带重试）"""
        if not VSOCK_SUPPORTED:
            print(f"[MCP] VSOCK not supported on this system")
            return False
        
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
                    print(f"[MCP] Connected to {self.name} via VSOCK CID={self.vsock_cid}: {result['result'].get('serverInfo', {})}")
                    
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
    
    async def call_tool(
        self, 
        name: str, 
        arguments: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        调用工具（带重试和 Session 恢复）
        
        Args:
            name: 工具名称
            arguments: 工具参数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒），使用指数退避
        
        Returns:
            工具执行结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 确保已初始化
                if not self._session_id:
                    if not await self.initialize():
                        last_error = "Failed to initialize MCP connection"
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        return {"success": False, "error": last_error}
                
                result = await self._send_request("tools/call", {
                    "name": name,
                    "arguments": arguments
                })
                
                # 检查是否是 Session 错误
                if self._is_session_error(result):
                    logger.warning(f"[MCP] Session error detected, reconnecting... (attempt {attempt + 1}/{max_retries})")
                    self._session_id = None  # 清除旧 session
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    return {"success": False, "error": "Session expired and reconnection failed"}
                
                if "result" in result:
                    return self._convert_tool_result(result["result"])
                else:
                    error = result.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    # 非 session 错误，直接返回（不重试业务错误）
                    return {"success": False, "error": error_msg}
                    
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                # 网络错误，重试
                last_error = str(e)
                logger.warning(f"[MCP] Network error calling {name} (attempt {attempt + 1}/{max_retries}): {e}")
                self._session_id = None  # 网络错误后清除 session
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                    
            except Exception as e:
                # 其他错误
                last_error = str(e)
                logger.error(f"[MCP] Failed to call tool {name}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
        
        return {"success": False, "error": f"Failed after {max_retries} attempts: {last_error}"}
    
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
    """MCP Client - 管理多个 MCP Server (VSOCK)"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConnection] = {}
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tool_server_map: Dict[str, str] = {}
    
    async def register_server(self, name: str, vsock_cid: int, vsock_port: int = 8080):
        """
        注册 MCP Server
        
        Args:
            name: Server 名称
            vsock_cid: VSOCK CID
            vsock_port: VSOCK 端口 (默认 8080)
        """
        server = MCPServerConnection(
            name=name,
            vsock_cid=vsock_cid,
            vsock_port=vsock_port,
        )
        self.servers[name] = server
        self._tools_cache = None
        self._tool_server_map.clear()
        
        logger.info(f"[MCPClient] Registered server: {name} (VSOCK CID={vsock_cid}:{vsock_port})")
    
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
    
    async def health_check(self) -> Dict[str, bool]:
        """
        检查所有 Server 的健康状态
        
        Returns:
            Dict mapping server name to health status
        """
        results = {}
        for name, server in self.servers.items():
            results[name] = await server.health_check()
        return results
    
    async def ensure_all_connected(self) -> Dict[str, bool]:
        """
        确保所有 Server 都已连接
        
        Returns:
            Dict mapping server name to connection status
        """
        results = {}
        for name, server in self.servers.items():
            results[name] = await server.ensure_connected()
        return results
    
    async def close(self):
        """关闭"""
        self.servers.clear()
        self._tools_cache = None
        self._tool_server_map.clear()
