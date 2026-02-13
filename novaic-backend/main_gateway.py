"""
NovAIC Backend 组件: Gateway - Main Entry Point

Backend 四组件（Gateway、Tools Server、Master、Worker）均由 Tauri 统一拉起。
本进程为 Gateway：API + DB，不含 MCP；Worker 由 Tauri 拉起。

- REST API (/api/*)
- SSE for real-time updates
- Static files (React Web UI)
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from common.utils.time import utc_now_iso

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

# ==================== Command Line Arguments ====================
# Parse command line arguments first to support Tauri's invocation style
# Usage: novaic-backend gateway --port 19999 --data-dir /path/to/data
parser = argparse.ArgumentParser(description='NovAIC Gateway')
parser.add_argument('command', nargs='?', default='gateway', help='Command (gateway)')
parser.add_argument('--port', type=int, default=19999, help='Gateway port')
parser.add_argument('--data-dir', type=str, help='Data directory')
args, unknown = parser.parse_known_args()

# Set NOVAIC_DATA_DIR from command line if provided
if args.data_dir:
    os.environ['NOVAIC_DATA_DIR'] = args.data_dir

# ==================== Environment Variables Debug ====================
print("[Gateway] === Environment Variables ===")
print(f"[Gateway] NOVAIC_DATA_DIR: {os.environ.get('NOVAIC_DATA_DIR', 'NOT SET')}")
print(f"[Gateway] NOVAIC_RESOURCE_DIR: {os.environ.get('NOVAIC_RESOURCE_DIR', 'NOT SET')}")
print(f"[Gateway] NOVAIC_TOOLS_SERVER_URL: {os.environ.get('NOVAIC_TOOLS_SERVER_URL', 'NOT SET')}")
print(f"[Gateway] Current working directory: {os.getcwd()}")
print(f"[Gateway] Executable path: {sys.executable}")
print("[Gateway] ===============================")

# ==================== Data Directory Setup ====================
# NOVAIC_DATA_DIR is required (passed from Tauri app via --data-dir or env var)
if not os.environ.get("NOVAIC_DATA_DIR"):
    print("[Gateway] ERROR: NOVAIC_DATA_DIR environment variable or --data-dir argument is required")
    print("[Gateway] Please start Gateway through the NovAIC app")
    sys.exit(1)

NOVAIC_DATA_DIR = os.environ["NOVAIC_DATA_DIR"]
print(f"[Gateway] Data directory: {NOVAIC_DATA_DIR}")

# ==================== Data Migration ====================
# Migrate data from old ~/.novaic/ to new $NOVAIC_DATA_DIR
def migrate_old_data():
    """Migrate data from ~/.novaic/ to $NOVAIC_DATA_DIR if needed"""
    old_dir = os.path.expanduser("~/.novaic")
    new_dir = NOVAIC_DATA_DIR
    
    if not os.path.exists(old_dir):
        return  # No old data to migrate
    
    if old_dir == new_dir:
        return  # Same directory, no migration needed
    
    print(f"[Gateway] Found old data directory: {old_dir}")
    print(f"[Gateway] Migrating to: {new_dir}")
    
    # Ensure new directory exists
    os.makedirs(new_dir, exist_ok=True)
    
    # Files/directories to migrate
    items_to_migrate = [
        "config.json",
        "agents.json",
        "logs",
        "vms",
        "images",
        "memory",  # MCP Memory storage
    ]
    
    migrated = []
    for item in items_to_migrate:
        old_path = os.path.join(old_dir, item)
        new_path = os.path.join(new_dir, item)
        
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                import shutil
                if os.path.isdir(old_path):
                    shutil.copytree(old_path, new_path)
                else:
                    shutil.copy2(old_path, new_path)
                migrated.append(item)
                print(f"[Gateway] Migrated: {item}")
            except Exception as e:
                print(f"[Gateway] Failed to migrate {item}: {e}")
    
    if migrated:
        print(f"[Gateway] Migration complete. Migrated {len(migrated)} items.")
        print(f"[Gateway] You can safely delete the old directory: {old_dir}")
    else:
        print(f"[Gateway] No migration needed (data already exists or nothing to migrate)")

# Run migration
migrate_old_data()

# ==================== Logging Setup ====================
LOG_DIR = os.path.join(NOVAIC_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log file with date
LOG_FILE = os.path.join(LOG_DIR, f"gateway-{datetime.utcnow().strftime('%Y%m%d')}.log")

# Open log file for appending
_log_file_handle = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)  # line buffered

# Custom stream that writes to both file and original stdout
class TeeStream:
    def __init__(self, file, stream):
        self.file = file
        self.stream = stream
    def write(self, data):
        if data:
            self.file.write(data)
            self.file.flush()
            if self.stream:
                try:
                    self.stream.write(data)
                    self.stream.flush()
                except:
                    pass  # Ignore if stdout is closed
    def flush(self):
        self.file.flush()
        if self.stream:
            try:
                self.stream.flush()
            except:
                pass
    def isatty(self):
        return False
    def fileno(self):
        return self.file.fileno()

# Redirect stdout and stderr to log file (captures all print statements)
sys.stdout = TeeStream(_log_file_handle, sys.__stdout__)
sys.stderr = TeeStream(_log_file_handle, sys.__stderr__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("gateway")
logger.info(f"Log file: {LOG_FILE}")
print(f"[Gateway] Stdout/stderr redirected to {LOG_FILE}")

import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gateway.api.routes import router as api_router
from gateway.api.agents import router as agents_router
from gateway.api.vm import router as vm_router
from gateway.api.internal import router as internal_router
from gateway.api.vmcontrol import router as vmcontrol_router
from gateway.config import get_config_manager

# Import database module
from gateway.db import init_database, close_database, run_migration

# Import core components
from gateway.core.task_manager import TaskManager, get_task_manager, set_task_manager

# Import v11 architecture components
from gateway.db.repositories.message import MessageRepository
from gateway.db.repositories.agent_state import AgentStateRepository

# v2.10: Master runs as separate service, no longer imported here


# Configuration
HOST = os.getenv("NOVAIC_HOST", "127.0.0.1")
# Use command line port if provided, otherwise env var, otherwise default
PORT = args.port if args.port != 19999 else int(os.getenv("NOVAIC_PORT", "19999"))
SOCKET_PATH = os.getenv("NOVAIC_SOCKET", "")  # Unix socket path, if set use UDS mode
DEBUG = os.getenv("NOVAIC_DEBUG", "false").lower() == "true"

# Global instances
task_manager: TaskManager = None

# v11 architecture instances
message_repo: MessageRepository = None
agent_state_repo: AgentStateRepository = None

# v2.10: Master runs as separate service (master_main.py)


# ==================== Component Accessors ====================

def get_task_mgr() -> TaskManager:
    """Get the global TaskManager instance."""
    return task_manager


def initialize_systems(config):
    """Initialize all system components."""
    global task_manager
    global message_repo, agent_state_repo
    
    # Get port configuration from first agent (or use defaults)
    from gateway.config.agents import get_agent_config_manager, allocate_ports_for_agent
    
    try:
        agent_mgr = get_agent_config_manager()
        agents = agent_mgr.list_agents()
        first_agent = agents[0] if agents else None
    except Exception as e:
        print(f"[Gateway] Warning: Could not get agent config: {e}")
        first_agent = None
    
    if first_agent:
        ports = first_agent.vm.ports
        print(f"[Gateway] Using ports from agent '{first_agent.name}' (ssh={first_agent.vm.ports.ssh})")
    else:
        ports = allocate_ports_for_agent(0)
        print(f"[Gateway] No agents found, using default ports (Agent 0)")
    
    # Initialize TaskManager (unified task system)
    def llm_factory(provider: str, api_base: str, api_key: str):
        """Create an LLM client for summary generation."""
        from gateway.core.llm_client import OpenAIClient, AnthropicClient, GoogleAIClient
        if provider == "anthropic":
            return AnthropicClient(api_key=api_key, base_url=api_base)
        elif provider == "google":
            return GoogleAIClient(api_key=api_key)
        else:
            return OpenAIClient(api_key=api_key, base_url=api_base)
    
    task_manager = TaskManager(
        subagent_manager=None,
        llm_factory=llm_factory,
    )
    set_task_manager(task_manager)
    print("[Gateway] TaskManager initialized")
    
    # Cleanup expired tasks on startup
    if task_manager:
        cleaned = task_manager.cleanup_expired()
        if cleaned:
            print(f"[Gateway] Cleaned up {cleaned} expired tasks on startup")
    
    # ==================== Initialize New Architecture ====================
    # Initialize repositories
    from gateway.db.repositories import get_message_repo, get_agent_state_repo
    message_repo = get_message_repo()
    agent_state_repo = get_agent_state_repo()
    print("[Gateway] MessageRepository and AgentStateRepository initialized")
    
    # v11: Agent processing now handled by Worker processes (started by Tauri)
    # The old AgentRunner has been removed in favor of the multi-process architecture
    if first_agent:
        # Ensure agent state exists
        agent_state_repo.ensure_exists(first_agent.id)
        print(f"[Gateway] Agent state initialized for {first_agent.id}")
    else:
        print("[Gateway] Warning: No agents found")


def shutdown_systems():
    """Shutdown all system components."""
    # v2: Most components are now separate processes
    pass


_cleanup_task: Optional[asyncio.Task] = None


async def periodic_task_cleanup():
    """Periodically clean up expired tasks (runs every hour)."""
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            
            from gateway.core.task_manager import get_task_manager
            tm = get_task_manager()
            if tm:
                cleaned = tm.cleanup_expired()
                if cleaned:
                    print(f"[Gateway] Periodic cleanup: removed {cleaned} expired tasks")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Gateway] Periodic cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    from contextlib import AsyncExitStack
    
    global _cleanup_task
    
    if SOCKET_PATH:
        print(f"🚀 NovAIC Gateway starting on unix://{SOCKET_PATH}")
    else:
        print(f"🚀 NovAIC Gateway starting on http://{HOST}:{PORT}")
    
    # Initialize database
    print("[Gateway] Initializing database...")
    db = init_database()
    print(f"[Gateway] Database initialized: {db.db_path}")
    
    # Run migrations (from file-based storage to SQLite)
    print("[Gateway] Checking for data migrations...")
    migration_results = run_migration(db)
    if any(migration_results.values()):
        print(f"[Gateway] Migrations completed: {migration_results}")
    else:
        print("[Gateway] No migrations needed")
    
    # Load config (now from database)
    config = get_config_manager().load()
    print(f"🤖 Default model: {config.default_model}")
    
    # Initialize all systems
    initialize_systems(config)
    
    # 工具服务由 Tools Server（main_tools.py）提供
    print("[Gateway] 工具服务由 Tools Server 提供")
    
    # Recover VM processes (check for running VMs from previous Gateway session)
    try:
        from gateway.vm import get_vm_manager
        vm_manager = get_vm_manager()
        vm_manager.recover_processes()
        print("[Gateway] VM process recovery complete")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to recover VM processes: {e}")
    
    # Start periodic cleanup task
    _cleanup_task = asyncio.create_task(periodic_task_cleanup())
    print("[Gateway] Periodic task cleanup started (every hour)")
    
    # Initialize Worker SSE broadcaster (v11)
    from gateway.sse import init_worker_broadcaster, shutdown_worker_broadcaster
    await init_worker_broadcaster()
    print("[Gateway] Worker SSE broadcaster initialized")
    
    # v2.0: Task Queue and Saga are now managed by Queue Service (port 19997)
    # Gateway only handles business logic and interacts with Queue Service via HTTP
    print("[Gateway] Task Queue v2.0: Managed by Queue Service (port 19997)")
    print("[Gateway] Workers connect to Queue Service directly")
    
    # Gateway is ready
    print("[Gateway] Ready (v2.0 - Queue Service architecture)")
    
    yield
    
    # Cancel cleanup task
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            _cleanup_task
        except asyncio.CancelledError:
            pass
        print("[Gateway] Periodic task cleanup stopped")
    
    # Shutdown Worker SSE broadcaster (v11)
    from gateway.sse import shutdown_worker_broadcaster
    await shutdown_worker_broadcaster()
    print("[Gateway] Worker SSE broadcaster shutdown")
    
    # Close vmcontrol client
    try:
        from gateway.clients.vmcontrol import close_vmcontrol_client
        await close_vmcontrol_client()
        print("[Gateway] VmControl client closed")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to close VmControl client: {e}")
    
    # v2.0: Queue Service handles its own shutdown
    print("[Gateway] Shutdown complete (v2.0)")
    
    # Stop all VMs (graceful shutdown)
    try:
        from gateway.vm import get_vm_manager
        vm_manager = get_vm_manager()
        await vm_manager.stop_all()
        print("[Gateway] All VMs stopped")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to stop VMs: {e}")
    
    # Shutdown all systems
    shutdown_systems()
    
    # Close database
    close_database()
    print("[Gateway] Database closed")
    
    print("👋 NovAIC Gateway shutting down")


app = FastAPI(
    title="NovAIC Gateway",
    description="Unified control plane for NovAIC AI Agent",
    version="0.4.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api")

# Agents API routes (already has /api/agents prefix)
app.include_router(agents_router)

# Skills API routes
from gateway.api.skills import router as skills_router
app.include_router(skills_router)

# VM API routes (already has /api/vm prefix)
app.include_router(vm_router)

# VmControl proxy routes (already has /api/vmcontrol prefix)
app.include_router(vmcontrol_router)

# Internal API routes (v2.10 - for services, has /internal prefix)
app.include_router(internal_router)


# Root endpoint
@app.get("/api")
def api_root():
    """API root endpoint"""
    return {
        "name": "NovAIC Gateway",
        "version": "2.0.0",
        "description": "NovAIC AI Agent Gateway (v2 Saga/Task Architecture)",
        "components": {
            "tools": "separate Tools Server process",
            "workers": "separate Watchdog/Task/Saga/Health worker processes",
        }
    }


# System status endpoint
@app.get("/api/system/status")
def system_status():
    """Get detailed system status"""
    return {
        "tools": "separate Tools Server process",
        "architecture": "v2 Saga/Task",
    }


# ==================== Unified Task API ====================

@app.post("/api/internal/tasks")
def create_task(data: dict):
    """Create a new task (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    agent_id = data.get("agent_id")
    if not agent_id:
        return {"error": "agent_id is required", "success": False}
    
    return task_manager.spawn(
        task_type=data.get("task_type", "agent"),
        config=data.get("task_config", {}),
        label=data.get("label"),
        timeout_seconds=data.get("timeout_seconds", 0),
        notify_on=data.get("notify_on", ["complete", "error"]),
        parent_session_key=data.get("parent_session_key", "main"),
        agent_id=agent_id,
    )


@app.get("/api/internal/tasks/{task_id}")
def get_task_status(task_id: str, include_outputs: bool = False, output_limit: int = 50):
    """Get task status (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    return task_manager.get_status(
        task_id=task_id,
        include_outputs=include_outputs,
        output_limit=output_limit,
    )


@app.get("/api/internal/tasks")
def list_tasks(status: str = None, agent_id: str = None):
    """List tasks (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    status_filter = status.split(",") if status else None
    return task_manager.get_status(
        task_id=None,
        status_filter=status_filter,
        agent_id=agent_id,
    )


@app.get("/api/internal/tasks/{task_id}/result")
def get_task_result(task_id: str, format: str = "summary"):
    """Get task result (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    return task_manager.get_result(
        task_id=task_id,
        format=format,
    )


@app.post("/api/internal/tasks/{task_id}/cancel")
def cancel_task(task_id: str, data: dict = None):
    """Cancel a task (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    reason = data.get("reason") if data else None
    return task_manager.cancel(
        task_id=task_id,
        reason=reason,
    )


# ==================== Trigger Management API ====================

# ==================== Chat MCP API ====================

# ==================== Chat MCP API (Agent <-> User Communication) ====================

import asyncio
from fastapi.responses import StreamingResponse
import json as json_module
from typing import Dict, Any, Optional
import uuid as uuid_module

# Import ChatService for database-backed state management
from gateway.api.chat_service import get_chat_service, ChatService

# SSE subscribers (runtime state - cannot be persisted)
_chat_subscribers: Dict[str, asyncio.Queue] = {}  # Chat SSE subscribers
_log_subscribers: Dict[str, asyncio.Queue] = {}   # Log SSE subscribers

# Note: v11 - Agent execution handled by Worker processes (started by Tauri)


def broadcast_chat_message(message: Dict[str, Any], agent_id: Optional[str] = None):
    """Broadcast a chat message to all SSE subscribers and save to database.
    
    Note: Non-persistent message types (STATUS_UPDATE, TYPING, etc.) are only
    broadcast to SSE subscribers and not saved to database.
    
    Args:
        message: The message to broadcast
        agent_id: Optional agent ID. If not provided, tries to get from message.
                  If no agent_id available, logs warning and skips database save.
    """
    chat_service = get_chat_service()
    
    # Use provided agent_id, then message's agent_id
    if agent_id is None:
        agent_id = message.get("agent_id")
    
    # Add/update agent_id in message for frontend filtering
    message["agent_id"] = agent_id
    
    # Extract message info
    msg_type = message.get("type", "UNKNOWN")
    msg_id = message.get("id", str(uuid_module.uuid4())[:12])
    timestamp = message.get("timestamp", utc_now_iso())
    content = message.get("content", message.get("message"))
    
    # Debug: log content extraction
    print(f"[Broadcast] type={msg_type}, content_from_content={message.get('content')}, content_from_message={message.get('message')}, final_content={content[:50] if content else 'EMPTY'}")
    
    # Build metadata from remaining fields
    metadata = {k: v for k, v in message.items() 
                if k not in ("id", "type", "timestamp", "content", "message")}
    
    # Agent-originated messages should be marked as read
    # (USER_MESSAGE is unread, AGENT_* are auto-read to avoid Monitor re-wake loops)
    is_agent_message = msg_type.startswith("AGENT_")
    
    # Save to database only if agent_id is available
    if agent_id:
        # Save to database (ChatRepository handles non-persistent types)
        chat_service.repo.add_message(
            agent_id=agent_id,
            id=msg_id,
            type=msg_type,
            content=content,
            read=is_agent_message,  # Agent messages auto-read
            metadata=metadata if metadata else None,
            timestamp=timestamp,
        )
    else:
        # Log warning but continue with SSE broadcast
        logger.warning(f"[Gateway] broadcast_chat_message: No agent_id provided, skipping database save for message type={msg_type}")
    
    # Broadcast to SSE subscribers (always do this regardless of agent_id)
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass


def update_message_status(message_id: str, status: str):
    """Update message status and broadcast to subscribers.
    
    For 'read' status, marks the message as read in the database.
    STATUS_UPDATE is broadcast to SSE but not persisted.
    """
    chat_service = get_chat_service()
    
    # Update in database - for 'read' status, use mark_as_read
    if status == "read":
        chat_service.repo.mark_as_read(message_id)
    
    # Broadcast status update (not persisted, just for real-time UI)
    status_update = {
        "id": str(uuid_module.uuid4())[:8],
        "type": "STATUS_UPDATE",
        "message_id": message_id,
        "status": status,
        "timestamp": utc_now_iso(),
    }
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(status_update)
        except asyncio.QueueFull:
            pass


def broadcast_log(log: Dict[str, Any], agent_id: Optional[str] = None) -> Optional[int]:
    """Write execution log to DB and notify SSE subscribers (lightweight: only log_id).
    
    SSE 只推送「有更新」通知（event + log_id + subagent_id），前端再 GET /api/logs/entries 拉取内容。
    
    支持的字段：
    - agent_id: Agent ID
    - subagent_id: Subagent ID (默认 'main')
    - type: 日志类型 (保留兼容)
    - kind: 新事件类型 'think' | 'tool'
    - status: 状态 'running' | 'complete'
    - event_key: 唯一业务键 (用于 upsert)
    - data: 通用数据
    - input_data 或 input: 输入数据 (可选，兼容两种字段名)
    - result_data 或 result: 结果数据 (可选，兼容两种字段名)
    """
    chat_service = get_chat_service()
    if agent_id is None:
        agent_id = log.get("agent_id")
    if not agent_id:
        logger.warning("[Gateway] broadcast_log: No agent_id provided, skipping database save")
        return None
    
    # 提取新字段
    subagent_id = log.get("subagent_id", "main")
    kind = log.get("kind")
    status = log.get("status")
    event_key = log.get("event_key")
    # 兼容两种字段名：client 发送的是 input_data/result_data，旧代码可能用 input/result
    input_data = log.get("input_data") or log.get("input")
    result_data = log.get("result_data") or log.get("result")
    
    # 如果有 event_key，使用 upsert 方法
    if event_key:
        row_id = chat_service.repo.upsert_execution_log(
            agent_id=agent_id,
            subagent_id=subagent_id,
            event_key=event_key,
            type=log.get("type", "unknown"),
            kind=kind,
            status=status,
            data=log.get("data"),
            input_data=input_data,
            result_data=result_data,
        )
    else:
        # 传统方式：直接插入
        row_id = chat_service.repo.add_execution_log(
            agent_id=agent_id,
            type=log.get("type", "unknown"),
            timestamp=log.get("timestamp", utc_now_iso()),
            data=log.get("data"),
        )
    
    # SSE 通知包含 subagent_id 便于前端过滤
    notification = {
        "event": "logs_updated",
        "agent_id": agent_id,
        "subagent_id": subagent_id,
        "log_id": row_id,
    }
    for queue in _log_subscribers.values():
        try:
            queue.put_nowait(notification)
        except asyncio.QueueFull:
            pass
    return row_id


@app.post("/api/logs/broadcast")
def receive_log_broadcast(data: dict):
    """
    Receive execution log broadcasts from Workers.
    
    Called by Workers to broadcast tool execution status (thinking, tool_start, tool_end).
    
    请求体字段：
    - agent_id: str (必需)
    - subagent_id: str (可选，默认 'main')
    - type: str (保留兼容，日志类型)
    - kind: str (新增: 'think' | 'tool')
    - status: str (新增: 'running' | 'complete')
    - event_key: str (新增: 唯一业务键，用于 upsert)
    - data: dict (通用数据)
    - input: dict (新增可选: 输入数据)
    - result: dict (新增可选: 结果数据)
    
    逻辑：
    - 调用 ChatRepository 的 upsert_execution_log 方法 (如果有 event_key)
    - 向 SSE 推送轻量通知：{"event": "logs_updated", "agent_id": ..., "subagent_id": ..., "log_id": ...}
    """
    # Debug: log incoming request
    print(f"[Gateway] receive_log_broadcast: agent_id={data.get('agent_id')}, kind={data.get('kind')}, status={data.get('status')}, event_key={data.get('event_key')}")
    
    # Extract agent_id from data
    agent_id = data.pop("agent_id", None)
    
    if not agent_id:
        logger.warning("[Gateway] receive_log_broadcast: No agent_id in data, broadcast will skip database save")
    
    # Broadcast the log (pass agent_id as parameter)
    # 保留所有字段传递给 broadcast_log，包括新字段
    log_id = broadcast_log({
        **data,
        "agent_id": agent_id,
    }, agent_id=agent_id)
    
    print(f"[Gateway] receive_log_broadcast: log_id={log_id}, agent_id={agent_id}")
    
    return {
        "success": True,
        "log_id": log_id,
        "subagent_id": data.get("subagent_id", "main"),
    }


@app.post("/api/chat/event")
def receive_chat_event(data: dict):
    """
    Receive chat events from novaic-mcp-chat.
    
    This is called when the Agent uses chat tools (chat_reply, chat_ask, etc.)
    Events are stored and broadcast to all SSE subscribers.
    
    Note: agent_id should be included in data or event_data by the caller.
    """
    event_type = data.get("type", "")
    event_data = data.get("data", {})
    
    # Debug: log incoming data
    print(f"[ChatEvent] Received: type={event_type}, data_keys={list(event_data.keys())}, message={event_data.get('message', 'N/A')[:50] if event_data.get('message') else 'EMPTY'}")
    
    # Generate message ID and timestamp
    message_id = str(uuid_module.uuid4())[:12]
    timestamp = utc_now_iso()
    
    # Create chat message
    chat_message = {
        "id": message_id,
        "type": event_type,
        "timestamp": timestamp,
        **event_data
    }
    
    # Get agent_id from data or event_data
    agent_id = data.get("agent_id") or event_data.get("agent_id")
    
    if not agent_id:
        logger.warning(f"[Gateway] receive_chat_event: No agent_id provided for event type={event_type}")
    
    # Handle AGENT_ASK specially - store pending question in database
    if event_type == "AGENT_ASK":
        if not agent_id:
            logger.warning("[Gateway] receive_chat_event: Cannot store AGENT_ASK without agent_id")
        else:
            request_id = event_data.get("request_id") or message_id
            chat_service = get_chat_service()
            chat_service.repo.add_pending_question(
                agent_id=agent_id,
                request_id=request_id,
                question=event_data.get("question"),
                options=event_data.get("options"),
                message_id=message_id,
            )
            chat_message["request_id"] = request_id
    
    # Use helper to store and broadcast (pass agent_id for correct routing)
    broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "message_id": message_id,
        "request_id": chat_message.get("request_id"),
    }


@app.get("/api/chat/messages")
def chat_messages_sse(agent_id: str = None):
    """
    SSE endpoint for real-time chat messages (Agent -> User).
    
    Frontend connects to this to receive:
    - Agent replies (AGENT_REPLY)
    - Agent questions (AGENT_ASK)
    - Agent notifications (AGENT_NOTIFY)
    - Agent images (AGENT_IMAGE)
    
    Args:
        agent_id: Required. Only messages for this agent will be pushed.
    """
    from fastapi.responses import JSONResponse
    
    # Validate agent_id is provided
    if not agent_id:
        return JSONResponse(
            status_code=400,
            content={"error": "agent_id parameter is required"}
        )
    
    subscriber_id = str(uuid_module.uuid4())[:8]
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _chat_subscribers[subscriber_id] = queue
    
    async def event_generator():
        try:
            # Send recent messages first (from database, filtered by agent_id)
            chat_service = get_chat_service()
            recent_messages = chat_service.repo.get_recent_chat_messages(agent_id, limit=10)
            for msg in recent_messages:
                yield f"data: {json_module.dumps(msg)}\n\n"
            
            # Stream new messages (filtered by agent_id)
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    # Filter: only push messages for the specified agent_id
                    if message.get("agent_id") == agent_id:
                        yield f"data: {json_module.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            # Cleanup on disconnect
            _chat_subscribers.pop(subscriber_id, None)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/chat/response/{request_id}")
def check_user_response(request_id: str):
    """
    Check if user has responded to an agent's question.
    
    Called by novaic-mcp-chat's chat_ask tool to poll for user response.
    """
    chat_service = get_chat_service()
    
    # Check if question exists
    question = chat_service.repo.get_pending_question(request_id)
    if not question:
        return {"error": "Question not found", "has_response": False}
    
    # Check for response
    response = chat_service.repo.get_question_response(request_id)
    if response:
        # Remove question and response after retrieval
        chat_service.repo.delete_pending_question(request_id)
        chat_service.repo.delete_question_response(request_id)
        return {"has_response": True, **response}
    
    return {"has_response": False}


@app.post("/api/chat/respond/{request_id}")
def submit_user_response(request_id: str, data: dict):
    """
    Submit user's response to an agent's question.
    
    Called by frontend when user answers a question from the agent.
    """
    chat_service = get_chat_service()
    
    # Check if question exists
    question = chat_service.repo.get_pending_question(request_id)
    if not question:
        return {"error": "Question not found or expired", "success": False}
    
    # Store response in database
    timestamp = utc_now_iso()
    chat_service.repo.add_question_response(
        request_id=request_id,
        response=data.get("response", ""),
        selected_option=data.get("selected_option"),
    )
    
    return {"success": True, "request_id": request_id}


@app.get("/api/chat/pending-questions")
def get_pending_questions(agent_id: str):
    """Get all pending questions from the agent.
    
    Args:
        agent_id: Agent ID (required query parameter)
    """
    if not agent_id:
        return {"error": "agent_id is required", "questions": []}
    
    chat_service = get_chat_service()
    questions = chat_service.repo.get_all_pending_questions(agent_id)
    return {
        "questions": questions
    }


@app.get("/api/chat/history")
def get_chat_history(
    agent_id: str,
    limit: int = 20,
    before_id: str = None,
    message_type: str = None,
    summary_length: int = 50
):
    """
    Get chat history between agent and user (with optional summary).
    
    Args:
        agent_id: Agent ID (required query parameter)
        limit: Maximum number of messages (default: 20, max: 100)
        before_id: Get messages before this ID (for pagination)
        message_type: Filter by type: "user", "agent", "notification"
        summary_length: Truncate message content to this length (0 for full)
    """
    if not agent_id:
        return {"error": "agent_id is required", "messages": [], "has_more": False}
    
    limit = min(limit, 100)
    chat_service = get_chat_service()
    
    # Build type filter
    type_filter = None
    if message_type:
        type_map = {
            "user": ["USER_MESSAGE"],
            "agent": ["AGENT_REPLY", "AGENT_IMAGE"],
            "notification": ["AGENT_NOTIFY"],
            "question": ["AGENT_ASK"],
        }
        type_filter = type_map.get(message_type, [message_type.upper()])
    
    # Get messages from database
    all_messages = chat_service.repo.get_chat_history(
        agent_id=agent_id,
        limit=limit + 1,  # Get one extra to check has_more
        before_id=before_id,
        type_filter=type_filter,
    )
    
    # Repository returns messages in chronological order (oldest first, newest last)
    # after reversing the DESC-ordered query results.
    # So we need to take the last 'limit' messages (newest ones).
    has_more = len(all_messages) > limit
    messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
    
    # Create summarized messages
    summarized = []
    for msg in messages:
        content = msg.get("message") or msg.get("question") or msg.get("content") or ""
        is_truncated = summary_length > 0 and len(content) > summary_length
        
        summary_msg = {
            "id": msg.get("id"),
            "type": msg.get("type"),
            "timestamp": msg.get("timestamp"),
            "summary": content[:summary_length] + "..." if is_truncated else content,
            "is_truncated": is_truncated,
            "read": msg.get("read", False),  # Include read status for frontend
        }
        # Include level for notifications
        if msg.get("level"):
            summary_msg["level"] = msg.get("level")
        # Include options count for questions
        if msg.get("options"):
            summary_msg["options_count"] = len(msg.get("options"))
        
        summarized.append(summary_msg)
    
    # Get total count
    total_count = chat_service.repo.get_chat_message_count(agent_id)
    
    return {
        "success": True,
        "messages": summarized,
        "has_more": has_more,
        "total_count": total_count,
    }


@app.get("/api/chat/message/{message_id}")
def get_chat_message(message_id: str):
    """
    Get full content of a specific chat message.
    
    Args:
        message_id: The message ID
    """
    chat_service = get_chat_service()
    msg = chat_service.repo.get_chat_message(message_id)
    
    if msg:
        return {"success": True, **msg}
    
    return {"success": False, "error": "Message not found"}


# ==================== Unified Inbox API (All messages to Agent) ====================
# v11: Uses MessageRepository and SSE broadcast for Worker processing

@app.post("/api/inbox")
def add_to_inbox(data: dict):
    """
    Unified API for adding messages to Agent's inbox.
    
    v11: Uses MessageRepository and broadcasts to Worker SSE.
    
    Request body:
    - type: Message type (USER_MESSAGE, SYSTEM_MESSAGE, WEBHOOK, CRON_TRIGGER, SUBAGENT_RESULT)
    - content: Message content
    - priority: Optional priority (stored in metadata)
    - source: Optional source identifier
    - metadata: Optional additional data
    - agent_id: Optional target agent ID (defaults to current agent)
    
    Response:
    - success: Boolean
    - message_id: ID of the created message
    - timestamp: Creation timestamp
    """
    msg_type = data.get("type", "USER_MESSAGE")
    content = data.get("content", "").strip()
    metadata = data.get("metadata", {})
    agent_id = data.get("agent_id")
    
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    
    if not content:
        return {"success": False, "error": "Content is required"}
    
    # Add model/api_key_id to metadata if provided
    if data.get("model"):
        metadata["model"] = data.get("model")
    if data.get("api_key_id"):
        metadata["api_key_id"] = data.get("api_key_id")
    if data.get("source"):
        metadata["source"] = data.get("source")
    if data.get("priority"):
        metadata["priority"] = data.get("priority")
    
    try:
        # 1. Store message using MessageRepository
        msg = message_repo.add_message(
            agent_id=agent_id,
            type=msg_type,
            content=content,
            metadata=metadata,
        )
        
        # 2. Broadcast to SSE (for UI display)
        broadcast_chat_message({
            "id": msg["id"],
            "type": msg_type,
            "timestamp": msg["timestamp"],
            "content": content,
        }, agent_id=agent_id)
        
        # v12: No broadcast_new_message needed
        # Monitor polls for unread messages and creates Runtimes
        # Master drives the ReACT loop
        
        return {
            "success": True,
            "message_id": msg["id"],
            "timestamp": msg["timestamp"],
            "status": "queued",  # v12: queued for Monitor to pick up
        }
    
    except Exception as e:
        print(f"[Inbox] Error adding message: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/inbox/summary")
def get_inbox_summary(agent_id: str):
    """
    Get inbox summary for the specified agent.
    
    Args:
        agent_id: Agent ID (required query parameter)
    
    v11: Uses MessageRepository to get pending (unclaimed, unprocessed) messages.
    
    Returns:
    - pending_count: Number of pending messages
    - messages: List of pending messages (truncated content)
    """
    if not agent_id:
        return {"success": False, "error": "agent_id is required", "pending_count": 0, "messages": []}
    
    try:
        # Get pending messages (unclaimed, unread)
        rows = message_repo.get_pending_unclaimed(agent_id, limit=20)
        
        messages = []
        for row in rows:
            content = row.get("content", "")
            messages.append({
                "id": row["id"],
                "type": row["type"],
                "content": content[:100] + "..." if len(content) > 100 else content,
                "timestamp": row["timestamp"],
            })
        
        return {
            "success": True,
            "pending_count": len(messages),
            "messages": messages,
        }
    except Exception as e:
        print(f"[Inbox] Error getting summary: {e}")
        return {"success": False, "error": str(e)}


# ==================== User Chat API (User -> Agent Communication) ====================
# v11: Message stored + broadcast to Worker SSE for processing

@app.post("/api/chat/send")
def send_chat_message(data: dict):
    """
    Send a user message.
    
    v11 architecture:
    1. Store message to chat_messages (read=0)
    2. Broadcast to UI SSE and Worker SSE
    3. Worker will claim and process via /api/claim/message
    
    Returns immediately with message_id.
    """
    agent_id = data.get("agent_id")
    
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    
    content = data.get("message", "").strip()
    model = data.get("model")
    api_key_id = data.get("api_key_id")
    
    if not content:
        return {"success": False, "error": "Message content required"}
    
    # 1. Store message using MessageRepository
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="USER_MESSAGE",
        content=content,
        metadata={"model": model, "api_key_id": api_key_id},
    )
    
    # 2. Broadcast to SSE directly (skip broadcast_chat_message to avoid double DB write)
    user_msg = {
        "id": msg["id"],
        "type": "USER_MESSAGE",
        "content": content,
        "timestamp": msg["timestamp"],
        "status": "delivered",
        "agent_id": agent_id,
    }
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(user_msg)
        except asyncio.QueueFull:
            pass
    
    # 3. Auto-respond to any pending questions (best-effort, don't fail the send)
    try:
        chat_service = get_chat_service()
        pending_questions = chat_service.repo.get_all_pending_questions(agent_id)
        if pending_questions:
            for q in pending_questions:
                request_id = q.get("request_id")
                try:
                    chat_service.repo.add_question_response(
                        agent_id=agent_id,
                        request_id=request_id,
                        response=content,
                        selected_option=None,
                    )
                    print(f"[Chat] Auto-responded to pending question {request_id}")
                except Exception as e:
                    print(f"[Chat] Failed to respond to question {request_id}: {e}")
    except Exception as e:
        print(f"[Chat] Error handling pending questions: {e}")
    
    # v12: No broadcast_new_message needed
    # Monitor polls for unread messages and creates Runtimes
    
    print(f"[Chat] Message {msg['id']} stored, Monitor will detect and process")
    
    return {
        "success": True,
        "message_id": msg["id"],
        "status": "queued",
        "timestamp": msg["timestamp"],
    }


@app.get("/api/logs/entries")
def get_log_entries(
    agent_id: str = Query(..., description="Agent ID"),
    subagent_id: Optional[str] = Query(None, description="Subagent ID (optional, filter by subagent)"),
    after_id: Optional[int] = Query(None, description="Return entries with id > after_id (incremental fetch)"),
    before_id: Optional[int] = Query(None, description="Return entries with id < before_id (pagination for older logs)"),
    limit: int = Query(50, ge=1, le=100, description="Max entries to return"),
):
    """
    分页拉取执行日志。前端用 after_id 增量拉取，before_id 加载更多历史日志。
    
    参数：
    - agent_id: Agent ID (必需)
    - subagent_id: Subagent ID (可选，若传入则只返回该 subagent 的日志)
    - after_id: 返回 id > after_id 的记录 (增量拉取)
    - before_id: 返回 id < before_id 的记录 (向前翻页加载更多)
    - limit: 最大返回条数 (1-100)
    
    返回的每条记录包含：
    - id, agent_id, type, timestamp, data (原有字段)
    - subagent_id, kind, status, event_key, input, result (新增字段)
    - has_more: 是否还有更多历史日志 (当使用 before_id 时)
    """
    if not agent_id:
        return {"success": False, "error": "agent_id required", "entries": [], "has_more": False}
    chat_service = get_chat_service()
    
    # Fetch limit + 1 to check if there are more entries
    fetch_limit = limit + 1 if before_id is not None else limit
    
    if after_id is not None:
        entries = chat_service.repo.get_execution_logs_after(
            agent_id, after_id, limit=fetch_limit, subagent_id=subagent_id
        )
        return {"success": True, "entries": entries, "has_more": False}
    elif before_id is not None:
        entries = chat_service.repo.get_execution_logs(
            agent_id, subagent_id=subagent_id, before_id=before_id, limit=fetch_limit
        )
        # Check if there are more entries (we fetched limit + 1)
        has_more = len(entries) > limit
        if has_more:
            entries = entries[1:]  # Remove the oldest one (first in list after reverse)
        return {"success": True, "entries": entries, "has_more": has_more}
    else:
        entries = chat_service.repo.get_recent_execution_logs(
            agent_id, limit=limit, subagent_id=subagent_id
        )
        # For initial load, check if there are more by comparing with count
        # We'll let the frontend determine has_more based on the returned count
        return {"success": True, "entries": entries, "has_more": len(entries) >= limit}


@app.get("/api/logs/subagents")
def get_log_subagents(
    agent_id: str = Query(..., description="Agent ID"),
):
    """
    获取指定 agent 下有日志的 subagent 列表。
    
    参数：
    - agent_id: Agent ID (必需)
    
    返回：
    - success: bool
    - subagents: List[str] - subagent_id 列表
    """
    if not agent_id:
        return {"success": False, "error": "agent_id required", "subagents": []}
    chat_service = get_chat_service()
    subagents = chat_service.repo.get_log_subagents(agent_id)
    return {"success": True, "subagents": subagents}


@app.get("/api/logs/stream")
def logs_sse(agent_id: str = None):
    """
    SSE for execution logs with initial history push.
    
    连接时：
    1. 先推送最近 50 条日志（event: log_entry）
    2. 然后监听新日志通知（event: logs_updated）
    
    前端收到 log_entry 事件后直接渲染，收到 logs_updated 后可增量拉取。
    """
    from fastapi.responses import JSONResponse

    if not agent_id:
        return JSONResponse(
            status_code=400,
            content={"error": "agent_id parameter is required"}
        )
    subscriber_id = str(uuid_module.uuid4())[:8]
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _log_subscribers[subscriber_id] = queue

    async def event_generator():
        try:
            # 1. 先推送最近日志（类似 Chat SSE）
            chat_service = get_chat_service()
            recent_logs = chat_service.repo.get_recent_execution_logs(agent_id, limit=50)
            for log in recent_logs:
                yield f"data: {json_module.dumps({'event': 'log_entry', 'agent_id': agent_id, 'entry': log})}\n\n"
            
            # 2. 然后监听新日志通知
            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if notification.get("agent_id") == agent_id:
                        yield f"data: {json_module.dumps(notification)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            _log_subscribers.pop(subscriber_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/logs/clear")
