"""
Unit tests for tool_result_adapter
"""
import sys

sys.path.insert(0, "/Users/wangchaoqun/novaic/novaic-backend")

import pytest
from unittest.mock import AsyncMock, patch


class TestToolResultAdapter:
    """Test adapt_tool_result"""

    @pytest.mark.asyncio
    async def test_screenshot_adapt(self):
        """screenshot: base64 -> url, display=True"""
        from tools_server.tool_result_adapter import adapt_tool_result, TOOL_ADAPTER_REGISTRY

        # 需要 mock File Service
        fake_url = "/api/files/images/agent-1/1234_abc.png"
        with patch("tools_server.tool_result_adapter._upload_base64_to_file_service", new_callable=AsyncMock, return_value=fake_url):
            # MIN_B64_LEN=100，需超过该长度
            raw = {"screenshot": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" + "A" * 20}
            result = await adapt_tool_result("screenshot", raw, "agent-1")
        assert result is not None
        assert result["success"] is True
        assert result["files_created"] == [{"url": fake_url, "filename": "1234_abc.png", "modality": "image"}]
        assert result["display_files"] == result["files_created"]
        assert "screenshot captured" in result["text"]

    @pytest.mark.asyncio
    async def test_unregistered_tool_returns_none(self):
        """未注册工具返回 None"""
        from tools_server.tool_result_adapter import adapt_tool_result

        raw = {"screenshot": "base64data..."}
        result = await adapt_tool_result("unknown_tool", raw, "agent-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_base64_returns_none(self):
        """无 base64 数据返回 None"""
        from tools_server.tool_result_adapter import adapt_tool_result

        raw = {"success": True, "text": "no image"}
        result = await adapt_tool_result("screenshot", raw, "agent-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_mcp_fallback_content_image(self):
        """MCP/未注册工具：content 中 type=image 可被兜底转换"""
        from tools_server.tool_result_adapter import adapt_tool_result

        # content 格式（MCP 常用）
        b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" + "A" * 20
        raw = {
            "content": [
                {"type": "text", "text": "some text"},
                {"type": "image", "data": b64, "mimeType": "image/png"},
            ]
        }
        with patch("tools_server.tool_result_adapter._upload_base64_to_file_service", new_callable=AsyncMock, return_value="/api/files/images/agent-1/mcp_abc.png"):
            result = await adapt_tool_result("some_mcp_tool", raw, "agent-1")
        assert result is not None
        assert result["success"] is True
        assert len(result["files_created"]) == 1
        assert "some_mcp_tool: content includes 1 image" in result["text"]

    @pytest.mark.asyncio
    async def test_clipboard_get_no_display(self):
        """clipboard_get: display_files 应为空（仅 files_created）"""
        from tools_server.tool_result_adapter import adapt_tool_result

        b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" + "A" * 20
        raw = {"content": [{"type": "image", "data": b64}]}
        with patch("tools_server.tool_result_adapter._upload_base64_to_file_service", new_callable=AsyncMock, return_value="/api/files/images/agent-1/clip.png"):
            result = await adapt_tool_result("clipboard_get", raw, "agent-1")
        assert result is not None
        assert result["files_created"]
        assert result["display_files"] == []  # clipboard: display=False
