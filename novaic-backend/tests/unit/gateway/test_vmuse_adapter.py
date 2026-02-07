"""
VMUSE 适配器单元测试

测试 VmuseAdapter 的功能和接口兼容性
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from gateway.clients.vmuse_adapter import VmuseAdapter, get_vmuse_adapter


class TestVmuseAdapter:
    """VmuseAdapter 单元测试"""
    
    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return VmuseAdapter(vmcontrol_url="http://test:8080", timeout=5.0)
    
    @pytest.fixture
    def mock_client(self, adapter):
        """Mock HTTP 客户端"""
        mock = AsyncMock()
        adapter.client = mock
        return mock
    
    # ==================== 初始化测试 ====================
    
    def test_init_default_url(self):
        """测试默认 URL 初始化"""
        with patch("gateway.clients.vmuse_adapter.ServiceConfig") as mock_config:
            mock_config.VMCONTROL_URL = "http://default:8080"
            adapter = VmuseAdapter()
            assert adapter.vmcontrol_url == "http://default:8080"
    
    def test_init_custom_url(self):
        """测试自定义 URL 初始化"""
        adapter = VmuseAdapter(vmcontrol_url="http://custom:9000")
        assert adapter.vmcontrol_url == "http://custom:9000"
    
    def test_init_custom_timeout(self):
        """测试自定义超时"""
        adapter = VmuseAdapter(timeout=60.0)
        assert adapter.timeout == 60.0
    
    # ==================== 浏览器操作测试 ====================
    
    @pytest.mark.asyncio
    async def test_browser_navigate_success(self, adapter, mock_client):
        """测试浏览器导航成功"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "url": "https://example.com"}
        mock_client.post.return_value = mock_response
        
        # Call
        result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"}, vm_id="1")
        
        # Assert
        assert result["success"] is True
        assert "result" in result
        mock_client.post.assert_called_once_with(
            "/api/vms/1/browser/navigate",
            json={"url": "https://example.com"}
        )
    
    @pytest.mark.asyncio
    async def test_browser_navigate_missing_url(self, adapter):
        """测试浏览器导航缺少 URL"""
        result = await adapter.call_tool("browser_navigate", {}, vm_id="1")
        
        assert result["success"] is False
        assert "Missing required parameter: url" in result["error"]
    
    @pytest.mark.asyncio
    async def test_browser_click_success(self, adapter, mock_client):
        """测试点击元素成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("browser_click", {"selector": "#button"}, vm_id="1")
        
        assert result["success"] is True
        mock_client.post.assert_called_once_with(
            "/api/vms/1/browser/click",
            json={"selector": "#button"}
        )
    
    @pytest.mark.asyncio
    async def test_browser_type_success(self, adapter, mock_client):
        """测试输入文本成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("browser_type", {
            "selector": "#input",
            "text": "test text"
        }, vm_id="1")
        
        assert result["success"] is True
        mock_client.post.assert_called_once_with(
            "/api/vms/1/browser/type",
            json={"selector": "#input", "text": "test text"}
        )
    
    @pytest.mark.asyncio
    async def test_browser_type_empty_text(self, adapter, mock_client):
        """测试输入空文本（应该允许）"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("browser_type", {
            "selector": "#input",
            "text": ""  # 空字符串应该被允许
        }, vm_id="1")
        
        assert result["success"] is True
    
    # ==================== 文件操作测试 ====================
    
    @pytest.mark.asyncio
    async def test_file_read_success(self, adapter, mock_client):
        """测试读取文件成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "file content",
            "size": 12
        }
        mock_client.get.return_value = mock_response
        
        result = await adapter.call_tool("file_read", {"path": "/tmp/test.txt"}, vm_id="1")
        
        assert result["success"] is True
        assert result["result"]["content"] == "file content"
        assert result["result"]["size"] == 12
        assert result["result"]["path"] == "/tmp/test.txt"
        mock_client.get.assert_called_once_with(
            "/api/vms/1/guest/file",
            params={"path": "/tmp/test.txt"}
        )
    
    @pytest.mark.asyncio
    async def test_file_write_success(self, adapter, mock_client):
        """测试写入文件成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("file_write", {
            "path": "/tmp/test.txt",
            "content": "new content"
        }, vm_id="1")
        
        assert result["success"] is True
        assert result["result"]["path"] == "/tmp/test.txt"
        assert result["result"]["bytes_written"] == len("new content")
        mock_client.post.assert_called_once_with(
            "/api/vms/1/guest/file",
            json={"path": "/tmp/test.txt", "content": "new content"}
        )
    
    @pytest.mark.asyncio
    async def test_file_write_empty_content(self, adapter, mock_client):
        """测试写入空内容"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("file_write", {
            "path": "/tmp/test.txt",
            "content": ""
        }, vm_id="1")
        
        assert result["success"] is True
        assert result["result"]["bytes_written"] == 0
    
    # ==================== Shell 操作测试 ====================
    
    @pytest.mark.asyncio
    async def test_shell_exec_success(self, adapter, mock_client):
        """测试执行命令成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exit_code": 0,
            "stdout": "command output",
            "stderr": ""
        }
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("shell_exec", {"command": "ls -la"}, vm_id="1")
        
        assert result["success"] is True
        assert result["result"]["exit_code"] == 0
        assert result["result"]["stdout"] == "command output"
        assert result["result"]["command"] == "ls -la"
        mock_client.post.assert_called_once_with(
            "/api/vms/1/guest/exec",
            json={"path": "/bin/bash", "args": ["-c", "ls -la"], "wait": True}
        )
    
    @pytest.mark.asyncio
    async def test_shell_exec_failure(self, adapter, mock_client):
        """测试执行命令失败"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exit_code": 1,
            "stdout": "",
            "stderr": "command not found"
        }
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("shell_exec", {"command": "invalid_cmd"}, vm_id="1")
        
        assert result["success"] is False  # exit_code != 0 means failure
        assert result["result"]["exit_code"] == 1
        assert result["result"]["stderr"] == "command not found"
    
    @pytest.mark.asyncio
    async def test_shell_exec_no_wait(self, adapter, mock_client):
        """测试异步执行命令"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"exit_code": 0, "stdout": "", "stderr": ""}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("shell_exec", {
            "command": "sleep 10",
            "wait": False
        }, vm_id="1")
        
        mock_client.post.assert_called_once_with(
            "/api/vms/1/guest/exec",
            json={"path": "/bin/bash", "args": ["-c", "sleep 10"], "wait": False}
        )
    
    # ==================== 截图测试 ====================
    
    @pytest.mark.asyncio
    async def test_screenshot_success(self, adapter, mock_client):
        """测试截图成功"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "image_data": "base64_data...",
            "format": "png",
            "width": 1920,
            "height": 1080
        }
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("screenshot", {}, vm_id="1")
        
        assert result["success"] is True
        assert result["result"]["format"] == "png"
        assert result["result"]["width"] == 1920
        assert result["result"]["height"] == 1080
        mock_client.post.assert_called_once_with("/api/vms/1/screenshot")
    
    # ==================== 错误处理测试 ====================
    
    @pytest.mark.asyncio
    async def test_unsupported_tool(self, adapter):
        """测试不支持的工具"""
        result = await adapter.call_tool("unsupported_tool", {}, vm_id="1")
        
        assert result["success"] is False
        assert "Unsupported tool" in result["error"]
    
    @pytest.mark.asyncio
    async def test_http_error(self, adapter, mock_client):
        """测试 HTTP 错误"""
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        
        result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"}, vm_id="1")
        
        assert result["success"] is False
        assert "HTTP error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unexpected_error(self, adapter, mock_client):
        """测试意外错误"""
        mock_client.post.side_effect = Exception("Unexpected error")
        
        result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"}, vm_id="1")
        
        assert result["success"] is False
        assert "Adapter error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_http_status_error(self, adapter, mock_client):
        """测试 HTTP 状态码错误"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"}, vm_id="1")
        
        assert result["success"] is False
        assert "HTTP error" in result["error"]
    
    # ==================== 工具列表测试 ====================
    
    def test_list_tools(self, adapter):
        """测试工具列表"""
        tools = adapter.list_tools()
        
        assert isinstance(tools, dict)
        assert "browser_navigate" in tools
        assert "browser_click" in tools
        assert "browser_type" in tools
        assert "file_read" in tools
        assert "file_write" in tools
        assert "shell_exec" in tools
        assert "screenshot" in tools
        
        # 检查工具定义格式
        for tool_name, tool_def in tools.items():
            assert "description" in tool_def
            assert "parameters" in tool_def
            assert isinstance(tool_def["parameters"], dict)
    
    # ==================== 客户端管理测试 ====================
    
    @pytest.mark.asyncio
    async def test_close(self, adapter, mock_client):
        """测试关闭客户端"""
        await adapter.close()
        mock_client.aclose.assert_called_once()


class TestGlobalAdapterInstance:
    """全局适配器实例测试"""
    
    def test_get_vmuse_adapter_singleton(self):
        """测试单例模式"""
        # 重置全局实例
        import gateway.clients.vmuse_adapter as adapter_module
        adapter_module._adapter_instance = None
        
        # 获取两次应该返回同一实例
        adapter1 = get_vmuse_adapter()
        adapter2 = get_vmuse_adapter()
        
        assert adapter1 is adapter2
    
    @pytest.mark.asyncio
    async def test_close_vmuse_adapter(self):
        """测试关闭全局实例"""
        from gateway.clients.vmuse_adapter import close_vmuse_adapter
        import gateway.clients.vmuse_adapter as adapter_module
        
        # 创建实例
        adapter = get_vmuse_adapter()
        assert adapter_module._adapter_instance is not None
        
        # 关闭
        await close_vmuse_adapter()
        assert adapter_module._adapter_instance is None


class TestIntegrationScenarios:
    """集成场景测试"""
    
    @pytest.fixture
    def adapter(self):
        return VmuseAdapter(vmcontrol_url="http://test:8080")
    
    @pytest.mark.asyncio
    async def test_browser_workflow(self, adapter):
        """测试浏览器操作流程"""
        mock_client = AsyncMock()
        adapter.client = mock_client
        
        # Mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        # 1. Navigate
        result = await adapter.call_tool("browser_navigate", {"url": "https://example.com"})
        assert result["success"] is True
        
        # 2. Click
        result = await adapter.call_tool("browser_click", {"selector": "#submit"})
        assert result["success"] is True
        
        # 3. Type
        result = await adapter.call_tool("browser_type", {
            "selector": "#username",
            "text": "admin"
        })
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_file_workflow(self, adapter):
        """测试文件操作流程"""
        mock_client = AsyncMock()
        adapter.client = mock_client
        
        # Write
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client.post.return_value = mock_response
        
        result = await adapter.call_tool("file_write", {
            "path": "/tmp/test.txt",
            "content": "Hello World"
        })
        assert result["success"] is True
        
        # Read
        mock_response.json.return_value = {"content": "Hello World", "size": 11}
        mock_client.get.return_value = mock_response
        
        result = await adapter.call_tool("file_read", {"path": "/tmp/test.txt"})
        assert result["success"] is True
        assert result["result"]["content"] == "Hello World"


# ==================== Pytest Configuration ====================

@pytest.fixture(autouse=True)
def reset_global_instance():
    """每个测试后重置全局实例"""
    yield
    import gateway.clients.vmuse_adapter as adapter_module
    adapter_module._adapter_instance = None