def clear_logs(agent_id: str = None):
    """Clear execution logs for a specific agent.
    
    Args:
        agent_id: Required. The agent ID to clear logs for.
    """
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    chat_service = get_chat_service()
    chat_service.clear_execution_logs(agent_id)
    return {"success": True, "message": "Logs cleared"}


# ==================== Worker SSE API (v11 Multi-process) ====================

from gateway.sse import get_worker_broadcaster, SSEEvent

@app.get("/api/worker/events")
def worker_events_sse(worker_id: Optional[str] = None):
    """
    SSE endpoint for Worker processes to receive events.
    
    Workers connect to this endpoint to receive real-time notifications:
    - new_message: New user message to process
    - new_task: New action task (tool_call, reply, subagent)
    - task_result: Task execution completed
    - round_complete: All mcpcalls in a round completed
    - heartbeat: Keep-alive ping
    - worker_shutdown: Graceful shutdown signal
    
    Args:
        worker_id: Optional worker identifier (auto-generated if not provided)
    
    Returns:
        SSE stream of events
    """
    broadcaster = get_worker_broadcaster()
    
    # Generate worker_id if not provided
    if worker_id is None:
        worker_id = f"worker-{uuid_module.uuid4().hex[:8]}"
    
    queue = broadcaster.register(worker_id)
    
    return StreamingResponse(
        broadcaster.event_generator(worker_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/worker/status")
def worker_broadcast_status():
    """
    Get status of the Worker SSE broadcaster.
    
    Returns information about connected Workers.
    """
    broadcaster = get_worker_broadcaster()
    return {
        "connected_workers": broadcaster.get_connection_count(),
        "connections": broadcaster.get_connections(),
    }


# ==================== Agent Self-Scheduling API ====================

@app.get("/api/agent/inbox")
def get_agent_inbox(agent_id: str):
    """
    Get pending events in the agent's inbox.
    
    Args:
        agent_id: Agent ID (required query parameter)
    
    Returns summary of pending events for agent to check during execution.
    Includes unread user messages.
    """
    if not agent_id:
        return {
            "success": False,
            "error": "agent_id is required",
            "pending_count": 0,
            "events": [],
            "has_urgent": False,
            "recommendation": "none"
        }
    
    chat_service = get_chat_service()
    
    # Get pending events from EventHandler
    pending_events = []
    has_urgent = False
    oldest_age = 0
    
    # Get unread user messages (highest priority - user is waiting!)
    unread_messages = chat_service.repo.get_unread_messages(agent_id)
    for msg in unread_messages:
        msg_id = msg.get("id")
        content = msg.get("content", "")
        pending_events.append({
            "type": "user_message",
            "message_id": msg_id,
            "summary": f"用户消息: {content[:50]}..." if len(content) > 50 else f"用户消息: {content}",
            "content": content,
            "timestamp": msg.get("timestamp"),
            "priority": "high"
        })
        # Mark as read when included in inbox
        chat_service.repo.mark_as_read(msg_id)
        print(f"[Inbox] Marking message {msg_id[:8]} as read")
        # Broadcast status update (not persisted)
        for queue in _chat_subscribers.values():
            try:
                queue.put_nowait({
                    "type": "STATUS_UPDATE",
                    "id": str(uuid_module.uuid4())[:8],
                    "message_id": msg_id,
                    "status": "read",
                    "timestamp": utc_now_iso()
                })
            except asyncio.QueueFull:
                pass
    
    # Check for any pending questions from chat (from database)
    pending_questions = chat_service.repo.get_all_pending_questions(agent_id)
    
    for q in pending_questions:
        pending_events.append({
            "type": "user_question_pending",
            "summary": f"用户问题等待回复: {q.get('question', '')[:50]}...",
            "timestamp": q.get("timestamp"),
            "priority": "high"
        })
    
    # Check for urgent keywords in pending events
    for event in pending_events:
        if event.get("priority") == "high":
            has_urgent = True
            break
    
    # Determine recommendation
    recommendation = "continue"
    if has_urgent:
        recommendation = "check_urgent"
    elif len(pending_events) > 3:
        recommendation = "process_all"
    
    return {
        "success": True,
        "pending_count": len(pending_events),
        "events": pending_events,
        "has_urgent": has_urgent,
        "oldest_age_seconds": oldest_age,
        "recommendation": recommendation,
    }


@app.post("/api/agent/interrupt")
def interrupt_agent(data: dict = {}):
    """
    Interrupt the currently executing agent.
    
    This stops the current task and saves the session state.
    """
    chat_service = get_chat_service()
    agent_id = data.get("agent_id")
    
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    
    try:
        from gateway.api.routes import get_agent
        agent = get_agent()
        
        if agent:
            agent.interrupt()
            print("[API] Agent interrupted via HTTP API")
        
        return {
            "success": True,
            "message": "Agent interrupted",
            "timestamp": utc_now_iso()
        }
    except Exception as e:
        print(f"[API] Interrupt error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/agent/rest")
def agent_rest(data: dict):
    """
    Put the agent into rest state.
    
    v2: Rest state is managed via subagents.status in database.
    """
    chat_service = get_chat_service()
    agent_id = data.get("agent_id")
    
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    
    reason = data.get("reason", "No reason provided")
    handoff_notes = data.get("handoff_notes")
    
    # Store rest state in database
    rest_state = {
        "is_resting": True,
        "reason": reason,
        "wake_triggers": [{"type": "user_response"}],
        "handoff_notes": handoff_notes,
        "rest_started": utc_now_iso(),
    }
    chat_service.repo.set_agent_rest_state(agent_id, rest_state)
    
    # Notify via chat
    chat_message = {
        "id": str(uuid_module.uuid4())[:12],
        "type": "AGENT_NOTIFY",
        "timestamp": utc_now_iso(),
        "message": f"💤 进入休息状态: {reason}",
        "level": "info",
        "handoff_notes": handoff_notes,
    }
    broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "state": "resting",  # Agent-level rest state (not runtime status)
        "reason": reason,
        "handoff_notes": handoff_notes,
    }


@app.get("/api/agent/rest-state")
def get_agent_rest_state(agent_id: str):
    """Get current rest state information.
    
    Args:
        agent_id: Agent ID (required query parameter)
    """
    if not agent_id:
        return {"success": False, "error": "agent_id is required", "is_resting": False}
    
    chat_service = get_chat_service()
    
    rest_state = chat_service.repo.get_agent_rest_state(agent_id)
    
    if not rest_state:
        rest_state = {
            "is_resting": False,
            "reason": None,
            "wake_triggers": [],
            "handoff_notes": None,
            "rest_started": None,
        }
    
    return {
        "success": True,
        **rest_state,
    }


@app.post("/api/agent/wake")
def wake_agent(data: dict = {}):
    """
    Manually wake the agent from rest state.
    """
    chat_service = get_chat_service()
    agent_id = data.get("agent_id")
    
    if not agent_id:
        return {"success": False, "error": "agent_id is required"}
    
    reason = data.get("reason", "Manual wake")
    
    # Get and clear rest state from database
    previous_state = chat_service.repo.get_agent_rest_state(agent_id) or {}
    chat_service.repo.set_agent_rest_state(agent_id, {
        "is_resting": False,
        "reason": None,
        "wake_triggers": [],
        "handoff_notes": None,
        "rest_started": None,
    })
    
    # Notify via chat
    chat_message = {
        "id": str(uuid_module.uuid4())[:12],
        "type": "AGENT_NOTIFY",
        "timestamp": utc_now_iso(),
        "message": f"☀️ 已唤醒: {reason}",
        "level": "success",
    }
    if previous_state.get("handoff_notes"):
        chat_message["handoff_notes"] = previous_state["handoff_notes"]
    
    broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "state": "awake",
        "wake_reason": reason,
        "previous_rest_reason": previous_state.get("reason"),
        "handoff_notes": previous_state.get("handoff_notes"),
    }


