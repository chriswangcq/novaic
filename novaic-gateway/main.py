"""
NovAIC Gateway - Main Entry Point

Unified control plane that serves:
- REST API (/api/*)
- SSE for real-time updates (/api/chat/messages, /api/logs/stream)
- Static files (React Web UI)
- Event-driven agent system
"""

import os
import sys
import logging
from datetime import datetime

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

# ==================== Data Directory Setup ====================
# NOVAIC_DATA_DIR is required (passed from Tauri app)
if not os.environ.get("NOVAIC_DATA_DIR"):
    print("[Gateway] ERROR: NOVAIC_DATA_DIR environment variable is required")
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
LOG_FILE = os.path.join(LOG_DIR, f"gateway-{datetime.now().strftime('%Y%m%d')}.log")

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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from api.routes import router as api_router
from api.agents import router as agents_router
from api.vm import router as vm_router
from api.claim import router as claim_router
from api.mcp import router as mcp_api_router
from config import get_config_manager

# Import database module
from db import init_database, close_database, run_migration

# Import new components
from agent.core.state import StateManager, AgentState
from agent.wake.controller import WakeController
from agent.micro.engine import MicroAgentEngine
from core.task_manager import TaskManager, get_task_manager, set_task_manager
from mcp_servers.manager import MCPManager, set_mcp_manager, get_mcp_manager

# Import v11 architecture components
from db.repositories.message import MessageRepository
from db.repositories.agent_state import AgentStateRepository

# Import v12 Master-driven architecture components
from master import Master, MasterConfig, set_master


# Configuration
HOST = os.getenv("NOVAIC_HOST", "127.0.0.1")
PORT = int(os.getenv("NOVAIC_PORT", "19999"))
SOCKET_PATH = os.getenv("NOVAIC_SOCKET", "")  # Unix socket path, if set use UDS mode
DEBUG = os.getenv("NOVAIC_DEBUG", "false").lower() == "true"

# Global instances
state_manager: StateManager = None
wake_controller: WakeController = None
micro_engine: MicroAgentEngine = None
subagent_manager = None  # Unused, kept for compatibility
task_manager: TaskManager = None
mcp_manager: MCPManager = None

# v11 architecture instances
message_repo: MessageRepository = None
agent_state_repo: AgentStateRepository = None

# v12 Master-driven architecture instance
_master: Master = None


# ==================== Component Accessors ====================

def get_state_manager() -> StateManager:
    """Get the global StateManager instance."""
    return state_manager


def get_wake_controller() -> WakeController:
    """Get the global WakeController instance."""
    return wake_controller


def get_micro_engine() -> MicroAgentEngine:
    """Get the global MicroAgentEngine instance."""
    return micro_engine


def get_subagent_manager():
    """
    Get the global SubAgentManager instance.
    
    v12: Deprecated - use Master for subagent management.
    Returns None as SubAgentManager is no longer used.
    """
    return None  # v12: Deprecated


def get_task_mgr() -> TaskManager:
    """Get the global TaskManager instance."""
    return task_manager


async def initialize_systems(config):
    """Initialize all system components."""
    global state_manager, wake_controller, micro_engine, subagent_manager, task_manager
    global message_repo, agent_state_repo
    
    # Initialize StateManager
    state_manager = StateManager(
        initial_state=AgentState.AWAKE,
        idle_timeout=None,  # No auto-sleep for now
    )
    print("[Gateway] StateManager initialized")
    
    # Get current agent's port configuration
    from config.agents import get_agent_config_manager, allocate_ports_for_agent
    
    try:
        agent_mgr = get_agent_config_manager()
        current_agent = agent_mgr.get_current_agent()
    except Exception as e:
        print(f"[Gateway] Warning: Could not get agent config: {e}")
        current_agent = None
    
    if current_agent:
        ports = current_agent.vm.ports
        print(f"[Gateway] Using ports from agent '{current_agent.name}' (index={current_agent.vm.agent_index})")
    else:
        ports = allocate_ports_for_agent(0)
        print(f"[Gateway] No current agent, using default ports (Agent 0)")
    
    # Initialize WakeController
    wake_controller = WakeController(
        storage_dir="storage/triggers",
    )
    print("[Gateway] WakeController initialized")
    
    # Initialize MicroAgentEngine
    micro_engine = MicroAgentEngine(
        llm_client=None,  # Will be set when needed
        storage_dir="storage/micro_agents",
    )
    
    # Register default micro agents
    from agent.micro.agent import MicroAgent, EvalMode
    
    # 1. Urgent keywords filter
    urgent_agent = MicroAgent(
        name="Urgent Filter",
        description="Filters messages containing urgent keywords",
        mode=EvalMode.RULES,
        enabled=True,
    )
    urgent_agent.add_rule("Emergency", r"\b(urgent|emergency|critical|asap|immediately)\b", "wake", priority=10)
    urgent_agent.add_rule("Error Alert", r"\b(error|failed|crash|exception|broken)\b", "wake", priority=8)
    urgent_agent.add_rule("Help Request", r"\b(help|assist|support)\b", "wake", priority=5)
    micro_engine.register_agent(urgent_agent)
    
    # 2. Spam/noise filter  
    spam_agent = MicroAgent(
        name="Spam Filter",
        description="Filters out spam and noise",
        mode=EvalMode.RULES,
        enabled=True,
    )
    spam_agent.add_rule("Test Message", r"^test$|^ping$|^hello$", "ignore", priority=5)
    spam_agent.add_rule("Empty/Short", r"^.{0,3}$", "ignore", priority=3)
    micro_engine.register_agent(spam_agent)
    
    print(f"[Gateway] MicroAgentEngine initialized with {len(micro_engine.list_agents())} agents")
    
    # SubAgents are managed by Master via Runtimes
    subagent_manager = None
    print("[Gateway] SubAgents managed via Master-driven Runtimes")
    
    # Initialize TaskManager (unified task system)
    from db.database import get_database
    
    def llm_factory(provider: str, api_base: str, api_key: str):
        """Create an LLM client for summary generation."""
        from core.llm_client import OpenAIClient, AnthropicClient, GoogleAIClient
        if provider == "anthropic":
            return AnthropicClient(api_key=api_key, base_url=api_base)
        elif provider == "google":
            return GoogleAIClient(api_key=api_key)
        else:
            return OpenAIClient(api_key=api_key, base_url=api_base)
    
    # v12: TaskManager no longer uses SubAgentManager
    task_manager = TaskManager(
        db=get_database(),
        subagent_manager=None,  # Deprecated: use Master for subagent management
        llm_factory=llm_factory,
    )
    set_task_manager(task_manager)
    print("[Gateway] TaskManager initialized")
    
    # Start WakeController (starts all enabled triggers)
    await wake_controller.start()
    print("[Gateway] WakeController started")
    
    # Cleanup expired tasks on startup
    if task_manager:
        cleaned = await task_manager.cleanup_expired()
        if cleaned:
            print(f"[Gateway] Cleaned up {cleaned} expired tasks on startup")
    
    # ==================== Initialize New Architecture ====================
    from db.database import get_database
    db = get_database()
    
    # Initialize repositories
    message_repo = MessageRepository(db)
    agent_state_repo = AgentStateRepository(db)
    print("[Gateway] MessageRepository and AgentStateRepository initialized")
    
    # v11: Agent processing now handled by Worker processes via ProcessManager
    # The old AgentRunner has been removed in favor of the multi-process architecture
    if current_agent:
        # Ensure agent state exists
        await agent_state_repo.ensure_exists(current_agent.id)
        print(f"[Gateway] Agent state initialized for {current_agent.id}")
    else:
        print("[Gateway] Warning: No current agent selected")


