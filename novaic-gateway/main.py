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
from config import get_config_manager

# Import database module
from db import init_database, close_database, run_migration

# Import new components
from agent.events.bus import EventBus
from agent.events.handler import AgentEventHandler
from agent.events.models import AgentEvent, EventType, EventPriority
from agent.core.state import StateManager, AgentState
from agent.wake.controller import WakeController
from agent.micro.engine import MicroAgentEngine
from agent.subagent.manager import SubAgentManager
from core.task_manager import TaskManager, get_task_manager, set_task_manager
from mcp_gateway.manager import MCPGatewayManager, set_mcp_gateway_manager, get_mcp_gateway_manager

# Import new Inbox components
from agent.inbox.monitor import InboxMonitor
from agent.runner import AgentRunner
from api.inbox_service import InboxService, get_inbox_service
from db.repositories.inbox import InboxRepository
from db.repositories.agent_state import AgentStateRepository


# Configuration
HOST = os.getenv("NOVAIC_HOST", "127.0.0.1")
PORT = int(os.getenv("NOVAIC_PORT", "19999"))
SOCKET_PATH = os.getenv("NOVAIC_SOCKET", "")  # Unix socket path, if set use UDS mode
DEBUG = os.getenv("NOVAIC_DEBUG", "false").lower() == "true"

# Global instances
event_bus: EventBus = None
state_manager: StateManager = None
wake_controller: WakeController = None
micro_engine: MicroAgentEngine = None
subagent_manager: SubAgentManager = None
task_manager: TaskManager = None
event_handler: AgentEventHandler = None
mcp_gateway_manager: MCPGatewayManager = None

# New Inbox system instances
inbox_service: InboxService = None
inbox_monitor: InboxMonitor = None
agent_runner: AgentRunner = None
inbox_repo: InboxRepository = None
agent_state_repo: AgentStateRepository = None


# ==================== Component Accessors ====================

def get_event_bus() -> EventBus:
    """Get the global EventBus instance."""
    return event_bus


def get_state_manager() -> StateManager:
    """Get the global StateManager instance."""
    return state_manager


def get_wake_controller() -> WakeController:
    """Get the global WakeController instance."""
    return wake_controller


def get_micro_engine() -> MicroAgentEngine:
    """Get the global MicroAgentEngine instance."""
    return micro_engine


def get_subagent_manager() -> SubAgentManager:
    """Get the global SubAgentManager instance."""
    return subagent_manager


def get_task_mgr() -> TaskManager:
    """Get the global TaskManager instance."""
    return task_manager


def get_event_handler() -> AgentEventHandler:
    """Get the global AgentEventHandler instance."""
    return event_handler


async def publish_user_event(
    message: str,
    session_id: str = "main",
    source: str = "http",
    reply_channel: str = "http"
) -> None:
    """
    Publish a user message event to the EventBus.
    
    This allows tracking of all user interactions through the event system.
    """
    if not event_bus:
        return
    
    event = AgentEvent(
        type=EventType.USER_MESSAGE,
        source=source,
        session_id=session_id,
        payload={"content": message},
        reply_channel=reply_channel,
    )
    await event_bus.publish(event)