# ==================== Image Storage API ====================
# Serves images stored by ImageStorage service to avoid large base64 in database

from task_queue.utils.image_storage import get_image_storage, set_image_storage, ImageStorage
from fastapi.responses import FileResponse

# Initialize image storage with data directory
_images_dir = os.path.join(NOVAIC_DATA_DIR, "images")
os.makedirs(_images_dir, exist_ok=True)
set_image_storage(ImageStorage(base_dir=_images_dir))
print(f"[Gateway] Image storage initialized at: {_images_dir}")


@app.get("/api/images/{agent_id}/{filename}")
def get_image(agent_id: str, filename: str):
    """
    Serve an image file.
    
    Images are stored by ImageStorage to avoid large base64 data in database.
    
    Args:
        agent_id: Agent ID
        filename: Image filename (e.g., "1234567890_abc123.png")
    """
    storage = get_image_storage()
    url = f"/api/images/{agent_id}/{filename}"
    file_path = storage.get_file_path(url)
    
    if not file_path or not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


@app.get("/api/images/{agent_id}/{subagent_id}/{filename}")
def get_image_with_subagent(agent_id: str, subagent_id: str, filename: str):
    """
    Serve an image file with subagent path.
    
    Args:
        agent_id: Agent ID
        subagent_id: Subagent ID
        filename: Image filename
    """
    storage = get_image_storage()
    url = f"/api/images/{agent_id}/{subagent_id}/{filename}"
    file_path = storage.get_file_path(url)
    
    if not file_path or not file_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Image not found")
    
    suffix = file_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


