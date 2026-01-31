"""
Unit Tests for SubMCPManager

Tests the v2.6 three-layer MCP Server architecture:
- Shared layer: qemu, memory, chat, local (created at startup, never destroyed)
- Runtime layer: single-agent-runtime (created per Runtime, managed by Master)
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


def create_mock_server(name: str):
    """Create a mock MCP server."""
    mock_instance = MagicMock()
    mock_instance.name = name
    mock_instance.setup = MagicMock()
    mock_instance.get_asgi_app = MagicMock(return_value=MagicMock())
    return mock_instance


class TestSharedLayerManagement:
    """Tests for shared layer MCP servers."""
    
    @pytest.mark.asyncio
    async def test_create_shared_servers_creates_servers(self, mock_fastapi_app):
        """create_shared_servers creates shared servers."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            servers = await manager.create_shared_servers()
            
            # Should create at least 3 shared servers (local may fail in some envs)
            assert len(servers) >= 3
            assert 'memory' in servers
            assert 'chat' in servers
            assert 'qemudebug' in servers
    
    @pytest.mark.asyncio
    async def test_shared_servers_only_created_once(self, mock_fastapi_app):
        """Calling create_shared_servers twice only creates once."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            servers1 = await manager.create_shared_servers()
            servers2 = await manager.create_shared_servers()
            
            # Should be the same instances
            assert servers1 is servers2
            assert manager._shared_initialized is True
    
    @pytest.mark.asyncio
    async def test_get_shared_server(self, mock_fastapi_app):
        """get_shared_server returns the correct server."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            await manager.create_shared_servers()
            
            memory_server = manager.get_shared_server('memory')
            assert memory_server is not None
            assert memory_server.name == 'memory'
    
    @pytest.mark.asyncio
    async def test_get_shared_server_returns_none_if_not_exists(self, mock_fastapi_app):
        """get_shared_server returns None for non-existent server."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            await manager.create_shared_servers()
            
            unknown = manager.get_shared_server('unknown')
            assert unknown is None
    
    @pytest.mark.asyncio
    async def test_get_shared_mount_path(self, mock_fastapi_app):
        """get_shared_mount_path returns correct path."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            await manager.create_shared_servers()
            
            path = manager.get_shared_mount_path('memory')
            assert path == '/sub-mcp/memory'


class TestRuntimeLayerManagement:
    """Tests for Runtime layer MCP servers."""
    
    @pytest.mark.asyncio
    async def test_create_runtime_server(self, mock_fastapi_app):
        """create_runtime_server creates a new Runtime MCP server."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'), \
             patch('mcp_servers.manager.SingleAgentRuntimeMCPServer') as mock_runtime:
            
            mock_runtime.return_value = create_mock_server('single-agent-runtime')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            server = await manager.create_runtime_server(
                agent_id="agent-1",
                subagent_id="main-abc123",
                agent_index=0,
            )
            
            assert server is not None
            assert "main-abc123" in manager._runtime_servers
    
    @pytest.mark.asyncio
    async def test_create_runtime_server_idempotent(self, mock_fastapi_app):
        """Creating same Runtime server twice returns existing."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'), \
             patch('mcp_servers.manager.SingleAgentRuntimeMCPServer') as mock_runtime:
            
            mock_runtime.return_value = create_mock_server('single-agent-runtime')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            server1 = await manager.create_runtime_server(
                agent_id="agent-1",
                subagent_id="main-abc123",
            )
            server2 = await manager.create_runtime_server(
                agent_id="agent-1",
                subagent_id="main-abc123",
            )
            
            assert server1 is server2
    
    @pytest.mark.asyncio
    async def test_remove_runtime_server(self, mock_fastapi_app):
        """remove_runtime_server removes the Runtime server."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'), \
             patch('mcp_servers.manager.SingleAgentRuntimeMCPServer') as mock_runtime:
            
            mock_runtime.return_value = create_mock_server('single-agent-runtime')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            await manager.create_runtime_server(
                agent_id="agent-1",
                subagent_id="main-abc123",
            )
            
            assert "main-abc123" in manager._runtime_servers
            
            result = await manager.remove_runtime_server("main-abc123")
            
            assert result is True
            assert "main-abc123" not in manager._runtime_servers
    
    @pytest.mark.asyncio
    async def test_remove_runtime_server_returns_false_if_not_exists(self, mock_fastapi_app):
        """remove_runtime_server returns False for non-existent server."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'):
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            result = await manager.remove_runtime_server("nonexistent")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_runtime_server(self, mock_fastapi_app):
        """get_runtime_server returns the correct server."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'), \
             patch('mcp_servers.manager.SingleAgentRuntimeMCPServer') as mock_runtime:
            
            mock_runtime.return_value = create_mock_server('single-agent-runtime')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            await manager.create_runtime_server(
                agent_id="agent-1",
                subagent_id="main-test",
            )
            
            server = manager.get_runtime_server("main-test")
            assert server is not None
    
    @pytest.mark.asyncio
    async def test_get_runtime_mount_path(self, mock_fastapi_app):
        """get_runtime_mount_path returns correct path."""
        with patch('mcp_servers.manager.LocalMCPServer'), \
             patch('mcp_servers.manager.MemoryMCPServer'), \
             patch('mcp_servers.manager.ChatMCPServer'), \
             patch('mcp_servers.manager.QemuDebugMCPServer'):
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            path = manager.get_runtime_mount_path("sub-xyz")
            assert path == "/sub-mcp/runtime/sub-xyz"


class TestSubMCPManagerStats:
    """Tests for manager statistics."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_fastapi_app):
        """get_stats returns correct statistics."""
        with patch('mcp_servers.manager.LocalMCPServer') as mock_local, \
             patch('mcp_servers.manager.MemoryMCPServer') as mock_memory, \
             patch('mcp_servers.manager.ChatMCPServer') as mock_chat, \
             patch('mcp_servers.manager.QemuDebugMCPServer') as mock_qemu, \
             patch('mcp_servers.manager.SingleAgentRuntimeMCPServer') as mock_runtime:
            
            mock_local.return_value = create_mock_server('local')
            mock_memory.return_value = create_mock_server('memory')
            mock_chat.return_value = create_mock_server('chat')
            mock_qemu.return_value = create_mock_server('qemudebug')
            mock_runtime.return_value = create_mock_server('single-agent-runtime')
            
            from mcp_servers.manager import SubMCPManager
            manager = SubMCPManager(mock_fastapi_app)
            
            # Create shared and runtime servers
            await manager.create_shared_servers()
            await manager.create_runtime_server("agent-1", "main-1")
            await manager.create_runtime_server("agent-1", "sub-1")
            
            stats = manager.get_stats()
            
            # shared_servers is a list of server names
            assert len(stats["shared_servers"]) >= 3  # At least 3 (local may fail)
            assert stats["total_runtime_servers"] == 2
            assert "memory" in stats["shared_servers"]
            assert "main-1" in stats["runtime_servers"]
            assert "sub-1" in stats["runtime_servers"]