async def initialize_systems(config):
    """Initialize all system components."""
    global event_bus, state_manager, wake_controller, micro_engine, subagent_manager, task_manager, event_handler
    global inbox_service, inbox_monitor, agent_runner, inbox_repo, agent_state_repo
    
    # Initialize EventBus
    event_bus = EventBus()
    print("[Gateway] EventBus initialized")
    
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
        event_bus=event_bus,
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
    
    # Initialize SubAgentManager (with agent factory using Gateway's ToolRegistry)
    async def create_agent_for_session(session_key: str):
        """Factory to create agent for sub-sessions using the Gateway's ToolRegistry."""
        from core.agent import NovAICAgent
        from mcp_gateway.manager import get_mcp_gateway_manager
        
        # Get Gateway's registry (has VM + all sub-MCPs)
        gateway_mgr = get_mcp_gateway_manager()
        agent_id = current_agent.id if current_agent else None
        
        tool_registry = None
        if gateway_mgr and agent_id:
            gateway = gateway_mgr.get_gateway(agent_id)
            if gateway:
                tool_registry = gateway.registry
        
        agent = NovAICAgent(mcp_port=ports.vm, tool_registry=tool_registry, session_key=session_key)
        await agent.initialize()
        return agent
    
    async def on_subagent_result(parent_session_id: str, result: Any):
        """Callback for sub-agent results."""
        if not event_bus:
            return
            
        try:
            from agent.events.models import AgentEvent
            # Convert result to dict if needed
            result_dict = result.to_dict() if hasattr(result, "to_dict") else result
            
            event = AgentEvent.subagent_result(
                subagent_id=result.subagent_id if hasattr(result, "subagent_id") else "unknown",
                result=result_dict,
                parent_session_id=parent_session_id,
            )
            await event_bus.publish(event)
            print(f"[Gateway] Published SUBAGENT_RESULT event for {event.payload.get('subagent_id')}")
        except Exception as e:
            print(f"[Gateway] Failed to publish subagent result: {e}")

    subagent_manager = SubAgentManager(
        agent_factory=create_agent_for_session,
        on_result=on_subagent_result,
        max_concurrent=5,
    )
    print("[Gateway] SubAgentManager initialized")
    
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
    
    task_manager = TaskManager(
        db=get_database(),
        subagent_manager=subagent_manager,
        event_bus=event_bus,
        llm_factory=llm_factory,
    )
    set_task_manager(task_manager)
    print("[Gateway] TaskManager initialized")
    
    # Initialize EventHandler with agent callback
    async def agent_callback(message: str, session_id: str) -> str:
        """Callback to process messages through the agent."""
        from api.routes import get_agent
        agent = get_agent()
        config_mgr = get_config_manager().load()
        
        # Collect full response from agent
        full_response = ""
        async for event in agent.chat_with_logs(
            message,
            model=config_mgr.default_model,
            provider=None,  # Use default
            api_base=None,
            api_key=None,
        ):
            if event.get("type") == "final":
                full_response = event.get("data", "")
                break
        return full_response
    
    event_handler = AgentEventHandler(
        event_bus=event_bus,
        state_manager=state_manager,
        agent_callback=agent_callback,
    )
    print("[Gateway] EventHandler initialized")
    
    # Start EventBus
    await event_bus.start()
    print("[Gateway] EventBus started")
    
    # Start WakeController (starts all enabled triggers)
    await wake_controller.start()
    print("[Gateway] WakeController started")
    
    # Cleanup expired tasks on startup
    if task_manager:
        cleaned = await task_manager.cleanup_expired()
        if cleaned:
            print(f"[Gateway] Cleaned up {cleaned} expired tasks on startup")
    
    # ==================== Initialize Inbox System ====================
    from db.database import get_database
    db = get_database()
    
    # Initialize repositories
    inbox_repo = InboxRepository(db)
    agent_state_repo = AgentStateRepository(db)
    print("[Gateway] Inbox and AgentState repositories initialized")
    
    # Initialize InboxService
    inbox_agent_id = current_agent.id if current_agent else None
    if not inbox_agent_id:
        print("[Gateway] Warning: No current agent, InboxService initialized without agent_id")
    inbox_service = InboxService(agent_id=inbox_agent_id)
    inbox_service.set_event_bus(event_bus)
    print(f"[Gateway] InboxService initialized (agent_id={inbox_agent_id})")
    
    # Initialize InboxMonitor if we have an agent
    if current_agent:
        # Ensure agent state exists
        await agent_state_repo.ensure_exists(current_agent.id)
        
        # Recover any messages stuck in processing state
        recovered = await inbox_repo.recover_processing(current_agent.id)
        if recovered:
            print(f"[Gateway] Recovered {recovered} messages stuck in processing state")
        
        # InboxMonitor and AgentRunner will be initialized when agent is created in routes.py
        print(f"[Gateway] Inbox system ready for agent {current_agent.id}")


async def shutdown_systems():
    """Shutdown all system components."""
    global event_bus, wake_controller
    
    if wake_controller:
        await wake_controller.stop()
        print("[Gateway] WakeController stopped")
    
    if event_bus:
        await event_bus.stop()
        print("[Gateway] EventBus stopped")


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
    global mcp_gateway_manager, _cleanup_task
    
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
    
    # Initialize MCP Gateway Manager (after app is ready)
    mcp_gateway_manager = MCPGatewayManager(app)
    set_mcp_gateway_manager(mcp_gateway_manager)
    print("[Gateway] MCPGatewayManager initialized")
    
    # Setup MCP Gateways for existing agents
    try:
        count = await mcp_gateway_manager.setup_existing_agents()
        print(f"[Gateway] MCP Gateways setup for {count} agents")
    except Exception as e:
        print(f"[Gateway] Warning: Failed to setup MCP Gateways: {e}")
    
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
    
    yield
    
    # Cancel cleanup task
    if _cleanup_task:
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        print("[Gateway] Periodic task cleanup stopped")
    
    # Shutdown MCP Gateway Manager
    if mcp_gateway_manager:
        await mcp_gateway_manager.close_all()
        print("[Gateway] MCPGatewayManager closed")
    
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


