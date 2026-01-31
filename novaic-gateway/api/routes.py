"""
NovAIC Gateway - REST API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
import json
import os
import shutil
import time
from pathlib import Path
import glob

from .schemas import (
    ChatRequest, ChatResponse, ChatResult,
    ApiKeyCreate, ApiKeyUpdate, ModelToggle, SettingsUpdate,
    HealthResponse, HistoryResponse
)
from config import get_config_manager, ProviderType
from core.agent import NovAICAgent

router = APIRouter()

# Global agent instance (keyed by agent_id for multi-agent support)
_agent: Optional[NovAICAgent] = None
_agent_id: Optional[str] = None  # Track which agent _agent was created for


def get_agent() -> NovAICAgent:
    """Get the agent instance for the current agent.
    
    Uses Gateway's ToolRegistry which has all sub-MCP servers registered.
    Re-creates the agent if the current agent has changed.
    """
    global _agent, _agent_id
    
    # Get current agent info
    from config.agents import get_agent_config_manager, allocate_ports_for_agent
    from mcp_gateway.manager import get_mcp_gateway_manager
    
    try:
        agent_mgr = get_agent_config_manager()
        current_agent = agent_mgr.get_current_agent()
        current_agent_id = current_agent.id if current_agent else None
        mcp_port = current_agent.vm.ports.vm if current_agent else allocate_ports_for_agent(0).vm
    except Exception:
        current_agent_id = None
        mcp_port = allocate_ports_for_agent(0).vm
    
    # Check if we need to recreate the agent (agent switched or not created yet)
    if _agent is None or _agent_id != current_agent_id:
        if _agent is not None:
            print(f"[Agent] Switching from agent {_agent_id} to {current_agent_id}")
        
        config = get_config_manager().load()
        
        # Get Gateway's registry (has VM + all sub-MCPs)
        tool_registry = None
        gateway_mgr = get_mcp_gateway_manager()
        if gateway_mgr and current_agent_id:
            gateway = gateway_mgr.get_gateway(current_agent_id)
            if gateway:
                tool_registry = gateway.registry
        
        _agent = NovAICAgent(mcp_port=mcp_port, tool_registry=tool_registry, session_key="main")
        _agent.max_iterations = config.max_iterations
        _agent.max_tokens = config.max_tokens
        _agent_id = current_agent_id
        
        print(f"[Agent] Created agent instance for {current_agent_id} with mcp_port={mcp_port}")
        
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
                    resp = await client.get("http://127.0.0.1:19999/api/agent/inbox")
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


@router.post("/config/cleanup")
async def cleanup_garbage(
    deep: bool = Query(False, description="Perform deep cleanup (vacuum db, remove all logs)"),
    days: int = Query(7, description="Remove logs older than N days"),
    clean_vm_cache: bool = Query(False, description="Remove cached VM base images (will need re-download)")
):
    """
    Clean up garbage configuration files and temporary data.
    
    Performs the following cleanup operations:
    1. Removes logs older than 'days' (or all logs if deep=True)
    2. Removes .DS_Store and ._* metadata files
    3. Removes .tmp and .bak temporary files
    4. Removes empty directories
    5. Vacuums the SQLite database (if deep=True)
    6. Removes orphaned agent directories (if deep=True)
    7. Removes cached VM images (if clean_vm_cache=True)
    """
    # Get data directory from environment variable
    data_dir = Path(os.environ.get("NOVAIC_DATA_DIR", os.path.expanduser("~/.novaic")))
    log_dir = data_dir / "logs"
    
    cleaned = {
        "logs": 0,
        "metadata_files": 0,
        "temp_files": 0,
        "empty_dirs": 0,
        "database_vacuumed": False,
        "orphaned_agents": 0,
        "vm_images": 0
    }
    
    try:
        # 1. Clean logs
        if log_dir.exists():
            cutoff = time.time() - (days * 86400)
            for log_file in log_dir.glob("*.log"):
                try:
                    if deep or log_file.stat().st_mtime < cutoff:
                        try:
                            log_file.unlink()
                            cleaned["logs"] += 1
                        except OSError:
                            pass
                except Exception:
                    pass

        # 2. Clean metadata and temp files recursively
        for root, dirs, files in os.walk(data_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                file_path = Path(root) / file
                if file == ".DS_Store" or file.startswith("._"):
                    try:
                        file_path.unlink()
                        cleaned["metadata_files"] += 1
                    except OSError:
                        pass
                elif file.endswith(".tmp") or file.endswith(".bak"):
                    try:
                        file_path.unlink()
                        cleaned["temp_files"] += 1
                    except OSError:
                        pass

        # 3. Clean empty directories
        for root, dirs, files in os.walk(data_dir, topdown=False):
            for d in dirs:
                dir_path = Path(root) / d
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        cleaned["empty_dirs"] += 1
                except OSError:
                    pass

        # 4. Vacuum database
        if deep:
            try:
                from db.database import get_database
                db = get_database()
                if db:
                    await db.vacuum()
                    cleaned["database_vacuumed"] = True
            except Exception as e:
                print(f"[Cleanup] Database vacuum failed: {e}")

        # 5. Clean orphaned agent directories (if deep=True)
        if deep:
            try:
                from config.agents import get_agent_config_manager
                agent_mgr = get_agent_config_manager()
                agent_config = agent_mgr.reload()
                valid_agent_ids = {a.id for a in agent_config.agents}
                
                # Check both vms/ and agents/ directories (legacy support)
                for dir_name in ["vms", "agents"]:
                    check_dir = data_dir / dir_name
                    if check_dir.exists():
                        for agent_dir in check_dir.iterdir():
                            if agent_dir.is_dir() and agent_dir.name not in valid_agent_ids:
                                try:
                                    shutil.rmtree(agent_dir)
                                    cleaned["orphaned_agents"] += 1
                                except Exception:
                                    pass
            except Exception as e:
                print(f"[Cleanup] Orphaned agent cleanup failed: {e}")

        # 6. Clean VM base images (if requested)
        if clean_vm_cache:
            try:
                # Check possible image locations
                image_dirs = [
                    data_dir / "images",
                    data_dir / "shared" / "images"
                ]
                
                for img_dir in image_dirs:
                    if img_dir.exists():
                        for img_file in img_dir.glob("*.img"):
                            try:
                                img_file.unlink()
                                cleaned["vm_images"] += 1
                            except Exception:
                                pass
                        for img_file in img_dir.glob("*.qcow2"):
                            # Only delete base images, not agent disks (which are usually in vms/)
                            # Base images usually have version numbers or 'cloudimg' in name
                            if "cloudimg" in img_file.name or "ubuntu" in img_file.name:
                                try:
                                    img_file.unlink()
                                    cleaned["vm_images"] += 1
                                except Exception:
                                    pass
            except Exception as e:
                print(f"[Cleanup] VM image cleanup failed: {e}")

        return {
            "status": "ok",
            "message": "Cleanup completed successfully",
            "details": cleaned
        }
        
    except Exception as e:
        print(f"[Cleanup] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


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

def _get_vnc_ports():
    """Get VNC/WebSocket ports from current agent config"""
    from config.agents import get_agent_config_manager, allocate_ports_for_agent
    
    try:
        agent_mgr = get_agent_config_manager()
        current_agent = agent_mgr.get_current_agent()
        if current_agent:
            return current_agent.vm.ports.vnc, current_agent.vm.ports.websocket
    except Exception:
        pass
    
    # Fallback to Agent 0 defaults
    ports = allocate_ports_for_agent(0)
    return ports.vnc, ports.websocket


@router.get("/vnc/status")
async def vnc_status():
    """Get VNC status by checking ports"""
    vnc_port, ws_port = _get_vnc_ports()
    vnc_ready = _check_port(vnc_port)
    ws_ready = _check_port(ws_port)
    
    return {
        "running": vnc_ready,
        "websockify_running": ws_ready,
        "port": vnc_port if vnc_ready else None,
        "ws_port": ws_port if ws_ready else None,
        "ready": vnc_ready and ws_ready
    }


@router.post("/vnc/start")
async def start_vnc():
    """
    Start VNC - in the current architecture, VNC runs inside the VM
    which is managed by Tauri. This endpoint just checks if VNC is ready.
    """
    vnc_port, ws_port = _get_vnc_ports()
    vnc_ready = _check_port(vnc_port)
    ws_ready = _check_port(ws_port)
    
    if vnc_ready and ws_ready:
        return {
            "status": "running",
            "message": "VNC and websockify are already running",
            "port": vnc_port,
            "ws_port": ws_port
        }
    elif vnc_ready:
        return {
            "status": "started",
            "message": "VNC is running, websockify may still be starting",
            "port": vnc_port,
            "ws_port": ws_port
        }
    else:
        return {
            "status": "waiting",
            "message": "VNC not yet available. VM may still be starting.",
            "port": vnc_port,
            "ws_port": ws_port
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
