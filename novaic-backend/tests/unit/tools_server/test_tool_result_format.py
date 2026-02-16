"""
Unit tests for unified tool result format (files_created, display_files)
and TRS _parse_tool_result parsing.
"""
import sys

sys.path.insert(0, "/Users/wangchaoqun/novaic/novaic-backend")

import pytest


class TestToolResult:
    """Test tool_result helper output format"""

    def test_screenshot_format(self):
        """screenshot: files_created + display_files both filled"""
        from tools_server.tool_result_adapter import tool_result

        file_ref = {"url": "/api/files/images/agent-1/screenshot.png", "filename": "screenshot.png", "modality": "image"}
        out = tool_result(
            text="screenshot captured.",
            files_created=[file_ref],
            display_files=[file_ref],
        )
        assert out["success"] is True
        assert out["text"] == "screenshot captured."
        assert out["files_created"] == [file_ref]
        assert out["display_files"] == [file_ref]
        assert out["file_url"] == file_ref["url"]

    def test_file_pull_format(self):
        """file_pull: files_created filled, display_files empty"""
        from tools_server.tool_result_adapter import tool_result

        file_ref = {"url": "/api/files/binaries/agent-1/file.txt", "filename": "file.txt", "modality": "resource"}
        out = tool_result(
            text="File pulled: file.txt (100 bytes).",
            files_created=[file_ref],
            display_files=[],
            extra={"size": 100},
        )
        assert out["files_created"] == [file_ref]
        assert out["display_files"] == []
        assert out.get("size") == 100

    def test_display_format(self):
        """display: files_created empty, display_files filled"""
        from tools_server.tool_result_adapter import tool_result

        file_ref = {"url": "/api/files/images/agent-1/existing.png", "filename": "existing.png", "modality": "image"}
        out = tool_result(
            text="Displaying file: existing.png.",
            files_created=[],
            display_files=[file_ref],
        )
        assert out["files_created"] == []
        assert out["display_files"] == [file_ref]

    def test_no_files_format(self):
        """file_push: both empty"""
        from tools_server.tool_result_adapter import tool_result

        out = tool_result(
            text="File pushed to VM.",
            extra={"path": "/tmp/x", "size": 100},
        )
        assert out["files_created"] == []
        assert out["display_files"] == []
        assert out.get("path") == "/tmp/x"


class TestTRSParseToolResult:
    """Test TRS _parse_tool_result with new format"""

    def _parse(self, raw):
        from task_queue.utils.trs_sdk import _parse_tool_result
        return _parse_tool_result(raw)

    def test_display_files_parse(self):
        """display: files_created empty -> text 不含 file_url"""
        raw = {
            "success": True,
            "text": "Displaying file.",
            "files_created": [],
            "display_files": [
                {"url": "/api/files/images/agent-1/x.png", "filename": "x.png", "modality": "image"}
            ],
        }
        parsed = self._parse(raw)
        assert parsed["text"] == "Displaying file."
        assert parsed["files_created"] == []
        assert len(parsed["display_files"]) == 1
        assert parsed["display_files"][0]["url"] == "/api/files/images/agent-1/x.png"

    def test_file_pull_only_text(self):
        """file_pull: display_files empty -> text includes file_url"""
        raw = {
            "success": True,
            "text": "File pulled: f.txt (100 bytes).",
            "files_created": [{"url": "/api/files/binaries/f.txt", "filename": "f.txt", "modality": "resource"}],
            "display_files": [],
        }
        parsed = self._parse(raw)
        assert "File pulled" in parsed["text"]
        assert "file_url: /api/files/binaries/f.txt" in parsed["text"]
        assert parsed["display_files"] == []

    def test_screenshot_includes_file_url_in_text(self):
        """screenshot: text includes file_url so LLM can call display() later"""
        raw = {
            "success": True,
            "text": "Mobile screenshot captured.",
            "files_created": [{"url": "/api/files/images/agent-1/screenshot.png", "filename": "screenshot.png", "modality": "image"}],
            "display_files": [{"url": "/api/files/images/agent-1/screenshot.png", "filename": "screenshot.png", "modality": "image"}],
        }
        parsed = self._parse(raw)
        assert "file_url: /api/files/images/agent-1/screenshot.png" in parsed["text"]
        assert len(parsed["display_files"]) == 1

    def test_legacy_files_compat(self):
        """Backward compat: old 'files' field -> display_files"""
        raw = {
            "success": True,
            "text": "Screenshot.",
            "files": [{"url": "/api/files/images/a.png", "filename": "a.png", "modality": "image"}],
        }
        parsed = self._parse(raw)
        assert "file_url: /api/files/images/a.png" in parsed["text"]
        assert len(parsed["display_files"]) == 1
        assert parsed["display_files"][0]["url"] == "/api/files/images/a.png"

    def test_string_input(self):
        """Plain string -> text only"""
        parsed = self._parse("Hello world")
        assert parsed["text"] == "Hello world"
        assert parsed["files_created"] == []
        assert parsed["display_files"] == []

    def test_none_input(self):
        """None -> empty"""
        parsed = self._parse(None)
        assert parsed["text"] == ""
        assert parsed["files_created"] == []
        assert parsed["display_files"] == []