# Root endpoint
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "name": "NovAIC Gateway",
        "version": "0.4.0",
        "description": "Unified control plane for NovAIC AI Agent",
        "components": {
            "event_bus": "active" if event_bus and event_bus.is_running else "inactive",
            "state_manager": state_manager.get_state().value if state_manager else "not_initialized",
            "mcp_gateway": f"{len(mcp_gateway_manager.gateways)} agents" if mcp_gateway_manager else "not_initialized",
            "wake_controller": f"{wake_controller.get_stats()['total_triggers']} triggers" if wake_controller else "not_initialized",
        }
    }


# System status endpoint
@app.get("/api/system/status")
async def system_status():
    """Get detailed system status"""
    # Get gateway stats for current agent
    gateway_stats = None
    if mcp_gateway_manager:
        agents = mcp_gateway_manager.list_agents()
        gateway_stats = {
            "agents_count": len(agents),
            "agents": agents,
        }
    
    return {
        "event_bus": event_bus.get_stats() if event_bus else None,
        "state_manager": state_manager.get_info() if state_manager else None,
        "mcp_gateway": gateway_stats,
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


@app.post("/api/internal/sessions/spawn")
async def spawn_subagent(data: dict):
    """Spawn a sub-agent (internal API)"""
    if not subagent_manager:
        return {"error": "SubAgentManager not initialized", "success": False}
    
    from agent.subagent.manager import SubAgentConfig
    
    config = SubAgentConfig(
        task=data.get("task", ""),
        model=data.get("model"),
        timeout_minutes=data.get("timeout_minutes", 30),
        announce=data.get("announce", True),
        context=data.get("context"),
        copy_context=data.get("copy_context", False),
        task_instruction=data.get("task_instruction"),
    )
    
    result = await subagent_manager.spawn(
        config=config,
        parent_session_id=data.get("parent_session_id", "main"),
        wait=data.get("wait", False),
    )
    
    return result


@app.get("/api/internal/sessions/subagent/{subagent_id}/status")
async def get_subagent_status(subagent_id: str):
    """Get sub-agent status (internal API)"""
    if not subagent_manager:
        return {"error": "SubAgentManager not initialized", "status": "unknown"}
    
    status = subagent_manager.get_status(subagent_id)
    if not status:
        return {"error": "Sub-agent not found", "status": "unknown"}
    
    return status


@app.post("/api/internal/sessions/subagent/{subagent_id}/cancel")
async def cancel_subagent(subagent_id: str):
    """Cancel a sub-agent (internal API)"""
    if not subagent_manager:
        return {"error": "SubAgentManager not initialized", "success": False}
    
    return await subagent_manager.cancel(subagent_id)


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

# Agent execution lock - ensures only one agent task runs at a time
_agent_lock = asyncio.Lock()
_current_agent_task: Optional[asyncio.Task] = None


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


@app.post("/api/chat/event")
async def receive_chat_event(data: dict):
    """
    Receive chat events from novaic-mcp-chat.
    
    This is called when the Agent uses chat tools (chat_reply, chat_ask, etc.)
    Events are stored and broadcast to all SSE subscribers.
    """
    event_type = data.get("type", "")
    event_data = data.get("data", {})
    
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
    
    # Also publish to EventBus as USER_RESPONSE event
    if event_bus:
        from agent.events.models import AgentEvent, EventType
        event = AgentEvent(
            type=EventType.USER_RESPONSE,
            source="user",
            payload={
                "request_id": request_id,
                "response": data.get("response", ""),
                "selected_option": data.get("selected_option"),
            }
        )
        await event_bus.publish(event)
    
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

@app.post("/api/inbox")
async def add_to_inbox(data: dict):
    """
    Unified API for adding messages to Agent's inbox.
    
    All input messages (user, system, webhook, etc.) should use this endpoint.
    
    Request body:
    - type: Message type (USER_MESSAGE, SYSTEM_MESSAGE, WEBHOOK, CRON_TRIGGER, SUBAGENT_RESULT)
    - content: Message content
    - priority: Optional priority (critical, high, normal, low). Default: normal
    - source: Optional source identifier (user, system:bootstrap, webhook:xxx, etc.)
    - metadata: Optional additional data
    - agent_id: Optional target agent ID (defaults to current agent)
    
    Response:
    - success: Boolean
    - message_id: ID of the created message
    - timestamp: Creation timestamp
    """
    from api.inbox_service import get_inbox_service
    
    msg_type = data.get("type", "USER_MESSAGE")
    content = data.get("content", "").strip()
    priority = data.get("priority", "normal")
    source = data.get("source", "user")
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
    
    try:
        inbox_svc = get_inbox_service()
        
        # Set SSE broadcast callback
        inbox_svc.set_sse_broadcast(broadcast_chat_message)
        
        msg = await inbox_svc.add_message(
            msg_type=msg_type,
            content=content,
            priority=priority,
            source=source,
            metadata=metadata,
            agent_id=agent_id,
        )
        
        return {
            "success": True,
            "message_id": msg["id"],
            "timestamp": msg["created_at"],
            "status": "pending",
        }
    
    except Exception as e:
        print(f"[Inbox] Error adding message: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/inbox/summary")
async def get_inbox_summary():
    """
    Get inbox summary for the current agent.
    
    Returns:
    - pending_count: Number of pending messages
    - messages: List of pending messages (truncated content)
    """
    from api.inbox_service import get_inbox_service
    
    agent_id = get_current_agent_id()
    if not agent_id:
        return {"success": False, "error": "No agent selected", "pending_count": 0, "messages": []}
    
    inbox_svc = get_inbox_service()
    
    try:
        summary = await inbox_svc.get_inbox_summary(agent_id)
        return {"success": True, **summary}
    except Exception as e:
        print(f"[Inbox] Error getting summary: {e}")
        return {"success": False, "error": str(e)}


# ==================== User Chat API (User -> Agent Communication) ====================
# Note: /api/chat/send is a compatibility layer that forwards to /api/inbox

@app.post("/api/chat/send")
async def send_chat_message(data: dict):
    """
    Send a user message (fire-and-forget style).
    
    The message is stored and broadcast, then processed asynchronously.
    - If agent is idle: starts processing immediately
    - If agent is busy: message goes to inbox, agent sees it via inbox_check
    
    Returns immediately with message_id and 'delivered' status.
    """
    chat_service = get_chat_service()
    agent_id = get_current_agent_id()
    
    if not agent_id:
        return {"success": False, "error": "No agent selected. Please select an agent first."}
    
    content = data.get("message", "").strip()
    model = data.get("model")
    mode = data.get("mode", "agent")
    api_key_id = data.get("api_key_id")
    
    if not content:
        return {"success": False, "error": "Message content required"}
    
    # Generate message ID
    message_id = str(uuid_module.uuid4())[:12]
    timestamp = datetime.now().isoformat()
    
    # Create user message
    user_msg = {
        "id": message_id,
        "type": "USER_MESSAGE",
        "content": content,
        "timestamp": timestamp,
        "status": "delivered",  # Backend received it
        "model": model,
        "api_key_id": api_key_id,
    }
    
    # Broadcast user message (this also saves to database, pass agent_id for correct routing)
    await broadcast_chat_message(user_msg, agent_id=agent_id)
    
    # Auto-respond to any pending questions
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
            print(f"[Chat] Auto-responded to pending question {request_id} with user message")
    
    # Check if agent is busy (from database)
    runtime_state = await chat_service.repo.get_agent_runtime_state(agent_id)
    agent_busy = runtime_state.get("agent_busy", False) if runtime_state else False
    
    if agent_busy:
        # Agent is busy - message stays unread in inbox
        # (Already saved via broadcast_chat_message with read=0)
        unread_count = await chat_service.repo.get_message_count(agent_id, read=False)
        print(f"[Chat] Agent busy, message {message_id} stays in inbox (unread: {unread_count})")
        return {
            "success": True,
            "message_id": message_id,
            "status": "delivered",
            "queued": True,
            "timestamp": timestamp,
            "note": "Agent is busy, message added to inbox"
        }
    
    # Process message asynchronously with execution lock
    async def process_message():
        global _current_agent_task
        aid = agent_id  # Capture agent_id from outer scope
        
        # Acquire lock to ensure only one agent task runs at a time
        async with _agent_lock:
            # Set agent busy in database
            await chat_service.repo.set_agent_busy(aid, True)
            print(f"[Chat] Acquired agent lock for message {message_id}, agent_busy=True")
            try:
                # Mark message as read when agent starts processing
                await update_message_status(message_id, "read")
                
                # Get agent instance
                from api.routes import get_agent
                from config import get_config_manager
                
                agent = get_agent()
                config = get_config_manager().load()
                
                # Resolve model configuration from API keys
                resolved_model = model or config.default_model
                resolved_provider = None
                resolved_api_base = None
                resolved_api_key = None
                
                # Find the right API key entry
                target_key = None
                if api_key_id and config.api_keys:
                    # Use specified api_key_id
                    for key in config.api_keys:
                        if key.id == api_key_id:
                            target_key = key
                            break
                elif config.api_keys:
                    # Use first available API key
                    target_key = config.api_keys[0]
                
                if target_key:
                    resolved_provider = target_key.provider.value if hasattr(target_key.provider, 'value') else target_key.provider
                    resolved_api_base = target_key.api_base
                    resolved_api_key = target_key.api_key
                
                # Initialize agent if needed
                if not agent._tools_initialized:
                    await agent.initialize()
                
                # Process with agent (logs will be broadcast via broadcast_log)
                final_content = None
                chat_reply_called = False  # Track if agent used chat_reply MCP tool
                
                async for event in agent.chat(
                    user_message=content,
                    model=resolved_model,
                    provider=resolved_provider,
                    api_base=resolved_api_base,
                    api_key=resolved_api_key,
                ):
                    event_type = event.get("type", "unknown")
                    event_data = event.get("data", {})
                    
                    # Broadcast execution logs
                    log_entry = {
                        "type": event_type,
                        "timestamp": datetime.now().isoformat(),
                        "data": event_data,
                        "message_id": message_id,
                    }
                    await broadcast_log(log_entry)
                    
                    # Track if chat_reply was called
                    if event_type == "tool_end":
                        tool_name = event_data.get("tool", "") if isinstance(event_data, dict) else ""
                        if tool_name == "chat_reply":
                            chat_reply_called = True
                    
                    # Capture final response content for fallback
                    if event_type == "final":
                        if isinstance(event_data, str):
                            final_content = event_data
                        elif isinstance(event_data, dict):
                            final_content = event_data.get("content") or event_data.get("data") or str(event_data)
                        else:
                            final_content = str(event_data)
                
                # Fallback: If agent didn't use chat_reply, send final_content as reply
                if not chat_reply_called and final_content:
                    print(f"[Chat] Agent didn't use chat_reply, fallback sending final_content")
                    agent_reply = {
                        "id": str(uuid_module.uuid4())[:12],
                        "type": "AGENT_REPLY",
                        "timestamp": datetime.now().isoformat(),
                        "message": final_content,
                    }
                    await broadcast_chat_message(agent_reply, agent_id=aid)
                
                # Agent finished processing - execution state will be updated by AGENT_REPLY handler
                
            except Exception as e:
                print(f"[Chat] Error processing message {message_id}: {e}")
                # Broadcast error log
                await broadcast_log({
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"error": str(e)},
                    "message_id": message_id,
                })
            finally:
                await chat_service.repo.set_agent_busy(aid, False)
                print(f"[Chat] Released agent lock for message {message_id}, agent_busy=False")
    
    # Fire and forget - don't await
    asyncio.create_task(process_message())
    
    return {
        "success": True,
        "message_id": message_id,
        "status": "delivered",
        "timestamp": timestamp,
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


# ==================== Agent Self-Scheduling API ====================

@app.get("/api/agent/inbox")
async def get_agent_inbox():
    """
    Get pending events in the agent's inbox.
    
    Returns summary of pending events for agent to check during execution.
    Includes unread user messages.
    """
    from agent.events.handler import AgentEventHandler
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
    
    # Check EventBus queue (note: this is a peek, not consume)
    if event_bus:
        # Get stats which includes queue size
        stats = event_bus.get_stats()
        queue_size = stats.get("queue_size", 0)
        
        # Also check if there are any pending questions from chat (from database)
        pending_questions = await chat_service.repo.get_all_pending_questions(agent_id)
        
        for q in pending_questions:
            pending_events.append({
                "type": "user_question_pending",
                "summary": f"用户问题等待回复: {q.get('question', '')[:50]}...",
                "timestamp": q.get("timestamp"),
                "priority": "high"
            })
        
        # Add info about queued events
        if queue_size > 0:
            pending_events.append({
                "type": "queued_events",
                "summary": f"{queue_size} 个事件在队列中等待处理",
                "priority": "normal"
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
        
        # Clear busy flag in database
        await chat_service.repo.set_agent_busy(agent_id, False)
        
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
