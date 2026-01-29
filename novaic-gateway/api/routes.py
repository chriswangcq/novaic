"""
NovAIC Gateway - REST API Routes
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime
import json

from .schemas import (
    ChatRequest, ChatResponse, ChatResult,
    ApiKeyCreate, ApiKeyUpdate, ModelToggle, SettingsUpdate,
    HealthResponse, HistoryResponse
)
from config.manager import get_config_manager, ProviderType
from core.agent import NovAICAgent

router = APIRouter()

# Global agent instance (singleton per gateway process)
_agent: Optional[NovAICAgent] = None


def get_agent() -> NovAICAgent:
    """Get the global agent instance, creating if needed.
    
    Uses ToolRegistry if available (multi-MCP server mode).
    """
    global _agent
    if _agent is None:
        config = get_config_manager().load()
        
        # Try to get ToolRegistry from main
        tool_registry = None
        try:
            from main import get_tool_registry
            tool_registry = get_tool_registry()
        except ImportError:
            pass
        
        _agent = NovAICAgent(mcp_port=config.mcp_port, tool_registry=tool_registry)
        _agent.max_iterations = config.max_iterations
        _agent.max_tokens = config.max_tokens
        
        # Register main session in registry
        try:
            from agent.session.registry import get_session_registry, SessionType
            registry = get_session_registry()
            registry.register(
                session_key="main",
                session_type=SessionType.MAIN,
                agent=_agent,
                session_manager=_agent.session,
            )
        except Exception:
            pass
        
        # Set up inbox callback for self-scheduling
        try:
            import httpx
            async def get_inbox():
                async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                    resp = await client.get("http://127.0.0.1:9000/api/agent/inbox")
                    if resp.status_code == 200:
                        return resp.json()
                    return {"pending_count": 0, "events": []}
            _agent.set_inbox_callback(get_inbox)
        except Exception:
            pass
    return _agent


# ==================== Health ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - returns immediately without blocking on MCP"""
    agent = get_agent()
    
    # Don't block on MCP connection - just return current state
    # MCP initialization happens lazily on first chat request
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        agent_initialized=agent._tools_initialized,
        mcp_healthy=agent._executor_healthy or False,
        tools_count=len(agent.tools)
    )


# ==================== Config ====================

@router.get("/config")
async def get_config():
    """Get current configuration (public version, hides API keys)"""
    config = get_config_manager().load()
    return config.to_public()


@router.patch("/config/settings")
async def update_settings(settings: SettingsUpdate):
    """Update common settings"""
    get_config_manager().update_settings(
        default_model=settings.default_model,
        max_tokens=settings.max_tokens,
        max_iterations=settings.max_iterations,
        visible_shell=settings.visible_shell,
    )
    
    # Update agent settings
    agent = get_agent()
    config = get_config_manager().load()
    agent.max_iterations = config.max_iterations
    agent.max_tokens = config.max_tokens
    
    return {"status": "ok"}


# ==================== API Keys ====================

@router.post("/config/api-keys")
async def add_api_key(data: ApiKeyCreate):
    """Add a new API key"""
    try:
        provider = ProviderType(data.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {data.provider}")
    
    entry = get_config_manager().add_api_key(
        provider=provider,
        name=data.name,
        api_key=data.api_key,
        api_base=data.api_base,
        deployment_name=data.deployment_name,
        api_version=data.api_version,
    )
    
    return entry.to_public()


@router.patch("/config/api-keys/{key_id}")
async def update_api_key(key_id: str, data: ApiKeyUpdate):
    """Update an existing API key"""
    entry = get_config_manager().update_api_key(
        key_id=key_id,
        name=data.name,
        api_key=data.api_key,
        api_base=data.api_base,
        deployment_name=data.deployment_name,
        api_version=data.api_version,
    )
    
    if entry is None:
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    return entry.to_public()


@router.delete("/config/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Delete an API key"""
    if not get_config_manager().delete_api_key(key_id):
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    return {"status": "ok"}


# ==================== Models ====================

@router.post("/config/models/toggle")
async def toggle_model(data: ModelToggle):
    """Toggle model enabled state"""
    if not get_config_manager().toggle_model(data.model_id, data.api_key_id, data.enabled):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "ok"}


@router.delete("/config/models/{api_key_id}/{model_id}")
async def delete_model(api_key_id: str, model_id: str):
    """Delete a model"""
    if not get_config_manager().delete_model(model_id, api_key_id):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "ok"}


@router.post("/config/api-keys/{key_id}/models")
async def save_models_for_key(key_id: str, models: List[dict]):
    """Save/merge models for an API key (keeps existing custom models)"""
    get_config_manager().save_models_for_key(key_id, models)
    return {"status": "ok"}