async def shutdown_systems():
    """Shutdown all system components."""
    global wake_controller
    
    if wake_controller:
        await wake_controller.stop()
        print("[Gateway] WakeController stopped")


_cleanup_task: Optional[asyncio.Task] = None


async def periodic_task_cleanup():
    """Periodically clean up expired tasks (runs every hour)."""
    while True:
        try:
            await asyncio.sleep(3600)  # Wait 1 hour
            
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            if tm:
                cleaned = await tm.cleanup_expired()
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
    
    global mcp_manager, _cleanup_task
    
    if SOCKET_PATH:
        print(f"🚀 NovAIC Gateway starting on unix://{SOCKET_PATH}")
    else:
        print(f"🚀 NovAIC Gateway starting on http://{HOST}:{PORT}")
    
    # Initialize database
    print("[Gateway] Initializing database...")
    db = await init_database()
    print(f"[Gateway] Database initialized: {db.db_path}")
    
    # Run migrations (from file-based storage to SQLite)
    print("[Gateway] Checking for data migrations...")
    migration_results = await run_migration(db)
    if any(migration_results.values()):
        print(f"[Gateway] Migrations completed: {migration_results}")
    else:
        print("[Gateway] No migrations needed")
    
    # Load config (now from database)
    config = get_config_manager().load()
    print(f"🤖 Default model: {config.default_model}")
    
    # Initialize all systems
    await initialize_systems(config)
    
    # v2.9: Initialize MCPManager
    mcp_manager = MCPManager(app)
    set_mcp_manager(mcp_manager)
    print("[Gateway] MCPManager initialized")
    
    # v2.9: Shared layer MCP servers are now created per-Agent by Master
    # No global shared servers - each Agent has its own isolated instance
    print("[Gateway] Shared MCP servers will be created per-Agent by Master")
    
    # Recover VM processes (check for running VMs from previous Gateway session)
    try:
        from vm import get_vm_manager
        vm_manager = get_vm_manager()
        await vm_manager.recover_processes()
        print("[Gateway] VM process recovery complete")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to recover VM processes: {e}")
    
    # Start periodic cleanup task
    _cleanup_task = asyncio.create_task(periodic_task_cleanup())
    print("[Gateway] Periodic task cleanup started (every hour)")
    
    # Initialize Worker SSE broadcaster (v11)
    from sse import init_worker_broadcaster, shutdown_worker_broadcaster
    await init_worker_broadcaster()
    print("[Gateway] Worker SSE broadcaster initialized")
    
    # Initialize Process Manager (v11 multi-process architecture)
    from config import get_worker_settings
    from process import ProcessManager, ProcessConfig
    worker_settings = get_worker_settings()
    process_config = ProcessConfig(
        min_workers=worker_settings.min_workers,
        max_workers=worker_settings.max_workers,
        max_concurrent_per_worker=worker_settings.max_concurrent_per_worker,
        heartbeat_timeout=worker_settings.heartbeat_timeout,
        task_timeout_minutes=worker_settings.task_timeout_minutes,
        gateway_url=f"http://{HOST}:{PORT}" if not SOCKET_PATH else f"http://localhost:{PORT}",
    )
    _process_manager = ProcessManager(process_config)
    await _process_manager.start()
    print(f"[Gateway] Process Manager started (workers={worker_settings.min_workers}-{worker_settings.max_workers})")
    
    # Initialize Master (v12 - Master-driven architecture)
    global _master
    from sse import get_worker_broadcaster
    from master import set_master
    
    _master = Master(
        db=db,
        sse_broadcaster=get_worker_broadcaster(),
        config=MasterConfig(
            monitor_interval=1.0,  # Check inbox every second
            scheduler_interval=0.1,  # Fast polling for runtime states
            max_rounds_per_runtime=50,
        ),
    )
    set_master(_master)
    await _master.start()
    print("[Gateway] Master started (v12 architecture)")
    
    yield
    
    # Cancel cleanup task
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        print("[Gateway] Periodic task cleanup stopped")
    
    # Shutdown Master (v12)
    if _master:
        await _master.stop()
        print("[Gateway] Master stopped")
    
    # Shutdown Process Manager (v11)
    await _process_manager.stop()
    print("[Gateway] Process Manager stopped")
    
    # Shutdown Worker SSE broadcaster (v11)
    from sse import shutdown_worker_broadcaster
    await shutdown_worker_broadcaster()
    print("[Gateway] Worker SSE broadcaster shutdown")
    
    # Shutdown MCPManager (v2.8)
    if mcp_manager:
        await mcp_manager.close_all()
        print("[Gateway] MCPManager closed")
    
    # Stop all VMs (graceful shutdown)
    try:
        from vm import get_vm_manager
        vm_manager = get_vm_manager()
        await vm_manager.stop_all()
        print("[Gateway] All VMs stopped")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to stop VMs: {e}")
    
    # Shutdown all systems
    await shutdown_systems()
    
    # Close database
    await close_database()
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

