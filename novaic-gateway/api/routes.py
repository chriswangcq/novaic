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
    """Get the global agent instance, creating if needed"""
    global _agent
    if _agent is None:
        config = get_config_manager().load()
        _agent = NovAICAgent(cid=config.vsock_cid)
        _agent.max_iterations = config.max_iterations
        _agent.max_tokens = config.max_tokens
    return _agent


# ==================== Health ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    agent = get_agent()
    health = await agent.check_executor_health()
    
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        agent_initialized=agent._tools_initialized,
        mcp_healthy=health.get("healthy", False),
        tools_count=health.get("tools_count", 0)
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
    """Save/replace all models for an API key"""
    get_config_manager().save_models_for_key(key_id, models)
    return {"status": "ok"}


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
    
    # Resolve API configuration
    provider, api_base, api_key = resolve_api_config(config, request)
    
    if not api_key:
        raise HTTPException(status_code=400, detail="No API key configured")
    
    model = request.model or config.default_model
    
    results = []
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