@router.post("/config/api-keys/{key_id}/models/add")
async def add_model(key_id: str, data: dict):
    """Add a single custom model"""
    model_id = data.get("id")
    model_name = data.get("name", model_id)
    
    if not model_id:
        raise HTTPException(status_code=400, detail="Model ID required")
    
    if not get_config_manager().add_model(key_id, model_id, model_name):
        raise HTTPException(status_code=400, detail="Model already exists or API key not found")
    
    return {"status": "ok"}


@router.post("/config/api-keys/{key_id}/test")
async def test_api_key(key_id: str):
    """Test API key connection by making a simple API call"""
    import httpx
    
    config = get_config_manager().load()
    entry = config.get_api_key_by_id(key_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    if not entry.api_key:
        return {"success": False, "error": "No API key configured"}
    
    try:
        base_url = entry.get_effective_base_url()
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try a simple models list request
            if entry.provider.value == "openai":
                url = f"{base_url}/models"
                headers = {"Authorization": f"Bearer {entry.api_key}"}
            elif entry.provider.value == "anthropic":
                # Anthropic doesn't have a models endpoint, test with a minimal request
                url = f"{base_url}/messages"
                headers = {
                    "x-api-key": entry.api_key,
                    "anthropic-version": entry.api_version or "2024-02-01",
                    "Content-Type": "application/json"
                }
                # Send minimal request to check auth
                response = await client.post(url, headers=headers, json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}]
                })
                # 400 means auth worked but request was invalid - that's ok
                if response.status_code in [200, 400]:
                    return {"success": True}
                elif response.status_code == 401:
                    return {"success": False, "error": "Invalid API key"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            else:
                url = f"{base_url}/models"
                headers = {"Authorization": f"Bearer {entry.api_key}"}
            
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return {"success": True}
            elif response.status_code == 401:
                return {"success": False, "error": "Invalid API key"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Connection timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/config/api-keys/{key_id}/fetch-models")
async def fetch_models_for_key(key_id: str):
    """Fetch available models from the provider API"""
    import httpx
    
    config = get_config_manager().load()
    entry = config.get_api_key_by_id(key_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    if not entry.api_key:
        return []
    
    try:
        base_url = entry.get_effective_base_url()
        async with httpx.AsyncClient(timeout=30.0) as client:
            if entry.provider.value in ["openai", "azure", "openai_compatible"]:
                url = f"{base_url}/models"
                headers = {"Authorization": f"Bearer {entry.api_key}"}
                print(f"[API] Fetching models from {url}")
                response = await client.get(url, headers=headers)
                print(f"[API] Models response: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("data", [])
                    return [
                        {
                            "id": m.get("id"),
                            "name": m.get("id"),
                            "provider": entry.provider.value,
                            "api_key_id": key_id,
                            "enabled": False,
                            "is_custom": False
                        }
                        for m in models if m.get("id")
                    ]
                else:
                    print(f"[API] Models fetch failed: {response.text}")
            elif entry.provider.value == "anthropic":
                # Anthropic doesn't have a models list API, return common models
                return [
                    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic", "api_key_id": key_id, "enabled": False, "is_custom": False},
                    {"id": "claude-opus-4-20250514", "name": "Claude Opus 4", "provider": "anthropic", "api_key_id": key_id, "enabled": False, "is_custom": False},
                    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "api_key_id": key_id, "enabled": False, "is_custom": False},
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "api_key_id": key_id, "enabled": False, "is_custom": False},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic", "api_key_id": key_id, "enabled": False, "is_custom": False},
                ]
        return []
    except Exception as e:
        print(f"[API] Error fetching models: {e}")
        return []


@router.post("/config/default-model")
async def set_default_model(data: dict):
    """Set the default model"""
    model_id = data.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
    
    get_config_manager().set_default_model(model_id)
    return {"status": "ok"}


# ==================== Chat ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    agent = get_agent()
    config = get_config_manager().load()
    
    # Get state manager for tracking
    try:
        from main import get_state_manager, publish_user_event
        state_manager = get_state_manager()
    except ImportError:
        state_manager = None
    
    # Resolve API configuration
    provider, api_base, api_key = resolve_api_config(config, request)
    
    if not api_key:
        raise HTTPException(status_code=400, detail="No API key configured")
    
    model = request.model or config.default_model
    
    # Track state: set to BUSY while processing
    if state_manager:
        from agent.core.state import AgentState
        state_manager.set_state(AgentState.BUSY)
        state_manager.record_activity()
    
    # Publish event for tracking (non-blocking)
    try:
        await publish_user_event(request.message, source="http", reply_channel="http")
    except Exception:
        pass  # Don't fail on event publishing errors
    
    results = []
    try:
        if request.mode == "chat":
            async for event in agent.simple_chat(
                request.message, model=model, provider=provider, api_base=api_base, api_key=api_key
            ):
                results.append(ChatResult(
                    type=event["type"], 
                    data=event["data"],
                    timestamp=datetime.now().isoformat()
                ))
        else:
            async for event in agent.chat_with_logs(
                request.message, model=model, provider=provider, api_base=api_base, api_key=api_key
            ):
                results.append(ChatResult(
                    type=event["type"], 
                    data=event["data"],
                    timestamp=datetime.now().isoformat()
                ))
    finally:
        # Return to AWAKE state
        if state_manager:
            state_manager.set_state(AgentState.AWAKE)
    
    return ChatResponse(results=results)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint (SSE) - for backward compatibility"""
    agent = get_agent()
    config = get_config_manager().load()
    
    # Resolve API configuration
    provider, api_base, api_key = resolve_api_config(config, request)
    
    if not api_key:
        raise HTTPException(status_code=400, detail="No API key configured")
    
    model = request.model or config.default_model
    
    async def event_generator():
        try:
            if request.mode == "chat":
                chat_gen = agent.simple_chat(
                    request.message, model=model, provider=provider, api_base=api_base, api_key=api_key
                )
            else:
                chat_gen = agent.chat_with_logs(
                    request.message, model=model, provider=provider, api_base=api_base, api_key=api_key
                )
            
            async for event in chat_gen:
                event["timestamp"] = datetime.now().isoformat()
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            error_event = {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


def resolve_api_config(config, request: ChatRequest) -> tuple:
    """Resolve API configuration from request and config"""
    provider = request.provider
    api_base = request.api_base
    api_key = request.api_key
    
    # If API key ID specified, use that
    if request.api_key_id:
        key_entry = config.get_api_key_by_id(request.api_key_id)
        if key_entry and key_entry.api_key:
            provider = provider or key_entry.provider.value
            api_base = api_base or key_entry.get_effective_base_url()
            api_key = api_key or key_entry.api_key
    
    # If still no API key, find first available
    if not api_key:
        for key_entry in config.api_keys:
            if key_entry.api_key and key_entry.api_key.strip():
                provider = provider or key_entry.provider.value
                api_base = api_base or key_entry.get_effective_base_url()
                api_key = key_entry.api_key
                break
    
    return provider, api_base, api_key


# ==================== History ====================

@router.get("/history", response_model=HistoryResponse)
async def get_history():
    """Get chat history"""
    agent = get_agent()
    messages = agent.get_messages()
    return HistoryResponse(messages=messages)


@router.post("/clear")
async def clear_history():
    """Clear chat history"""
    agent = get_agent()
    agent.clear_messages()
    return {"status": "ok", "message": "History cleared"}


# ==================== Control ====================

@router.post("/interrupt")
async def interrupt():
    """Interrupt current execution"""
    agent = get_agent()
    agent.interrupt()
    return {"status": "ok", "message": "Interrupt signal sent"}


@router.post("/init")
async def init_agent():
    """Initialize the agent (for backward compatibility)"""
    agent = get_agent()
    await agent.initialize()
    return {"status": "ok", "message": "Agent initialized"}


# ==================== VNC ====================

import socket

def _check_port(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """Check if a port is listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# VNC ports (these are forwarded from QEMU)
VNC_PORT = 5900
WS_PORT = 6080


@router.get("/vnc/status")
async def vnc_status():
    """Get VNC status by checking ports"""
    vnc_ready = _check_port(VNC_PORT)
    ws_ready = _check_port(WS_PORT)
    
    return {
        "running": vnc_ready,
        "websockify_running": ws_ready,
        "port": VNC_PORT if vnc_ready else None,
        "ws_port": WS_PORT if ws_ready else None,
        "ready": vnc_ready and ws_ready
    }


@router.post("/vnc/start")
async def start_vnc():
    """
    Start VNC - in the current architecture, VNC runs inside the VM
    which is managed by Tauri. This endpoint just checks if VNC is ready.
    """
    vnc_ready = _check_port(VNC_PORT)
    ws_ready = _check_port(WS_PORT)
    
    if vnc_ready and ws_ready:
        return {
            "status": "running",
            "message": "VNC and websockify are already running",
            "port": VNC_PORT,
            "ws_port": WS_PORT
        }
    elif vnc_ready:
        return {
            "status": "started",
            "message": "VNC is running, websockify may still be starting",
            "port": VNC_PORT,
            "ws_port": WS_PORT
        }
    else:
        return {
            "status": "waiting",
            "message": "VNC not yet available. VM may still be starting.",
            "port": VNC_PORT,
            "ws_port": WS_PORT
        }


@router.post("/vnc/stop")
async def stop_vnc():
    """
    Stop VNC - in the current architecture, VNC is managed by the VM.
    This is a no-op but provided for API compatibility.
    """
    return {
        "status": "ok",
        "message": "VNC is managed by the VM. Use VM controls to stop."
    }