# VM API routes (already has /api/vm prefix)
app.include_router(vm_router)

# Claim API routes (v11 multi-process - already has /api prefix)
app.include_router(claim_router)

# MCP API routes (v11 multi-process - already has /api/mcp prefix)
app.include_router(mcp_api_router)


# Root endpoint
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "name": "NovAIC Gateway",
        "version": "0.4.0",
        "description": "Unified control plane for NovAIC AI Agent",
        "components": {
            "state_manager": state_manager.get_state().value if state_manager else "not_initialized",
            "mcp": mcp_manager.get_stats() if mcp_manager else "not_initialized",
            "wake_controller": f"{wake_controller.get_stats()['total_triggers']} triggers" if wake_controller else "not_initialized",
        }
    }


# System status endpoint
@app.get("/api/system/status")
async def system_status():
    """Get detailed system status"""
    # Get MCPManager stats
    mcp_stats = mcp_manager.get_stats() if mcp_manager else None
    
    return {
        "state_manager": state_manager.get_info() if state_manager else None,
        "mcp": mcp_stats,
        "wake_controller": wake_controller.get_stats() if wake_controller else None,
        "micro_engine": micro_engine.get_stats() if micro_engine else None,
        "subagent_manager": subagent_manager.get_stats() if subagent_manager else None,
    }


# Internal API for session tools (called by novaic-mcp-session)
@app.get("/api/internal/sessions")
async def list_sessions():
    """List all sessions (internal API)"""
    from agent.session.registry import get_session_registry
    registry = get_session_registry()
    return {"sessions": registry.list_sessions()}


@app.post("/api/internal/sessions/{session_key}/history")
async def get_session_history(session_key: str, data: dict):
    """Get session history (internal API)"""
    from agent.session.registry import get_session_registry
    registry = get_session_registry()
    
    limit = data.get("limit", 50)
    offset = data.get("offset", 0)
    
    messages = registry.get_history(session_key, limit=limit, offset=offset)
    if messages is None:
        return {"error": "Session not found", "messages": []}
    
    return {"messages": messages}


@app.post("/api/internal/sessions/{session_key}/send")
async def send_to_session(session_key: str, data: dict):
    """Send message to session (internal API)"""
    from agent.session.registry import get_session_registry
    registry = get_session_registry()
    
    message = data.get("message", "")
    wait_response = data.get("wait_response", False)
    timeout = data.get("timeout", 60)
    
    result = registry.send_message(
        session_key=session_key,
        message=message,
        wait_response=wait_response,
        timeout=timeout,
    )
    return result


# ==================== Unified Task API ====================