@app.get("/api/images/stats")
def get_image_stats(agent_id: Optional[str] = None):
    """
    Get image storage statistics.
    
    Args:
        agent_id: Optional agent ID to limit scope
    """
    storage = get_image_storage()
    return storage.get_storage_stats(agent_id)


@app.post("/api/images/cleanup")
def cleanup_images(max_age_days: int = 7, agent_id: Optional[str] = None):
    """
    Clean up old images.
    
    Args:
        max_age_days: Maximum age in days (default: 7)
        agent_id: Optional agent ID to limit scope
    """
    storage = get_image_storage()
    deleted = storage.cleanup_old_images(max_age_days, agent_id)
    return {"deleted_count": deleted}


# Static files (React Web UI) - mount last to catch-all
# NOTE: This mount is at "/" which would catch all unmatched requests.
# MCP servers are mounted dynamically at /agents/{id}/mcp/ and /mcp/...
# The key insight: Starlette matches routes in order, and Mount at "/" is a catch-all.
# HOWEVER, more specific paths like /agents/ and /mcp/ should be matched first.
# Starlette's Mount uses path.startswith() matching, so /agents/... will match
# a Mount at /agents/ before it matches a Mount at /.
web_dist = Path(__file__).parent / "web" / "dist"
if web_dist.exists():
    print(f"📂 Serving Web UI from: {web_dist}")
    app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
