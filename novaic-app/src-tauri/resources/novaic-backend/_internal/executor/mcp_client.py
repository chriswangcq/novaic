"""
MCP Client - HTTP 实现

通过 HTTP 与 VM 内的 MCP Server 通信。
QEMU 使用端口转发将 VM 的 8080 端口映射到宿主机。

架构:
  Gateway -> HTTP -> QEMU port forward -> VM MCP Server

特性:
- HTTP: 简单可靠
- 端口绑定到 127.0.0.1，只有本地可访问
- 自动重试: 网络错误时自动重试
- Session 恢复: Session 失效时自动重新初始化
- 健康检查: 定期检查连接状态
- MCP 三元组: Tools, Resources, Prompts 完整支持
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import asyncio
import httpx

logger = logging.getLogger(__name__)


# ==================== Data Classes ====================

@dataclass
class MCPResource:
    """MCP Resource 数据类"""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResource":
        return cls(
            uri=data.get("uri", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            mime_type=data.get("mimeType", "text/plain")
        )


@dataclass
class MCPPrompt:
    """MCP Prompt 数据类"""
    name: str
    description: str = ""
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPPrompt":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            arguments=data.get("arguments", [])
        )


@dataclass
class MCPSkill:
    """MCP Skill - 从 Resources 中提取的技能定义"""
    name: str
    uri: str
    description: str
    content: str = ""
    loaded_at: Optional[datetime] = None
    
    def is_loaded(self) -> bool:
        return bool(self.content)

# 常见的 Session 失效错误消息
SESSION_ERROR_MESSAGES = [
    "session not found",
    "session expired",
    "invalid session",
    "unknown session",
    "session_id",
]


def get_mcp_url(port: int) -> str:
    """获取 MCP Server URL"""
    return f"http://127.0.0.1:{port}/mcp"


class MCPServerConnection:
    """
    单个 MCP Server 的连接管理
    
    通过 HTTP 与 MCP Server 通信。
    支持 MCP 三元组: Tools, Resources, Prompts
    """
    
    def __init__(self, name: str, port: int = None, url: str = None, connect_timeout: float = 1.0):
        """
        初始化 MCP Server 连接
        
        Args:
            name: Server 名称
            port: 宿主机端口 (可选，与 url 二选一)
            url: 完整 URL (可选，与 port 二选一)
            connect_timeout: 连接超时时间 (秒)
        """
        self.name = name
        self.port = port
        self.connect_timeout = connect_timeout
        if url:
            self.url = url
        elif port:
            self.url = get_mcp_url(port)
        else:
            raise ValueError("Either port or url must be provided")
        
        # Caches
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._resources_cache: Optional[List[MCPResource]] = None
        self._prompts_cache: Optional[List[MCPPrompt]] = None
        self._skills_cache: Dict[str, MCPSkill] = {}  # uri -> skill
        
        self._request_id = 0
        self._session_id: Optional[str] = None
        self._protocol_version = "2024-11-05"
    
    def _create_client(self) -> httpx.AsyncClient:
        """创建 HTTP 客户端"""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(connect=self.connect_timeout, read=60.0, write=30.0, pool=10.0),
            transport=httpx.AsyncHTTPTransport(proxy=None),
            trust_env=False,
        )
    
    def _next_request_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
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
        
        print(f"[MCP] HTTP {self.url} method={method}")
        
        try:
            async with self._create_client() as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    headers=headers,
                )
                
                print(f"[MCP] Response status: {response.status_code}")
                
                # 保存 session ID
                if "mcp-session-id" in response.headers:
                    self._session_id = response.headers["mcp-session-id"]
                
                # 解析响应
                content_type = response.headers.get("content-type", "")
                text = response.text
                print(f"[MCP] Response body length: {len(text)}")
                
                if "text/event-stream" in content_type:
                    return self._parse_sse_response(text, request_id)
                else:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"[MCP] HTTP request failed: {e}")
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
    
    async def health_check(self, timeout: float = 1.0) -> bool:
        """
        检查 MCP 连接是否健康
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self._session_id:
            return False
        
        try:
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

    async def initialize(self, max_retries: int = 1, retry_delay: float = 1.0) -> bool:
        """初始化 MCP 连接（带重试）
        
        Args:
            max_retries: 最大重试次数 (默认 1，即不重试，快速失败)
            retry_delay: 重试延迟（秒）
        """
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
                    print(f"[MCP] Connected to {self.name} via {self.url}: {result['result'].get('serverInfo', {})}")
                    
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
    
    async def list_tools(self, use_cache: bool = True, max_retries: int = 1) -> List[Dict[str, Any]]:
        """获取工具列表（带重试）
        
        Args:
            use_cache: 是否使用缓存
            max_retries: 最大重试次数 (默认 1，即不重试，快速失败用于发现阶段)
        """
        print(f"[MCP] list_tools called: use_cache={use_cache}, cache_exists={self._tools_cache is not None}")
        
        if use_cache and self._tools_cache is not None:
            print(f"[MCP] Returning cached tools: {len(self._tools_cache)} tools")
            return self._tools_cache
        
        for attempt in range(max_retries):
            try:
                # 先初始化
                if not self._session_id:
                    print(f"[MCP] No session, initializing connection to {self.name} at {self.url}...")
                    init_result = await self.initialize()
                    if not init_result:
                        print(f"[MCP] ✗ Failed to initialize {self.name}")
                        if attempt < max_retries - 1:
                            print(f"[MCP] Retrying in 1s... (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(1.0)
                            continue
                        return []
                    print(f"[MCP] ✓ Initialized {self.name}, session_id: {self._session_id[:20]}...")
                else:
                    print(f"[MCP] Using existing session: {self._session_id[:20]}...")
                
                print(f"[MCP] Sending tools/list request to {self.name}...")
                result = await self._send_request("tools/list", {})
                
                if "result" in result:
                    tools = result["result"].get("tools", [])
                    self._tools_cache = tools
                    print(f"[MCP] ✓ Discovered {len(tools)} tools from {self.name}")
                    if tools:
                        tool_names = [t.get('name', 'unknown') for t in tools[:5]]
                        print(f"[MCP] First 5 tools: {tool_names}")
                    return tools
                else:
                    error = result.get('error', {})
                    print(f"[MCP] ✗ List tools failed: code={error.get('code')}, message={error.get('message')}")
                    
            except Exception as e:
                import traceback
                print(f"[MCP] ✗ Exception listing tools from {self.name} (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"[MCP] Traceback:\n{traceback.format_exc()}")
            
            # 重试前重置 session
            print(f"[MCP] Resetting session for retry...")
            self._session_id = None
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0)
        
        print(f"[MCP] ✗ All {max_retries} attempts failed, returning empty list")
        return []
    
    # ==================== Resources API ====================
    
    async def list_resources(self, use_cache: bool = True) -> List[MCPResource]:
        """
        获取 Resources 列表
        
        Returns:
            MCPResource 列表
        """
        if use_cache and self._resources_cache is not None:
            return self._resources_cache
        
        try:
            if not self._session_id:
                if not await self.initialize():
                    return []
            
            result = await self._send_request("resources/list", {})
            
            if "result" in result:
                resources_data = result["result"].get("resources", [])
                self._resources_cache = [MCPResource.from_dict(r) for r in resources_data]
                print(f"[MCP] Discovered {len(self._resources_cache)} resources from {self.name}")
                return self._resources_cache
            else:
                logger.warning(f"[MCP] List resources failed: {result.get('error', {})}")
                
        except Exception as e:
            logger.error(f"[MCP] Failed to list resources from {self.name}: {e}")
        
        return []
    
    async def read_resource(self, uri: str) -> str:
        """
        读取 Resource 内容
        
        Args:
            uri: Resource URI (e.g., "skill://desktop")
        
        Returns:
            Resource 内容文本
        """
        try:
            if not self._session_id:
                if not await self.initialize():
                    return ""
            
            result = await self._send_request("resources/read", {"uri": uri})
            
            if "result" in result:
                contents = result["result"].get("contents", [])
                if contents:
                    # 通常只有一个 content
                    return contents[0].get("text", "")
            else:
                logger.warning(f"[MCP] Read resource failed for {uri}: {result.get('error', {})}")
                
        except Exception as e:
            logger.error(f"[MCP] Failed to read resource {uri}: {e}")
        
        return ""
    
    # ==================== Prompts API ====================
    
    async def list_prompts(self, use_cache: bool = True) -> List[MCPPrompt]:
        """
        获取 Prompts 列表
        
        Returns:
            MCPPrompt 列表
        """
        if use_cache and self._prompts_cache is not None:
            return self._prompts_cache
        
        try:
            if not self._session_id:
                if not await self.initialize():
                    return []
            
            result = await self._send_request("prompts/list", {})
            
            if "result" in result:
                prompts_data = result["result"].get("prompts", [])
                self._prompts_cache = [MCPPrompt.from_dict(p) for p in prompts_data]
                print(f"[MCP] Discovered {len(self._prompts_cache)} prompts from {self.name}")
                return self._prompts_cache
            else:
                # Prompts 可能不被所有 server 支持，静默处理
                logger.debug(f"[MCP] List prompts not supported or failed: {result.get('error', {})}")
                
        except Exception as e:
            logger.debug(f"[MCP] Failed to list prompts from {self.name}: {e}")
        
        return []
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """
        获取 Prompt 内容
        
        Args:
            name: Prompt 名称
            arguments: Prompt 参数
        
        Returns:
            Prompt 渲染后的内容
        """
        try:
            if not self._session_id:
                if not await self.initialize():
                    return ""
            
            params = {"name": name}
            if arguments:
                params["arguments"] = arguments
            
            result = await self._send_request("prompts/get", params)
            
            if "result" in result:
                messages = result["result"].get("messages", [])
                # 合并所有消息内容
                content_parts = []
                for msg in messages:
                    msg_content = msg.get("content", {})
                    if isinstance(msg_content, dict) and msg_content.get("type") == "text":
                        content_parts.append(msg_content.get("text", ""))
                    elif isinstance(msg_content, str):
                        content_parts.append(msg_content)
                return "\n".join(content_parts)
            else:
                logger.warning(f"[MCP] Get prompt failed for {name}: {result.get('error', {})}")
                
        except Exception as e:
            logger.error(f"[MCP] Failed to get prompt {name}: {e}")
        
        return ""
    
    # ==================== Skills API (基于 Resources) ====================
    
    async def discover_skills(self, uri_prefix: str = "skill://") -> List[MCPSkill]:
        """
        发现并缓存 Skills (从 Resources 中筛选)
        
        Args:
            uri_prefix: Skill URI 前缀
        
        Returns:
            MCPSkill 列表
        """
        resources = await self.list_resources()
        skills = []
        
        for resource in resources:
            if resource.uri.startswith(uri_prefix):
                skill = MCPSkill(
                    name=resource.name,
                    uri=resource.uri,
                    description=resource.description
                )
                self._skills_cache[resource.uri] = skill
                skills.append(skill)
        
        print(f"[MCP] Discovered {len(skills)} skills from {self.name}")
        return skills
    
    async def load_skill(self, uri: str) -> Optional[MCPSkill]:
        """
        加载 Skill 内容
        
        Args:
            uri: Skill URI
        
        Returns:
            加载了内容的 MCPSkill，如果失败返回 None
        """
        # 先检查缓存
        if uri in self._skills_cache and self._skills_cache[uri].is_loaded():
            return self._skills_cache[uri]
        
        # 读取内容
        content = await self.read_resource(uri)
        if not content:
            return None
        
        # 更新或创建 skill
        if uri in self._skills_cache:
            self._skills_cache[uri].content = content
            self._skills_cache[uri].loaded_at = datetime.now()
        else:
            self._skills_cache[uri] = MCPSkill(
                name=uri.replace("skill://", ""),
                uri=uri,
                description="",
                content=content,
                loaded_at=datetime.now()
            )
        
        return self._skills_cache[uri]
    
    async def get_skill_content(self, skill_name: str) -> str:
        """
        获取 Skill 内容（便捷方法）
        
        Args:
            skill_name: Skill 名称（不含 skill:// 前缀）
        
        Returns:
            Skill 内容
        """
        uri = f"skill://{skill_name}"
        skill = await self.load_skill(uri)
        return skill.content if skill else ""
    
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
        """
        转换 MCP 工具结果为标准格式
        
        保留 _mcp_content 数组以支持多模态内容的通用处理。
        content 中的 type 字段标识内容类型：
        - "text": 文本内容
        - "image": 图片内容 (data + mimeType)
        - "resource": 资源引用
        """
        if result.get("isError"):
            content = result.get("content", [])
            error_msg = ""
            for item in content:
                if item.get("type") == "text":
                    error_msg += item.get("text", "")
            return {"success": False, "error": error_msg or "Tool execution failed"}
        
        output = {"success": True}
        content = result.get("content", [])
        
        # 保留原始 MCP content 数组，供多模态处理使用
        output["_mcp_content"] = content
        
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
            # 图片等多模态内容保留在 _mcp_content 中，不再展开为特定字段
        
        return output
    
    def clear_cache(self):
        """清除所有缓存"""
        self._tools_cache = None
        self._resources_cache = None
        self._prompts_cache = None
        self._skills_cache.clear()


class MCPClient:
    """
    MCP Client - 管理多个 MCP Server
    
    支持 MCP 三元组完整功能:
    - Tools: 可执行的动作
    - Resources: 可读的数据源（包括 Skills）
    - Prompts: 预定义的交互模板
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConnection] = {}
        
        # Tools
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tool_server_map: Dict[str, str] = {}
        
        # Resources & Skills
        self._resources_cache: Optional[List[MCPResource]] = None
        self._skills_cache: Dict[str, MCPSkill] = {}  # uri -> skill
        
        # Prompts
        self._prompts_cache: Optional[List[MCPPrompt]] = None
    
    async def register_server(self, name: str, port: int = None, url: str = None, connect_timeout: float = 1.0):
        """
        注册 MCP Server
        
        Args:
            name: Server 名称
            port: 宿主机端口 (可选，与 url 二选一)
            url: 完整 URL (可选，与 port 二选一)
            connect_timeout: 连接超时时间 (秒)
        """
        server = MCPServerConnection(name=name, port=port, url=url, connect_timeout=connect_timeout)
        self.servers[name] = server
        self._clear_all_caches()
        
        logger.info(f"[MCPClient] Registered server: {name} ({server.url})")
    
    def _clear_all_caches(self):
        """清除所有缓存"""
        self._tools_cache = None
        self._tool_server_map.clear()
        self._resources_cache = None
        self._skills_cache.clear()
        self._prompts_cache = None
    
    async def list_all_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """从所有 Server 收集工具"""
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        all_tools = []
        self._tool_server_map.clear()
        
        for server_name, server in self.servers.items():
            tools = await server.list_tools(use_cache=use_cache)
            for tool in tools:
                input_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
                
                # 调试日志：打印 MCP Server 返回的原始 schema
                if len(all_tools) < 5:
                    print(f"[MCP] Raw tool from server: name={tool.get('name')}")
                    print(f"[MCP] Raw inputSchema: {json.dumps(input_schema, indent=2)}")
                
                tool_dict = {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "inputSchema": input_schema,
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
        """
        转换为 LLM 工具格式
        
        遵循 Codex/Cursor 最佳实践：
        - 清理和规范化 schema
        - 确保 required 字段正确设置
        - 设置 additionalProperties: false
        """
        if tools is None:
            tools = self._tools_cache or []
        
        result = []
        for tool in tools:
            input_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
            
            # 清理和规范化 schema（对齐 Codex 实现）
            sanitized = self._sanitize_json_schema(input_schema)
            
            # 确保 required 字段正确设置
            parameters = self._ensure_required_fields(sanitized)
            
            # 调试日志：打印前 5 个工具的 schema
            if len(result) < 5:
                print(f"[MCP] Tool '{tool['name']}' schema: required={parameters.get('required', [])}, "
                      f"properties={list(parameters.get('properties', {}).keys())}")
            
            result.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": parameters
                }
            })
        
        return result
    
    def _sanitize_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理和规范化 JSON Schema（对齐 Codex 实现）
        
        功能：
        - 确保每个 schema 有 type 字段
        - 确保 object 有 properties
        - 确保 array 有 items
        - 设置 additionalProperties: false（防止意外参数）
        """
        if not isinstance(schema, dict):
            return {"type": "string"}
        
        schema = schema.copy()
        schema_type = schema.get("type")
        
        # 推断 type
        if not schema_type:
            if "properties" in schema or "required" in schema:
                schema_type = "object"
            elif "items" in schema:
                schema_type = "array"
            else:
                schema_type = "string"
            schema["type"] = schema_type
        
        # 确保 object 有 properties
        if schema_type == "object":
            if "properties" not in schema:
                schema["properties"] = {}
            # 禁止额外属性（关键！防止 LLM 传递意外参数）
            schema["additionalProperties"] = False
            # 递归清理 properties
            cleaned_props = {}
            for name, prop_schema in schema.get("properties", {}).items():
                if isinstance(prop_schema, dict):
                    cleaned_props[name] = self._sanitize_json_schema(prop_schema)
                else:
                    cleaned_props[name] = prop_schema
            schema["properties"] = cleaned_props
        
        # 确保 array 有 items
        if schema_type == "array" and "items" not in schema:
            schema["items"] = {"type": "string"}
        
        return schema
    
    def _ensure_required_fields(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        确保 JSON Schema 有正确的 required 字段
        
        规则：
        - 如果参数没有 default，则为 required
        - 如果参数的类型不包含 null（nullable），则为 required
        - 如果 description 不包含 "optional"，则为 required
        """
        if schema.get("type") != "object":
            return schema
        
        properties = schema.get("properties", {})
        existing_required = schema.get("required")
        
        # 如果已经有非空的 required 字段，使用它
        if existing_required and len(existing_required) > 0:
            return schema
        
        # 推断 required 字段
        required = []
        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                required.append(prop_name)
                continue
            
            # 检查是否有 default
            has_default = "default" in prop_schema
            
            # 检查是否是可选类型 (anyOf 包含 null)
            any_of = prop_schema.get("anyOf", [])
            is_nullable = any(
                isinstance(t, dict) and t.get("type") == "null" 
                for t in any_of
            )
            
            # 检查 description 中的 optional 提示
            desc = str(prop_schema.get("description", "")).lower()
            is_optional_hint = "optional" in desc
            
            # 如果没有 default、不是 nullable、也没有 optional 提示，则为 required
            if not has_default and not is_nullable and not is_optional_hint:
                required.append(prop_name)
        
        # 总是设置 required 字段（即使为空也显式设置）
        result = schema.copy()
        result["required"] = required
        return result
    
    def clear_cache(self):
        """清除缓存"""
        self._clear_all_caches()
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
    
    # ==================== Resources API ====================
    
    async def list_all_resources(self, use_cache: bool = True) -> List[MCPResource]:
        """
        从所有 Server 收集 Resources
        
        Returns:
            所有 MCPResource 列表
        """
        if use_cache and self._resources_cache is not None:
            return self._resources_cache
        
        all_resources = []
        for server_name, server in self.servers.items():
            resources = await server.list_resources(use_cache=use_cache)
            all_resources.extend(resources)
        
        self._resources_cache = all_resources
        return all_resources
    
    async def read_resource(self, uri: str) -> str:
        """
        读取 Resource 内容
        
        Args:
            uri: Resource URI
        
        Returns:
            Resource 内容
        """
        # 尝试从每个 server 读取
        for server in self.servers.values():
            content = await server.read_resource(uri)
            if content:
                return content
        return ""
    
    # ==================== Skills API ====================
    
    async def discover_all_skills(self, uri_prefix: str = "skill://") -> List[MCPSkill]:
        """
        从所有 Server 发现 Skills
        
        Args:
            uri_prefix: Skill URI 前缀
        
        Returns:
            所有 MCPSkill 列表
        """
        all_skills = []
        for server_name, server in self.servers.items():
            skills = await server.discover_skills(uri_prefix)
            for skill in skills:
                self._skills_cache[skill.uri] = skill
            all_skills.extend(skills)
        
        print(f"[MCPClient] Total skills discovered: {len(all_skills)}")
        return all_skills
    
    async def load_skill(self, uri_or_name: str) -> Optional[MCPSkill]:
        """
        加载 Skill 内容
        
        Args:
            uri_or_name: Skill URI 或名称
        
        Returns:
            加载了内容的 MCPSkill
        """
        # 规范化 URI
        uri = uri_or_name if uri_or_name.startswith("skill://") else f"skill://{uri_or_name}"
        
        # 检查缓存
        if uri in self._skills_cache and self._skills_cache[uri].is_loaded():
            return self._skills_cache[uri]
        
        # 从 servers 加载
        for server in self.servers.values():
            skill = await server.load_skill(uri)
            if skill and skill.is_loaded():
                self._skills_cache[uri] = skill
                return skill
        
        return None
    
    async def get_skill_content(self, skill_name: str) -> str:
        """
        获取 Skill 内容（便捷方法）
        
        Args:
            skill_name: Skill 名称
        
        Returns:
            Skill 内容
        """
        skill = await self.load_skill(skill_name)
        return skill.content if skill else ""
    
    async def load_relevant_skills(self, task: str, max_skills: int = 3) -> List[MCPSkill]:
        """
        根据任务加载相关的 Skills
        
        Args:
            task: 用户任务描述
            max_skills: 最多加载的 skill 数量
        
        Returns:
            相关的 MCPSkill 列表
        """
        # 确保 skills 已发现
        if not self._skills_cache:
            await self.discover_all_skills()
        
        task_lower = task.lower()
        relevant = []
        
        # 关键词匹配
        skill_keywords = {
            "desktop": ["screenshot", "click", "mouse", "keyboard", "screen", "gui", "桌面", "截图", "点击"],
            "browser": ["browser", "web", "navigate", "url", "page", "网页", "浏览器"],
            "shell": ["command", "shell", "terminal", "bash", "run", "命令", "终端"],
            "files": ["file", "read", "write", "save", "文件", "读取", "写入"],
            "memory": ["remember", "recall", "memory", "save", "记忆", "保存"],
            "software": ["app", "application", "launch", "open", "软件", "应用", "打开"],
            "wechat": ["wechat", "微信", "聊天", "消息"],
        }
        
        for uri, skill in self._skills_cache.items():
            skill_name = skill.name.replace("skill_", "")
            if skill_name in skill_keywords:
                keywords = skill_keywords[skill_name]
                if any(kw in task_lower for kw in keywords):
                    loaded_skill = await self.load_skill(uri)
                    if loaded_skill:
                        relevant.append(loaded_skill)
                        if len(relevant) >= max_skills:
                            break
        
        # 如果没有匹配，加载默认的 desktop skill
        if not relevant:
            desktop_skill = await self.load_skill("skill://desktop")
            if desktop_skill:
                relevant.append(desktop_skill)
        
        return relevant
    
    # ==================== Prompts API ====================
    
    async def list_all_prompts(self, use_cache: bool = True) -> List[MCPPrompt]:
        """
        从所有 Server 收集 Prompts
        
        Returns:
            所有 MCPPrompt 列表
        """
        if use_cache and self._prompts_cache is not None:
            return self._prompts_cache
        
        all_prompts = []
        for server_name, server in self.servers.items():
            prompts = await server.list_prompts(use_cache=use_cache)
            all_prompts.extend(prompts)
        
        self._prompts_cache = all_prompts
        return all_prompts
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """
        获取 Prompt 内容
        
        Args:
            name: Prompt 名称
            arguments: Prompt 参数
        
        Returns:
            Prompt 渲染后的内容
        """
        for server in self.servers.values():
            content = await server.get_prompt(name, arguments)
            if content:
                return content
        return ""
    
    # ==================== Full Discovery ====================
    
    async def full_discovery(self) -> Dict[str, Any]:
        """
        完整发现: Tools, Resources, Skills, Prompts
        
        Returns:
            包含所有发现结果的字典
        """
        tools = await self.list_all_tools(use_cache=False)
        resources = await self.list_all_resources(use_cache=False)
        skills = await self.discover_all_skills()
        prompts = await self.list_all_prompts(use_cache=False)
        
        return {
            "tools_count": len(tools),
            "resources_count": len(resources),
            "skills_count": len(skills),
            "prompts_count": len(prompts),
            "skills": [{"name": s.name, "uri": s.uri, "description": s.description} for s in skills]
        }
    
    async def close(self):
        """关闭"""
        self.servers.clear()
        self._clear_all_caches()
