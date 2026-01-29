"""
NovAIC Gateway - Main Entry Point

Unified control plane that serves:
- REST API (/api/*)
- WebSocket (/ws/*)
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

# ==================== Logging Setup ====================
# Log directory: ~/.novaic/logs/
LOG_DIR = os.path.expanduser("~/.novaic/logs")
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
from api.ws import router as ws_router
from api.agents import router as agents_router
from config.manager import get_config_manager

# Import new components
from agent.events.bus import EventBus
from agent.events.handler import AgentEventHandler
from agent.core.state import StateManager, AgentState
from executor.registry import ToolRegistry
from agent.wake.controller import WakeController
from agent.micro.engine import MicroAgentEngine
from agent.subagent.manager import SubAgentManager


# Configuration
HOST = os.getenv("NOVAIC_HOST", "127.0.0.1")
PORT = int(os.getenv("NOVAIC_PORT", "9000"))
SOCKET_PATH = os.getenv("NOVAIC_SOCKET", "")  # Unix socket path, if set use UDS mode
DEBUG = os.getenv("NOVAIC_DEBUG", "false").lower() == "true"

# Global instances
event_bus: EventBus = None
state_manager: StateManager = None
tool_registry: ToolRegistry = None
wake_controller: WakeController = None
micro_engine: MicroAgentEngine = None
subagent_manager: SubAgentManager = None


async def initialize_systems(config):
    """Initialize all system components."""
    global event_bus, state_manager, tool_registry, wake_controller, micro_engine, subagent_manager
    
    # Initialize EventBus
    event_bus = EventBus()
    print("[Gateway] EventBus initialized")
    
    # Initialize StateManager
    state_manager = StateManager(
        initial_state=AgentState.AWAKE,
        idle_timeout=None,  # No auto-sleep for now
    )
    print("[Gateway] StateManager initialized")
    
    # Initialize ToolRegistry with MCP servers
    tool_registry = ToolRegistry()
    
    # Register VM MCP Server (primary, in VM)
    tool_registry.register_server(
        name="vm",
        port=config.mcp_port,
        priority=0,  # Highest priority
    )
    
    # Register Session MCP Server (host)
    session_port = int(os.getenv("NOVAIC_MCP_SESSION_PORT", "8081"))
    tool_registry.register_server(
        name="session",
        port=session_port,
        enabled=False,  # Disabled until deployed
        priority=1,
    )
    
    # Register Local MCP Server (host)
    local_port = int(os.getenv("NOVAIC_MCP_LOCAL_PORT", "8082"))
    tool_registry.register_server(
        name="local",
        port=local_port,
        enabled=False,  # Disabled until deployed
        priority=2,
    )
    
    # Register QEMU MCP Server (host)
    qemu_port = int(os.getenv("NOVAIC_MCP_QEMU_PORT", "8083"))
    tool_registry.register_server(
        name="qemu",
        port=qemu_port,
        enabled=False,  # Disabled until deployed
        priority=3,
    )
    
    print(f"[Gateway] ToolRegistry initialized with {len(tool_registry._servers)} servers")
    
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
    print("[Gateway] MicroAgentEngine initialized")
    
    # Initialize SubAgentManager (with placeholder factory)
    async def create_agent_for_session(session_key: str):
        """Factory to create agent for sub-sessions."""
        from agent.core.agent import NovAICAgent
        agent = NovAICAgent(mcp_port=config.mcp_port)
        await agent.initialize()
        return agent
    
    subagent_manager = SubAgentManager(
        agent_factory=create_agent_for_session,
        max_concurrent=5,
    )
    print("[Gateway] SubAgentManager initialized")
    
    # Start EventBus
    await event_bus.start()
    print("[Gateway] EventBus started")
    
    # Start WakeController (starts all enabled triggers)
    await wake_controller.start()
    print("[Gateway] WakeController started")


async def shutdown_systems():
    """Shutdown all system components."""
    global event_bus, wake_controller
    
    if wake_controller:
        await wake_controller.stop()
        print("[Gateway] WakeController stopped")
    
    if event_bus:
        await event_bus.stop()
        print("[Gateway] EventBus stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    config = get_config_manager().load()
    
    if SOCKET_PATH:
        print(f"🚀 NovAIC Gateway starting on unix://{SOCKET_PATH}")
    else:
        print(f"🚀 NovAIC Gateway starting on http://{HOST}:{PORT}")
    print(f"📋 Config: {get_config_manager().config_file}")
    print(f"🔧 MCP Server: http://127.0.0.1:{config.mcp_port}/mcp")
    print(f"🤖 Default model: {config.default_model}")
    
    # Initialize all systems
    await initialize_systems(config)
    
    yield
    
    # Shutdown all systems
    await shutdown_systems()
    
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

# WebSocket routes
app.include_router(ws_router)


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
            "tool_registry": f"{len(tool_registry._servers)} servers" if tool_registry else "not_initialized",
            "wake_controller": f"{wake_controller.get_stats()['total_triggers']} triggers" if wake_controller else "not_initialized",
        }
    }


# System status endpoint
@app.get("/api/system/status")
async def system_status():
    """Get detailed system status"""
    return {
        "event_bus": event_bus.get_stats() if event_bus else None,
        "state_manager": state_manager.get_info() if state_manager else None,
        "tool_registry": tool_registry.get_stats() if tool_registry else None,
        "wake_controller": wake_controller.get_stats() if wake_controller else None,
        "micro_engine": micro_engine.get_stats() if micro_engine else None,
        "subagent_manager": subagent_manager.get_stats() if subagent_manager else None,
    }


# Internal API for session tools (called by novaic-mcp-session)
@app.get("/api/internal/sessions")
async def list_sessions():
    """List all sessions (internal API)"""
    # TODO: Implement session listing
    return {"sessions": []}


@app.post("/api/internal/sessions/{session_key}/history")
async def get_session_history(session_key: str, data: dict):
    """Get session history (internal API)"""
    # TODO: Implement session history
    return {"messages": []}


@app.post("/api/internal/sessions/{session_key}/send")
async def send_to_session(session_key: str, data: dict):
    """Send message to session (internal API)"""
    # TODO: Implement session messaging
    return {"success": True, "message_id": "todo"}


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
            <h2>WebSocket</h2>
            <p>Connect to <code>ws://localhost:9000/ws/{client_id}</code> for real-time chat.</p>
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
