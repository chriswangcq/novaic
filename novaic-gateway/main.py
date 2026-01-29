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
from agent.events.models import AgentEvent, EventType, EventPriority
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
event_handler: AgentEventHandler = None


# ==================== Component Accessors ====================

def get_tool_registry() -> ToolRegistry:
    """Get the global ToolRegistry instance."""
    return tool_registry


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
    global event_bus, state_manager, tool_registry, wake_controller, micro_engine, subagent_manager, event_handler
    
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
    session_enabled = os.getenv("NOVAIC_MCP_SESSION_ENABLED", "true").lower() == "true"
    tool_registry.register_server(
        name="session",
        port=session_port,
        enabled=session_enabled,
        priority=1,
    )
    
    # Register Local MCP Server (host)
    local_port = int(os.getenv("NOVAIC_MCP_LOCAL_PORT", "8082"))
    local_enabled = os.getenv("NOVAIC_MCP_LOCAL_ENABLED", "true").lower() == "true"
    tool_registry.register_server(
        name="local",
        port=local_port,
        enabled=local_enabled,
        priority=2,
    )
    
    # Register QEMU MCP Server (host)
    qemu_port = int(os.getenv("NOVAIC_MCP_QEMUDEBUG_PORT", "8083"))
    qemu_enabled = os.getenv("NOVAIC_MCP_QEMUDEBUG_ENABLED", "false").lower() == "true"  # Default disabled (fallback only)
    tool_registry.register_server(
        name="qemudebug",
        port=qemu_port,
        enabled=qemu_enabled,
        priority=3,  # Lowest priority
    )
    
    # Register Memory MCP Server (host)
    memory_port = int(os.getenv("NOVAIC_MCP_MEMORY_PORT", "8084"))
    memory_enabled = os.getenv("NOVAIC_MCP_MEMORY_ENABLED", "true").lower() == "true"  # Default enabled
    tool_registry.register_server(
        name="memory",
        port=memory_port,
        enabled=memory_enabled,
        priority=1,  # High priority (host-based memory)
    )
    
    # Register Chat MCP Server (host - Agent<->User communication)
    chat_port = int(os.getenv("NOVAIC_MCP_CHAT_PORT", "8085"))
    chat_enabled = os.getenv("NOVAIC_MCP_CHAT_ENABLED", "true").lower() == "true"  # Default enabled
    tool_registry.register_server(
        name="chat",
        port=chat_port,
        enabled=chat_enabled,
        priority=0,  # Highest priority (essential for user interaction)
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
    
    # Initialize SubAgentManager (with agent factory using ToolRegistry)
    async def create_agent_for_session(session_key: str):
        """Factory to create agent for sub-sessions using the shared ToolRegistry."""
        from core.agent import NovAICAgent
        agent = NovAICAgent(mcp_port=config.mcp_port, tool_registry=tool_registry)
        await agent.initialize()
        return agent
    
    subagent_manager = SubAgentManager(
        agent_factory=create_agent_for_session,
        max_concurrent=5,
    )
    print("[Gateway] SubAgentManager initialized")
    
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
from collections import deque
from typing import Dict, Any
import uuid as uuid_module

# Chat message store (for SSE streaming to frontend)
_chat_messages: deque = deque(maxlen=100)  # Recent chat messages
_chat_subscribers: Dict[str, asyncio.Queue] = {}  # SSE subscribers

# Pending questions (agent asking user)
_pending_questions: Dict[str, Dict[str, Any]] = {}  # request_id -> question data
_question_responses: Dict[str, Dict[str, Any]] = {}  # request_id -> user response


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
    
    # Store message
    _chat_messages.append(chat_message)
    
    # Handle AGENT_ASK specially - store pending question
    if event_type == "AGENT_ASK":
        request_id = event_data.get("request_id") or message_id
        _pending_questions[request_id] = {
            "question": event_data.get("question"),
            "options": event_data.get("options"),
            "timestamp": timestamp,
            "message_id": message_id,
        }
        chat_message["request_id"] = request_id
    
    # Broadcast to all SSE subscribers
    for queue in _chat_subscribers.values():
        try:
            queue.put_nowait(chat_message)
        except asyncio.QueueFull:
            pass  # Skip if subscriber's queue is full
    
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
            # Send recent messages first
            for msg in list(_chat_messages)[-10:]:
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
    if request_id not in _pending_questions:
        return {"error": "Question not found", "has_response": False}
    
    if request_id in _question_responses:
        response = _question_responses.pop(request_id)
        _pending_questions.pop(request_id, None)
        return {"has_response": True, **response}
    
    return {"has_response": False}


@app.post("/api/chat/respond/{request_id}")
async def submit_user_response(request_id: str, data: dict):
    """
    Submit user's response to an agent's question.
    
    Called by frontend when user answers a question from the agent.
    """
    if request_id not in _pending_questions:
        return {"error": "Question not found or expired", "success": False}
    
    # Store response
    _question_responses[request_id] = {
        "response": data.get("response", ""),
        "selected_option": data.get("selected_option"),
        "timestamp": datetime.now().isoformat(),
    }
    
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
    return {
        "questions": [
            {"request_id": rid, **qdata}
            for rid, qdata in _pending_questions.items()
        ]
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
    
    # Get all messages as a list
    all_messages = list(_chat_messages)
    
    # Filter by message_type if specified
    if message_type:
        type_map = {
            "user": ["USER_MESSAGE"],
            "agent": ["AGENT_REPLY", "AGENT_IMAGE"],
            "notification": ["AGENT_NOTIFY"],
            "question": ["AGENT_ASK"],
        }
        allowed_types = type_map.get(message_type, [message_type.upper()])
        all_messages = [m for m in all_messages if m.get("type") in allowed_types]
    
    # Filter by before_id if specified
    if before_id:
        found_idx = None
        for i, msg in enumerate(all_messages):
            if msg.get("id") == before_id:
                found_idx = i
                break
        if found_idx is not None:
            all_messages = all_messages[:found_idx]
    
    # Get the last `limit` messages
    messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
    has_more = len(all_messages) > limit
    
    # Create summarized messages
    summarized = []
    for msg in messages:
        content = msg.get("message") or msg.get("question") or ""
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
    
    return {
        "success": True,
        "messages": summarized,
        "has_more": has_more,
        "total_in_memory": len(_chat_messages),
    }


@app.get("/api/chat/message/{message_id}")
async def get_chat_message(message_id: str):
    """
    Get full content of a specific chat message.
    
    Args:
        message_id: The message ID
    """
    for msg in _chat_messages:
        if msg.get("id") == message_id:
            return {"success": True, **msg}
    
    return {"success": False, "error": "Message not found"}


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