else:
    # Fallback: simple HTML page
    from fastapi.responses import HTMLResponse
    
    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>NovAIC Gateway</title>
            <style>
                body { font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>🚀 NovAIC Gateway</h1>
            <p>Gateway is running! Web UI is not built yet.</p>
            <h2>Quick Start</h2>
            <ol>
                <li>Build the Web UI: <code>cd novaic-web && npm run build</code></li>
                <li>Copy to gateway: <code>cp -r dist ../novaic-backend/web/</code></li>
                <li>Restart gateway</li>
            </ol>
            <h2>API Endpoints</h2>
            <ul>
                <li><a href="/api/health">/api/health</a> - Health check</li>
                <li><a href="/api/config">/api/config</a> - Configuration</li>
                <li><a href="/api/system/status">/api/system/status</a> - System status</li>
                <li><a href="/docs">/docs</a> - API Documentation</li>
            </ul>
            <h2>Real-time Streams (SSE)</h2>
            <p>Chat messages: <code>/api/chat/messages</code></p>
            <p>Execution logs: <code>/api/logs/stream</code></p>
        </body>
        </html>
        """


if __name__ == "__main__":
    import sys
    
    # Check if running as PyInstaller bundle
    is_frozen = getattr(sys, 'frozen', False)
    
    if SOCKET_PATH:
        # Unix Domain Socket mode
        # Remove existing socket file if exists
        import pathlib
        socket_file = pathlib.Path(SOCKET_PATH)
        if socket_file.exists():
            socket_file.unlink()
        
        if is_frozen:
            # PyInstaller: use app object directly
            uvicorn.run(
                app,
                uds=SOCKET_PATH,
                log_level="info"
            )
        else:
            uvicorn.run(
                "main_gateway:app",
                uds=SOCKET_PATH,
                reload=DEBUG,
                log_level="info"
            )
    else:
        # TCP mode (default)
        if is_frozen:
            # PyInstaller: use app object directly
            uvicorn.run(
                app,
                host=HOST,
                port=PORT,
                log_level="info",
                timeout_keep_alive=30,  # Keep-alive timeout
                ws_ping_interval=20,    # WebSocket ping interval
                ws_ping_timeout=20,     # WebSocket ping timeout
            )
        else:
            uvicorn.run(
                "main_gateway:app",
                host=HOST,
                port=PORT,
                reload=DEBUG,
                log_level="info",
                timeout_keep_alive=30,
                ws_ping_interval=20,
                ws_ping_timeout=20,
            )
