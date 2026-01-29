"""
NovAIC Gateway - WebSocket Handler

Provides real-time bidirectional communication for chat and events.

Features:
- Heartbeat: Server periodically pings clients to detect zombie connections
- Auto-cleanup: Disconnected clients are automatically removed
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional, Any
from datetime import datetime
import asyncio
import json
import time

from core.agent import NovAICAgent
from config.manager import get_config_manager

router = APIRouter()

# Heartbeat configuration
HEARTBEAT_INTERVAL = 30  # seconds between heartbeats
HEARTBEAT_TIMEOUT = 10   # seconds to wait for pong response


class ConnectionManager:
    """Manages WebSocket connections with heartbeat support"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._agents: Dict[str, Any] = {}  # client_id -> agent instance
        self._last_pong: Dict[str, float] = {}  # client_id -> last pong timestamp
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self._last_pong[client_id] = time.time()  # Initialize pong time
        print(f"[WS] Client {client_id} connected. Total: {len(self.active_connections)}")
        
        # Start heartbeat loop if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        self.active_connections.pop(client_id, None)
        self._agents.pop(client_id, None)
        self._last_pong.pop(client_id, None)
        print(f"[WS] Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    def record_pong(self, client_id: str):
        """Record that we received a pong from client"""
        self._last_pong[client_id] = time.time()
    
    async def _heartbeat_loop(self):
        """
        Background task that sends heartbeat pings to all clients.
        Detects and removes zombie connections.
        """
        print("[WS] Heartbeat loop started")
        while self.active_connections:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            
            if not self.active_connections:
                break
            
            current_time = time.time()
            disconnected = []
            
            for client_id, ws in list(self.active_connections.items()):
                # Check if client missed too many heartbeats
                last_pong = self._last_pong.get(client_id, 0)
                if current_time - last_pong > HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT:
                    print(f"[WS] Client {client_id} heartbeat timeout, disconnecting...")
                    disconnected.append(client_id)
                    continue
                
                # Send ping
                try:
                    await ws.send_json({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"[WS] Failed to send heartbeat to {client_id}: {e}")
                    disconnected.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected:
                self.disconnect(client_id)
        
        print("[WS] Heartbeat loop stopped (no active connections)")
    
    async def send_event(self, client_id: str, event_type: str, data: Any):
        """Send an event to a specific client"""
        if ws := self.active_connections.get(client_id):
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            try:
                await ws.send_json(event)
            except Exception as e:
                print(f"[WS] Failed to send to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, event_type: str, data: Any):
        """Broadcast an event to all connected clients"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        disconnected = []
        for client_id, ws in self.active_connections.items():
            try:
                await ws.send_json(event)
            except Exception:
                disconnected.append(client_id)
        
        for client_id in disconnected:
            self.disconnect(client_id)
    
    def get_agent(self, client_id: str):
        """Get or create agent for a client"""
        return self._agents.get(client_id)
    
    def set_agent(self, client_id: str, agent):
        """Set agent for a client"""
        self._agents[client_id] = agent


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time chat communication.
    
    Client -> Server messages:
    - {"type": "chat", "message": "...", "model": "...", "mode": "agent|chat", "api_key_id": "..."}
    - {"type": "interrupt"}
    - {"type": "clear"}
    - {"type": "ping"}
    
    Server -> Client events:
    - {"type": "thinking", "data": "...", "timestamp": "..."}
    - {"type": "tool_start", "data": {...}, "timestamp": "..."}
    - {"type": "tool_end", "data": {...}, "timestamp": "..."}
    - {"type": "final", "data": "...", "timestamp": "..."}
    - {"type": "error", "data": {...}, "timestamp": "..."}
    - {"type": "pong", "data": null, "timestamp": "..."}
    """
    await connection_manager.connect(websocket, client_id)
    
    # Get or create agent for this client
    agent = connection_manager.get_agent(client_id)
    if agent is None:
        config = get_config_manager().load()
        
        # Try to get ToolRegistry from main
        tool_registry = None
        try:
            from main import get_tool_registry
            tool_registry = get_tool_registry()
        except ImportError:
            pass
        
        agent = NovAICAgent(mcp_port=config.mcp_port, tool_registry=tool_registry)
        agent.max_iterations = config.max_iterations
        agent.max_tokens = config.max_tokens
        connection_manager.set_agent(client_id, agent)
        
        # Register websocket session
        try:
            from agent.session.registry import get_session_registry, SessionType
            registry = get_session_registry()
            session_key = f"ws:{client_id}"
            registry.register(
                session_key=session_key,
                session_type=SessionType.WEBSOCKET,
                agent=agent,
                session_manager=agent.session,
                metadata={"client_id": client_id},
            )
        except Exception:
            pass
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            
            if msg_type == "ping":
                # Client initiated ping
                await connection_manager.send_event(client_id, "pong", None)
                connection_manager.record_pong(client_id)  # Also counts as activity
                
            elif msg_type == "pong":
                # Response to server heartbeat
                connection_manager.record_pong(client_id)
                
            elif msg_type == "chat":
                await handle_chat(client_id, agent, data)
                
            elif msg_type == "interrupt":
                agent.interrupt()
                await connection_manager.send_event(client_id, "status", {"message": "Interrupted"})
                
            elif msg_type == "clear":
                agent.clear_messages()
                await connection_manager.send_event(client_id, "status", {"message": "History cleared"})
                
            else:
                await connection_manager.send_event(client_id, "error", {"error": f"Unknown message type: {msg_type}"})
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        # Unregister session
        try:
            from agent.session.registry import get_session_registry
            get_session_registry().unregister(f"ws:{client_id}")
        except Exception:
            pass
    except Exception as e:
        print(f"[WS] Error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)
        # Unregister session
        try:
            from agent.session.registry import get_session_registry
            get_session_registry().unregister(f"ws:{client_id}")
        except Exception:
            pass


async def handle_chat(client_id: str, agent, data: dict):
    """Handle a chat message from the client"""
    
    message = data.get("message", "")
    model_id = data.get("model")
    mode = data.get("mode", "agent")
    api_key_id = data.get("api_key_id")
    
    print(f"[WS] handle_chat: model={model_id}, api_key_id={api_key_id}, mode={mode}")
    
    if not message:
        await connection_manager.send_event(client_id, "error", {"error": "Empty message"})
        return
    
    # Get state manager for tracking
    state_manager = None
    try:
        from main import get_state_manager, publish_user_event
        state_manager = get_state_manager()
    except ImportError:
        pass
    
    # Track state: set to BUSY
    if state_manager:
        from agent.core.state import AgentState
        state_manager.set_state(AgentState.BUSY)
        state_manager.record_activity()
    
    # Publish event for tracking (non-blocking)
    try:
        await publish_user_event(message, session_id=f"ws:{client_id}", source="websocket", reply_channel="websocket")
    except Exception:
        pass
    
    # Update session activity
    try:
        from agent.session.registry import get_session_registry
        get_session_registry().update_activity(f"ws:{client_id}")
    except Exception:
        pass
    
    # Get API configuration
    config = get_config_manager().load()
    
    # Resolve model and API key
    provider = None
    api_base = None
    api_key = None
    
    if api_key_id:
        # Use specified API key
        key_entry = config.get_api_key_by_id(api_key_id)
        if key_entry and key_entry.api_key:
            provider = key_entry.provider.value
            api_base = key_entry.get_effective_base_url()
            api_key = key_entry.api_key
            print(f"[WS] Using specified API key: {api_key_id}, provider={provider}")
    
    if not api_key:
        # Find first API key with credentials
        for key_entry in config.api_keys:
            if key_entry.api_key and key_entry.api_key.strip():
                provider = key_entry.provider.value
                api_base = key_entry.get_effective_base_url()
                api_key = key_entry.api_key
                print(f"[WS] Using fallback API key: {key_entry.id}, provider={provider}")
                break
    
    if not api_key:
        await connection_manager.send_event(client_id, "error", {"error": "No API key configured"})
        return
    
    # Use default model if not specified
    if not model_id:
        model_id = config.default_model
        print(f"[WS] No model specified, using default: {model_id}")
    
    print(f"[WS] Final: model={model_id}, provider={provider}, api_base={api_base}")
    
    # Execute chat
    try:
        if mode == "chat":
            chat_gen = agent.simple_chat(
                message, 
                model=model_id, 
                provider=provider, 
                api_base=api_base, 
                api_key=api_key
            )
        else:
            chat_gen = agent.chat_with_logs(
                message, 
                model=model_id, 
                provider=provider, 
                api_base=api_base, 
                api_key=api_key
            )
        
        async for event in chat_gen:
            await connection_manager.send_event(client_id, event["type"], event["data"])
            
    except Exception as e:
        print(f"[WS] Chat error for {client_id}: {e}")
        await connection_manager.send_event(client_id, "error", {"error": str(e)})
    finally:
        # Return to AWAKE state
        if state_manager:
            from agent.core.state import AgentState
            state_manager.set_state(AgentState.AWAKE)