@app.post("/api/internal/tasks")
async def create_task(data: dict):
    """Create a new task (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    agent_id = data.get("agent_id") or get_current_agent_id()
    if not agent_id:
        return {"error": "No agent selected. Please select an agent first.", "success": False}
    
    return await task_manager.spawn(
        task_type=data.get("task_type", "agent"),
        config=data.get("task_config", {}),
        label=data.get("label"),
        timeout_seconds=data.get("timeout_seconds", 0),
        notify_on=data.get("notify_on", ["complete", "error"]),
        parent_session_key=data.get("parent_session_key", "main"),
        agent_id=agent_id,
    )


@app.get("/api/internal/tasks/{task_id}")
async def get_task_status(task_id: str, include_outputs: bool = False, output_limit: int = 50):
    """Get task status (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    return await task_manager.get_status(
        task_id=task_id,
        include_outputs=include_outputs,
        output_limit=output_limit,
    )


@app.get("/api/internal/tasks")
async def list_tasks(status: str = None, agent_id: str = None):
    """List tasks (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    status_filter = status.split(",") if status else None
    return await task_manager.get_status(
        task_id=None,
        status_filter=status_filter,
        agent_id=agent_id,
    )


@app.get("/api/internal/tasks/{task_id}/result")
async def get_task_result(task_id: str, format: str = "summary"):
    """Get task result (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    return await task_manager.get_result(
        task_id=task_id,
        format=format,
    )


@app.post("/api/internal/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, data: dict = None):
    """Cancel a task (internal API)"""
    if not task_manager:
        return {"error": "TaskManager not initialized", "success": False}
    
    reason = data.get("reason") if data else None
    return await task_manager.cancel(
        task_id=task_id,
        reason=reason,
    )


# ==================== Trigger Management API ====================

@app.get("/api/triggers")
async def list_triggers():
    """List all wake triggers"""
    if not wake_controller:
        return {"triggers": []}
    return {"triggers": wake_controller.list_triggers()}


@app.post("/api/triggers/cron")
async def add_cron_trigger(data: dict):
    """Add a new cron trigger"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    name = data.get("name", "Unnamed Cron")
    cron_expr = data.get("cron_expr", "0 * * * *")
    wake_message = data.get("wake_message", "Scheduled wake-up")
    enabled = data.get("enabled", True)
    
    trigger_id = await wake_controller.add_cron_trigger(
        name=name,
        cron_expr=cron_expr,
        wake_message=wake_message,
        enabled=enabled,
    )
    
    return {"success": True, "trigger_id": trigger_id}


@app.post("/api/triggers/webhook")
async def add_webhook_trigger(data: dict):
    """Add a new webhook trigger"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    name = data.get("name", "Unnamed Webhook")
    endpoint = data.get("endpoint", f"/webhook/{name.lower().replace(' ', '-')}")
    wake_message_template = data.get("wake_message_template", "Webhook triggered: {webhook_name}")
    secret = data.get("secret")
    enabled = data.get("enabled", True)
    
    trigger_id = await wake_controller.add_webhook_trigger(
        name=name,
        endpoint=endpoint,
        wake_message_template=wake_message_template,
        secret=secret,
        enabled=enabled,
    )
    
    return {"success": True, "trigger_id": trigger_id, "endpoint": endpoint}


@app.delete("/api/triggers/{trigger_id}")
async def remove_trigger(trigger_id: str):
    """Remove a trigger"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    success = await wake_controller.remove_trigger(trigger_id)
    return {"success": success}


@app.post("/api/triggers/{trigger_id}/enable")
async def enable_trigger(trigger_id: str):
    """Enable a trigger"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    success = await wake_controller.enable_trigger(trigger_id)
    return {"success": success}


@app.post("/api/triggers/{trigger_id}/disable")
async def disable_trigger(trigger_id: str):
    """Disable a trigger"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    success = await wake_controller.disable_trigger(trigger_id)
    return {"success": success}


@app.post("/api/webhook/{endpoint:path}")
async def handle_webhook(endpoint: str, data: dict = {}):
    """Handle incoming webhook requests"""
    if not wake_controller:
        return {"error": "WakeController not initialized", "success": False}
    
    return await wake_controller.handle_webhook(f"/webhook/{endpoint}", data)


# ==================== MicroAgent Management API ====================

@app.get("/api/micro-agents")
async def list_micro_agents():
    """List all registered micro agents"""
    if not micro_engine:
        return {"agents": []}
    return {"agents": micro_engine.list_agents()}


@app.post("/api/micro-agents")
async def create_micro_agent(data: dict):
    """Create a new micro agent"""
    if not micro_engine:
        return {"error": "MicroAgentEngine not initialized", "success": False}
    
    from agent.micro.agent import MicroAgent, EvalMode, Rule
    
    # Create agent
    agent = MicroAgent(
        name=data.get("name", "Unnamed Agent"),
        description=data.get("description", ""),
        mode=EvalMode(data.get("mode", "rules")),
        enabled=data.get("enabled", True),
        confidence_threshold=data.get("confidence_threshold", 0.7),
    )
    
    # Add rules if provided
    for rule_data in data.get("rules", []):
        agent.add_rule(
            name=rule_data.get("name", "Unnamed Rule"),
            pattern=rule_data.get("pattern", ""),
            action=rule_data.get("action", "wake"),
            priority=rule_data.get("priority", 0),
        )
    
    # Set LLM prompt if provided
    if "llm_prompt" in data:
        agent.llm_prompt = data["llm_prompt"]
    
    agent_id = micro_engine.register_agent(agent)
    
    return {"success": True, "agent_id": agent_id, "agent": agent.to_dict()}


@app.get("/api/micro-agents/{agent_id}")
async def get_micro_agent(agent_id: str):
    """Get a specific micro agent"""
    if not micro_engine:
        return {"error": "MicroAgentEngine not initialized"}
    
    agent = micro_engine.get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found"}
    
    return {"agent": agent.to_dict()}


@app.delete("/api/micro-agents/{agent_id}")
async def delete_micro_agent(agent_id: str):
    """Delete a micro agent"""
    if not micro_engine:
        return {"error": "MicroAgentEngine not initialized", "success": False}
    
    success = micro_engine.unregister_agent(agent_id)
    return {"success": success}


@app.post("/api/micro-agents/{agent_id}/rules")
async def add_micro_agent_rule(agent_id: str, data: dict):
    """Add a rule to a micro agent"""
    if not micro_engine:
        return {"error": "MicroAgentEngine not initialized", "success": False}
    
    agent = micro_engine.get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found", "success": False}
    
    rule_id = agent.add_rule(
        name=data.get("name", "Unnamed Rule"),
        pattern=data.get("pattern", ""),
        action=data.get("action", "wake"),
        priority=data.get("priority", 0),
    )
    
    return {"success": True, "rule_id": rule_id}


@app.post("/api/micro-agents/evaluate")
async def evaluate_with_micro_agents(data: dict):
    """Evaluate text using all enabled micro agents"""
    if not micro_engine:
        return {"error": "MicroAgentEngine not initialized", "success": False}
    
    event_text = data.get("text", "")
    event_data = data.get("data")
    
    result = await micro_engine.evaluate_all(event_text, event_data)
    
    return {
        "success": True,
        "result": result.to_dict(),
    }


# ==================== Chat MCP API (Agent <-> User Communication) ====================

import asyncio
from fastapi.responses import StreamingResponse
import json as json_module
from typing import Dict, Any, Optional
import uuid as uuid_module

# Import ChatService for database-backed state management
from api.chat_service import get_chat_service, ChatService

# SSE subscribers (runtime state - cannot be persisted)
_chat_subscribers: Dict[str, asyncio.Queue] = {}  # Chat SSE subscribers
_log_subscribers: Dict[str, asyncio.Queue] = {}   # Log SSE subscribers

# Note: v11 - Agent execution handled by Worker processes via ProcessManager


def get_current_agent_id() -> Optional[str]:
    """Get the current agent ID from config.
    
    Returns:
        The current agent ID, or None if no agent is selected.
        
    Note: Returns None instead of a fallback value to make issues visible.
    Callers should handle None explicitly.
    """
    try:
        from config.agents import get_agent_config_manager
        mgr = get_agent_config_manager()
        current = mgr.get_current_agent()
        if current:
            return current.id
    except Exception as e:
        logger.warning(f"[Gateway] Failed to get current agent ID: {e}")
    return None


async def broadcast_chat_message(message: Dict[str, Any], agent_id: Optional[str] = None):
    """Broadcast a chat message to all SSE subscribers and save to database.
    
    Note: Non-persistent message types (STATUS_UPDATE, TYPING, etc.) are only
    broadcast to SSE subscribers and not saved to database.
    
    Args:
        message: The message to broadcast
        agent_id: Optional agent ID. If not provided, uses the message's agent_id 
                  or falls back to current agent. This ensures messages are 
                  correctly attributed even when user switches agents.
    """
    chat_service = get_chat_service()
    
    # Use provided agent_id, then message's agent_id, then current agent
    if agent_id is None:
        agent_id = message.get("agent_id") or get_current_agent_id()
    
    # Add/update agent_id in message for frontend filtering
    message["agent_id"] = agent_id
    
    # Extract message info
    msg_type = message.get("type", "UNKNOWN")
    msg_id = message.get("id", str(uuid_module.uuid4())[:12])
    timestamp = message.get("timestamp", datetime.now().isoformat())
    content = message.get("content", message.get("message"))
    
    # Debug: log content extraction
    print(f"[Broadcast] type={msg_type}, content_from_content={message.get('content')}, content_from_message={message.get('message')}, final_content={content[:50] if content else 'EMPTY'}")
    
    # Build metadata from remaining fields
    metadata = {k: v for k, v in message.items() 
                if k not in ("id", "type", "timestamp", "content", "message")}
    
    # Save to database (ChatRepository handles non-persistent types)
    await chat_service.repo.add_message(
        agent_id=agent_id,
        id=msg_id,
        type=msg_type,
        content=content,
        metadata=metadata if metadata else None,
        timestamp=timestamp,
    )
    
    # Broadcast to SSE subscribers
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass


async def update_message_status(message_id: str, status: str):
    """Update message status and broadcast to subscribers.
    
    For 'read' status, marks the message as read in the database.
    STATUS_UPDATE is broadcast to SSE but not persisted.
    """
    chat_service = get_chat_service()
    
    # Update in database - for 'read' status, use mark_as_read
    if status == "read":
        await chat_service.repo.mark_as_read(message_id)
    
    # Broadcast status update (not persisted, just for real-time UI)
    status_update = {
        "id": str(uuid_module.uuid4())[:8],
        "type": "STATUS_UPDATE",
        "message_id": message_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(status_update)
        except asyncio.QueueFull:
            pass


async def broadcast_log(log: Dict[str, Any]):
    """Broadcast an execution log to all log SSE subscribers and save to database."""
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        logger.warning("[Gateway] broadcast_log: No current agent, skipping database save")
        # Still broadcast to SSE subscribers
        for queue in _log_subscribers.values():
            try:
                queue.put_nowait(log)
            except asyncio.QueueFull:
                pass
        return
    
    # Save to database (pure flow logs, not associated with messages)
    await chat_service.repo.add_execution_log(
        agent_id=agent_id,
        type=log.get("type", "unknown"),
        timestamp=log.get("timestamp", datetime.now().isoformat()),
        data=log.get("data"),
    )
    
    # Broadcast to SSE subscribers
    for queue in _log_subscribers.values():
        try:
            queue.put_nowait(log)
        except asyncio.QueueFull:
            pass


@app.post("/api/logs/broadcast")
async def receive_log_broadcast(data: dict):
    """
    Receive execution log broadcasts from Workers.
    
    Called by Workers to broadcast tool execution status (thinking, tool_start, tool_end).
    """
    # Extract agent_id from data or use current agent
    agent_id = data.pop("agent_id", None) or get_current_agent_id()
    
    # Broadcast the log
    await broadcast_log({
        **data,
        "agent_id": agent_id,
    })
    
    return {"success": True}


@app.post("/api/chat/event")
async def receive_chat_event(data: dict):
    """
    Receive chat events from novaic-mcp-chat.
    
    This is called when the Agent uses chat tools (chat_reply, chat_ask, etc.)
    Events are stored and broadcast to all SSE subscribers.
    """
    event_type = data.get("type", "")
    event_data = data.get("data", {})
    
    # Debug: log incoming data
    print(f"[ChatEvent] Received: type={event_type}, data_keys={list(event_data.keys())}, message={event_data.get('message', 'N/A')[:50] if event_data.get('message') else 'EMPTY'}")
    
    # Generate message ID and timestamp
    message_id = str(uuid_module.uuid4())[:12]
    timestamp = datetime.now().isoformat()
    
    # Create chat message
    chat_message = {
        "id": message_id,
        "type": event_type,
        "timestamp": timestamp,
        **event_data
    }
    
    # Get agent_id early for consistent routing
    agent_id = get_current_agent_id()
    
    # Handle AGENT_ASK specially - store pending question in database
    if event_type == "AGENT_ASK":
        request_id = event_data.get("request_id") or message_id
        chat_service = get_chat_service()
        await chat_service.repo.add_pending_question(
            agent_id=agent_id,
            request_id=request_id,
            question=event_data.get("question"),
            options=event_data.get("options"),
            message_id=message_id,
        )
        chat_message["request_id"] = request_id
    
    # Use helper to store and broadcast (pass agent_id for correct routing)
    await broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "message_id": message_id,
        "request_id": chat_message.get("request_id"),
    }


@app.get("/api/chat/messages")
async def chat_messages_sse():
    """
    SSE endpoint for real-time chat messages (Agent -> User).
    
    Frontend connects to this to receive:
    - Agent replies (AGENT_REPLY)
    - Agent questions (AGENT_ASK)
    - Agent notifications (AGENT_NOTIFY)
    - Agent images (AGENT_IMAGE)
    """
    subscriber_id = str(uuid_module.uuid4())[:8]
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _chat_subscribers[subscriber_id] = queue
    
    async def event_generator():
        try:
            # Send recent messages first (from database)
            chat_service = get_chat_service()
            agent_id = get_current_agent_id()
            recent_messages = await chat_service.repo.get_recent_chat_messages(agent_id, limit=10)
            for msg in recent_messages:
                yield f"data: {json_module.dumps(msg)}\n\n"
            
            # Stream new messages
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
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
async def check_user_response(request_id: str):
    """
    Check if user has responded to an agent's question.
    
    Called by novaic-mcp-chat's chat_ask tool to poll for user response.
    """
    chat_service = get_chat_service()
    
    # Check if question exists
    question = await chat_service.repo.get_pending_question(request_id)
    if not question:
        return {"error": "Question not found", "has_response": False}
    
    # Check for response
    response = await chat_service.repo.get_question_response(request_id)
    if response:
        # Remove question and response after retrieval
        await chat_service.repo.delete_pending_question(request_id)
        await chat_service.repo.delete_question_response(request_id)
        return {"has_response": True, **response}
    
    return {"has_response": False}


@app.post("/api/chat/respond/{request_id}")
async def submit_user_response(request_id: str, data: dict):
    """
    Submit user's response to an agent's question.
    
    Called by frontend when user answers a question from the agent.
    """
    chat_service = get_chat_service()
    
    # Check if question exists
    question = await chat_service.repo.get_pending_question(request_id)
    if not question:
        return {"error": "Question not found or expired", "success": False}
    
    # Store response in database
    timestamp = datetime.now().isoformat()
    await chat_service.repo.add_question_response(
        request_id=request_id,
        response=data.get("response", ""),
        selected_option=data.get("selected_option"),
    )
    
    return {"success": True, "request_id": request_id}


@app.get("/api/chat/pending-questions")
async def get_pending_questions():
    """Get all pending questions from the agent."""
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    if not agent_id:
        return {"questions": [], "warning": "No agent selected"}
    questions = await chat_service.repo.get_all_pending_questions(agent_id)
    return {
        "questions": questions
    }


@app.get("/api/chat/history")
async def get_chat_history(
    limit: int = 20,
    before_id: str = None,
    message_type: str = None,
    summary_length: int = 50
):
    """
    Get chat history between agent and user (with optional summary).
    
    Args:
        limit: Maximum number of messages (default: 20, max: 100)
        before_id: Get messages before this ID (for pagination)
        message_type: Filter by type: "user", "agent", "notification"
        summary_length: Truncate message content to this length (0 for full)
    """
    limit = min(limit, 100)
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"messages": [], "has_more": False, "warning": "No agent selected"}
    
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
    all_messages = await chat_service.repo.get_chat_history(
        agent_id=agent_id,
        limit=limit + 1,  # Get one extra to check has_more
        before_id=before_id,
        type_filter=type_filter,
    )
    
    has_more = len(all_messages) > limit
    messages = all_messages[:limit]
    
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
        }
        # Include level for notifications
        if msg.get("level"):
            summary_msg["level"] = msg.get("level")
        # Include options count for questions
        if msg.get("options"):
            summary_msg["options_count"] = len(msg.get("options"))
        
        summarized.append(summary_msg)
    
    # Get total count
    total_count = await chat_service.repo.get_chat_message_count(agent_id)
    
    return {
        "success": True,
        "messages": summarized,
        "has_more": has_more,
        "total_count": total_count,
    }


@app.get("/api/chat/message/{message_id}")
async def get_chat_message(message_id: str):
    """
    Get full content of a specific chat message.
    
    Args:
        message_id: The message ID
    """
    chat_service = get_chat_service()
    msg = await chat_service.repo.get_chat_message(message_id)
    
    if msg:
        return {"success": True, **msg}
    
    return {"success": False, "error": "Message not found"}


# ==================== Unified Inbox API (All messages to Agent) ====================
# v11: Uses MessageRepository and SSE broadcast for Worker processing

@app.post("/api/inbox")
async def add_to_inbox(data: dict):
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
    agent_id = data.get("agent_id") or get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected. Please select an agent first."}
    
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
        msg = await message_repo.add_message(
            agent_id=agent_id,
            type=msg_type,
            content=content,
            metadata=metadata,
        )
        
        # 2. Broadcast to SSE (for UI display)
        await broadcast_chat_message({
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
async def get_inbox_summary():
    """
    Get inbox summary for the current agent.
    
    v11: Uses MessageRepository to get pending (unclaimed, unprocessed) messages.
    
    Returns:
    - pending_count: Number of pending messages
    - messages: List of pending messages (truncated content)
    """
    agent_id = get_current_agent_id()
    if not agent_id:
        return {"success": False, "error": "No agent selected", "pending_count": 0, "messages": []}
    
    try:
        # Get pending messages (unclaimed, unprocessed)
        db = get_database()
        rows = await db.fetchall(
            """SELECT id, type, content, timestamp FROM chat_messages 
               WHERE agent_id = ? AND claimed_by IS NULL AND processed = 0
               ORDER BY timestamp DESC LIMIT 20""",
            (agent_id,)
        )
        
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
async def send_chat_message(data: dict):
    """
    Send a user message.
    
    v11 architecture:
    1. Store message to chat_messages (read=0, processed=0)
    2. Broadcast to UI SSE and Worker SSE
    3. Worker will claim and process via /api/claim/message
    
    Returns immediately with message_id.
    """
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected. Please select an agent first."}
    
    content = data.get("message", "").strip()
    model = data.get("model")
    api_key_id = data.get("api_key_id")
    
    if not content:
        return {"success": False, "error": "Message content required"}
    
    # 1. Store message using MessageRepository
    msg = await message_repo.add_message(
        agent_id=agent_id,
        type="USER_MESSAGE",
        content=content,
        metadata={"model": model, "api_key_id": api_key_id},
    )
    
    # 2. Broadcast to SSE (for UI display)
    user_msg = {
        "id": msg["id"],
        "type": "USER_MESSAGE",
        "content": content,
        "timestamp": msg["timestamp"],
        "status": "delivered",
    }
    await broadcast_chat_message(user_msg, agent_id=agent_id)
    
    # 3. Auto-respond to any pending questions
    chat_service = get_chat_service()
    pending_questions = await chat_service.repo.get_all_pending_questions(agent_id)
    if pending_questions:
        for q in pending_questions:
            request_id = q.get("request_id")
            await chat_service.repo.add_question_response(
                agent_id=agent_id,
                request_id=request_id,
                response=content,
                selected_option=None,
            )
            print(f"[Chat] Auto-responded to pending question {request_id}")
    
    # v12: No broadcast_new_message needed
    # Monitor polls for unread messages and creates Runtimes
    
    print(f"[Chat] Message {msg['id']} stored, Monitor will detect and process")
    
    return {
        "success": True,
        "message_id": msg["id"],
        "status": "queued",
        "timestamp": msg["timestamp"],
    }


@app.get("/api/logs/stream")
async def logs_sse():
    """
    SSE endpoint for real-time agent execution logs.
    
    Streams:
    - tool_start: Tool execution started
    - tool_end: Tool execution completed
    - thinking: Agent reasoning
    - status: Status updates
    - error: Errors
    - warning: Warnings
    """
    subscriber_id = str(uuid_module.uuid4())[:8]
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _log_subscribers[subscriber_id] = queue
    
    async def event_generator():
        try:
            # Send recent logs as catch-up (last 20, from database)
            chat_service = get_chat_service()
            agent_id = get_current_agent_id()
            recent_logs = await chat_service.repo.get_recent_execution_logs(agent_id, limit=20)
            for log in recent_logs:
                yield f"data: {json_module.dumps(log)}\n\n"
            
            # Stream new logs
            while True:
                try:
                    log = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json_module.dumps(log)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            # Cleanup on disconnect
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
async def clear_logs():
    """Clear execution logs."""
    _agent_logs.clear()
    return {"success": True, "message": "Logs cleared"}


# ==================== Worker SSE API (v11 Multi-process) ====================

from sse import get_worker_broadcaster, SSEEvent

@app.get("/api/worker/events")
async def worker_events_sse(worker_id: Optional[str] = None):
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
async def worker_broadcast_status():
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
async def get_agent_inbox():
    """
    Get pending events in the agent's inbox.
    
    Returns summary of pending events for agent to check during execution.
    Includes unread user messages.
    """
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {
            "success": False,
            "error": "No agent selected",
            "pending_count": 0,
            "events": [],
            "has_urgent": False,
            "recommendation": "none"
        }
    
    # Get pending events from EventHandler
    pending_events = []
    has_urgent = False
    oldest_age = 0
    
    # Get unread user messages (highest priority - user is waiting!)
    unread_messages = await chat_service.repo.get_unread_messages(agent_id)
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
        await chat_service.repo.mark_as_read(msg_id)
        print(f"[Inbox] Marking message {msg_id[:8]} as read")
        # Broadcast status update (not persisted)
        for queue in _chat_subscribers.values():
            try:
                queue.put_nowait({
                    "type": "STATUS_UPDATE",
                    "id": str(uuid_module.uuid4())[:8],
                    "message_id": msg_id,
                    "status": "read",
                    "timestamp": datetime.now().isoformat()
                })
            except asyncio.QueueFull:
                pass
    
    # Check for any pending questions from chat (from database)
    pending_questions = await chat_service.repo.get_all_pending_questions(agent_id)
    
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
        "agent_state": state_manager.get_state().value if state_manager else "unknown"
    }


@app.post("/api/agent/interrupt")
async def interrupt_agent():
    """
    Interrupt the currently executing agent.
    
    This stops the current task and saves the session state.
    """
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected"}
    
    try:
        from api.routes import get_agent
        agent = get_agent()
        
        if agent:
            agent.interrupt()
            print("[API] Agent interrupted via HTTP API")
        
        # Also update state
        if state_manager:
            state_manager.set_state(AgentState.AWAKE)
        
        # v11: is_busy flag removed, Workers manage their own state
        
        return {
            "success": True,
            "message": "Agent interrupted",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[API] Interrupt error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/agent/rest")
async def agent_rest(data: dict):
    """
    Put the agent into rest state with wake triggers.
    
    The agent voluntarily enters rest state and sets conditions for waking up.
    """
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected"}
    
    reason = data.get("reason", "No reason provided")
    wake_triggers = data.get("wake_triggers", [{"type": "user_response"}])
    handoff_notes = data.get("handoff_notes")
    
    # Set agent to sleep state
    if state_manager:
        state_manager.set_state(AgentState.SLEEP)
    
    # Store rest state in database
    rest_state = {
        "is_resting": True,
        "reason": reason,
        "wake_triggers": wake_triggers,
        "handoff_notes": handoff_notes,
        "rest_started": datetime.now().isoformat(),
    }
    await chat_service.repo.set_agent_rest_state(agent_id, rest_state)
    
    # Configure wake triggers
    triggers_set = 0
    estimated_wake = None
    
    for trigger in wake_triggers:
        trigger_type = trigger.get("type")
        
        if trigger_type == "cron" and wake_controller:
            # Add cron trigger
            expr = trigger.get("expr", "*/30 * * * *")
            await wake_controller.add_cron_trigger(
                name=f"rest_wake_{triggers_set}",
                cron_expr=expr,
                wake_message=f"[Auto Wake] Rest timeout. Reason: {reason}",
                enabled=True
            )
            triggers_set += 1
            
        elif trigger_type == "timeout":
            # Add timeout trigger via cron
            minutes = trigger.get("minutes", 30)
            if wake_controller:
                # Calculate next wake time
                from datetime import timedelta
                wake_time = datetime.now() + timedelta(minutes=minutes)
                estimated_wake = wake_time.isoformat()
                
                # Use a one-shot approach: set wake time
                # For simplicity, we'll use the micro agent to check timeout
            triggers_set += 1
            
        elif trigger_type == "keyword" and micro_engine:
            # Add keyword-based micro agent rule
            pattern = trigger.get("pattern", "")
            if pattern:
                # Create or update a wake filter micro agent
                from agent.micro.agent import MicroAgent, EvalMode
                agent = MicroAgent(
                    name="Rest Wake Filter",
                    description=f"Wake on keyword: {pattern}",
                    mode=EvalMode.RULES,
                )
                agent.add_rule(
                    name="keyword_wake",
                    pattern=pattern,
                    action="wake",
                    priority=10
                )
                micro_engine.register_agent(agent)
                triggers_set += 1
        
        elif trigger_type in ("user_response", "user_message"):
            # Default behavior: wake on any user message
            # This is handled by the EventHandler checking sleep state
            triggers_set += 1
    
    # Notify via chat
    if triggers_set > 0:
        chat_message = {
            "id": str(uuid_module.uuid4())[:12],
            "type": "AGENT_NOTIFY",
            "timestamp": datetime.now().isoformat(),
            "message": f"💤 进入休息状态: {reason}",
            "level": "info",
            "handoff_notes": handoff_notes,
        }
        await broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "state": "resting",
        "reason": reason,
        "triggers_set": triggers_set,
        "estimated_wake": estimated_wake,
        "handoff_notes": handoff_notes,
    }


@app.get("/api/agent/rest-state")
async def get_agent_rest_state():
    """Get current rest state information."""
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected", "is_resting": False}
    
    rest_state = await chat_service.repo.get_agent_rest_state(agent_id)
    
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
        "current_state": state_manager.get_state().value if state_manager else "unknown"
    }


@app.post("/api/agent/wake")
async def wake_agent(data: dict = {}):
    """
    Manually wake the agent from rest state.
    """
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected"}
    
    reason = data.get("reason", "Manual wake")
    
    if state_manager:
        state_manager.set_state(AgentState.AWAKE)
    
    # Get and clear rest state from database
    previous_state = await chat_service.repo.get_agent_rest_state(agent_id) or {}
    await chat_service.repo.set_agent_rest_state(agent_id, {
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
        "timestamp": datetime.now().isoformat(),
        "message": f"☀️ 已唤醒: {reason}",
        "level": "success",
    }
    if previous_state.get("handoff_notes"):
        chat_message["handoff_notes"] = previous_state["handoff_notes"]
    
    await broadcast_chat_message(chat_message, agent_id=agent_id)
    
    return {
        "success": True,
        "state": "awake",
        "wake_reason": reason,
        "previous_rest_reason": previous_state.get("reason"),
        "handoff_notes": previous_state.get("handoff_notes"),
    }


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
    async def root():
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
                <li>Copy to gateway: <code>cp -r dist ../novaic-gateway/web/</code></li>
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
                "main:app",
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
                "main:app",
                host=HOST,
                port=PORT,
                reload=DEBUG,
                log_level="info",
                timeout_keep_alive=30,
                ws_ping_interval=20,
                ws_ping_timeout=20,
            )
