"""
NovAIC Gateway - REST API Routes

v12: Master-driven architecture
- Chat messages go to inbox, not directly to Agent
- Master detects new messages and creates Runtimes
- Workers execute tasks (think, tool_call, reply)
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
    ApiKeyCreate, ApiKeyUpdate, ModelToggle, CustomModelAdd, SettingsUpdate,
    HealthResponse, HistoryResponse
)
from gateway.config import get_config_manager, ProviderType
from gateway.db.access import get_db

router = APIRouter()

# v12: Removed global _agent instance - Master-driven architecture doesn't need it


# ==================== Health ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - v2.7: simplified for per-Runtime architecture"""
    # Check vmcontrol service health
    vmcontrol_healthy = False
    try:
        from gateway.clients.vmcontrol import get_vmcontrol_client
        client = get_vmcontrol_client()
        vmcontrol_healthy = await client.health_check()
    except Exception as e:
        print(f"[Health] vmcontrol check failed: {e}")
    
    # 简化health check，避免DB访问导致的锁竞争
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        agent_initialized=True,  # 简化：不查询DB
        mcp_healthy=False,
        tools_count=0,
        vmcontrol_healthy=vmcontrol_healthy
    )


# ==================== Config ====================

@router.get("/config")
def get_config():
    """Get current configuration (public version, hides API keys)"""
    config = get_config_manager().load()
    return config.to_public()


@router.get("/config/internal")
def get_config_internal():
    """
    Get full configuration including API keys.
    
    Internal API for Worker processes - includes sensitive data.
    Should only be called by Workers on localhost.
    """
    config = get_config_manager().load()
    
    # Return full config with API keys for Workers
    return {
        "version": config.version,
        "api_keys": [
            {
                "id": k.id,
                "name": k.name,
                "provider": k.provider.value,
                "api_key": k.api_key,  # Include actual key
                "api_base": k.get_effective_base_url(),
                "deployment_name": k.deployment_name,
                "api_version": k.api_version,
            }
            for k in config.api_keys
        ],
        "candidate_models": [m.model_dump() for m in config.candidate_models],
        "default_model": config.default_model,
        "max_tokens": config.max_tokens,
        "max_iterations": config.max_iterations,
    }


@router.patch("/config/settings")
def update_settings(settings: SettingsUpdate):
    """Update common settings - v12: Master-driven architecture"""
    get_config_manager().update_settings(
        default_model=settings.default_model,
        max_tokens=settings.max_tokens,
        max_iterations=settings.max_iterations,
        visible_shell=settings.visible_shell,
    )
    
    # v12: Settings are read from config when Workers execute tasks
    # No need to update a global agent instance
    
    return {"status": "ok"}


# ==================== API Keys ====================

@router.post("/config/api-keys")
def add_api_key(data: ApiKeyCreate):
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
def update_api_key(key_id: str, data: ApiKeyUpdate):
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
def delete_api_key(key_id: str):
    """Delete an API key"""
    if not get_config_manager().delete_api_key(key_id):
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    return {"status": "ok"}


# ==================== Models ====================

@router.post("/config/models/toggle")
def toggle_model(data: ModelToggle):
    """Toggle model enabled state"""
    if not get_config_manager().toggle_model(data.model_id, data.api_key_id, data.enabled):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "ok"}


@router.delete("/config/models/{api_key_id}/{model_id}")
def delete_model(api_key_id: str, model_id: str):
    """Delete a model"""
    if not get_config_manager().delete_model(model_id, api_key_id):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "ok"}


@router.post("/config/api-keys/{key_id}/models")
def save_models_for_key(key_id: str, models: List[dict]):
    """Save/merge models for an API key (keeps existing custom models)"""
    get_config_manager().save_models_for_key(key_id, models)
    return {"status": "ok"}


@router.post("/config/api-keys/{key_id}/models/add")
def add_model(key_id: str, data: CustomModelAdd):
    """Add a single custom model"""
    # Get API key to determine provider
    config = get_config_manager().load()
    api_key = config.get_api_key_by_id(key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")
    
    model_name = data.name if data.name else data.id
    
    try:
        # Call add_model with correct parameter order:
        # model_id, name, provider, api_key_id, enabled=True, is_custom=True
        get_config_manager().add_model(
            model_id=data.id,
            name=model_name,
            provider=api_key.provider,
            api_key_id=key_id,
            enabled=True,
            is_custom=True
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/config/api-keys/{key_id}/test")
def test_api_key(key_id: str):
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
        with httpx.Client(timeout=10.0) as client:
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
                response = client.post(url, headers=headers, json={
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
            
            response = client.get(url, headers=headers)
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
def fetch_models_for_key(key_id: str):
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
        with httpx.Client(timeout=30.0) as client:
            if entry.provider.value in ["openai", "azure", "openai_compatible"]:
                url = f"{base_url}/models"
                headers = {"Authorization": f"Bearer {entry.api_key}"}
                print(f"[API] Fetching models from {url}")
                response = client.get(url, headers=headers)
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
def set_default_model(data: dict):
    """Set the default model"""
    model_id = data.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
    
    get_config_manager().set_default_model(model_id)
    return {"status": "ok"}


@router.post("/config/cleanup")
def cleanup_garbage(
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
                db = get_db()
                if db:
                    db.vacuum()
                    cleaned["database_vacuumed"] = True
            except Exception as e:
                print(f"[Cleanup] Database vacuum failed: {e}")

        # 5. Clean orphaned agent directories (if deep=True)
        if deep:
            try:
                from gateway.config.agents import get_agent_config_manager
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


# ==================== Chat (v12: Master-driven via inbox) ====================

@router.post("/chat")
def chat(request: ChatRequest):
    """
    Send a message to the Agent's inbox.
    
    v12: Uses Master-driven architecture.
    - Message is stored in inbox (chat_messages table)
    - Monitor detects unread messages
    - Master creates Runtime and drives ReACT loop
    - Agent replies via SSE events (subscribe to /api/chat/events)
    
    Returns:
    - success: Whether the message was stored
    - message_id: ID of the stored message
    - timestamp: When the message was stored
    """
    from gateway.db.repositories.message import MessageRepository
    from gateway.config.agents import get_agent_config_manager
    
    # agent_id is required
    if not request.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    # Validate agent exists
    agent_mgr = get_agent_config_manager()
    agent = agent_mgr.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")
    agent_id = request.agent_id
    
    content = request.message.strip()
    
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")
    
    # Build metadata
    config = get_config_manager().load()
    metadata = {}
    
    # Resolve API configuration for LLM calls
    provider, api_base, api_key = resolve_api_config(config, request)
    model = request.model or config.default_model
    
    if model:
        metadata["model"] = model
    if provider:
        metadata["provider"] = provider
    if api_base:
        metadata["api_base"] = api_base
    if api_key:
        metadata["api_key"] = api_key  # Note: Consider security implications
    if request.api_key_id:
        metadata["api_key_id"] = request.api_key_id
    
    # Store message in inbox (status=sending for Monitor queue)
    db = get_db()
    message_repo = MessageRepository(db)
    
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="USER_MESSAGE",
        content=content,
        metadata=metadata if metadata else None,
        status="sending",  # v18: Monitor will consume and change to 'sent'
    )
    
    # Broadcast to UI SSE (for display)
    try:
        from main import broadcast_chat_message
        broadcast_chat_message({
            "id": msg["id"],
            "type": "USER_MESSAGE",
            "timestamp": msg["timestamp"],
            "content": content,
        }, agent_id=agent_id)
    except Exception as e:
        print(f"[Chat] Warning: Failed to broadcast to UI: {e}")
    
    # Monitor will consume sending message, wake SubAgent, and create Runtime
    # Agent replies will come via SSE /api/chat/events
    
    return {
        "success": True,
        "message_id": msg["id"],
        "timestamp": msg["timestamp"],
        "status": "sending",  # v18: waiting for Monitor to process
        "note": "Subscribe to /api/chat/events for agent responses",
    }


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Send a message and stream responses via SSE.
    
    v12: Uses Master-driven architecture.
    - Message is stored in inbox
    - Returns SSE stream that includes agent responses
    
    Note: This endpoint stores the message and then subscribes to events.
    For better control, use POST /chat + GET /api/chat/events separately.
    """
    from gateway.db.repositories.message import MessageRepository
    from gateway.config.agents import get_agent_config_manager
    import asyncio
    
    # agent_id is required
    if not request.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    # Validate agent exists
    agent_mgr = get_agent_config_manager()
    agent = agent_mgr.get_agent(request.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")
    agent_id = request.agent_id
    
    content = request.message.strip()
    
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")
    
    # Build metadata
    config = get_config_manager().load()
    metadata = {}
    
    provider, api_base, api_key = resolve_api_config(config, request)
    model = request.model or config.default_model
    
    if model:
        metadata["model"] = model
    if provider:
        metadata["provider"] = provider
    if api_base:
        metadata["api_base"] = api_base
    if api_key:
        metadata["api_key"] = api_key
    if request.api_key_id:
        metadata["api_key_id"] = request.api_key_id
    
    # Store message in inbox (status=sending for Monitor queue)
    db = get_db()
    message_repo = MessageRepository(db)
    
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="USER_MESSAGE",
        content=content,
        metadata=metadata if metadata else None,
        status="sending",  # v18: Monitor will consume and change to 'sent'
    )
    
    user_message_id = msg["id"]
    
    def event_generator():
        # First, emit the stored message confirmation
        yield f"data: {json.dumps({'type': 'message_stored', 'data': {'message_id': user_message_id}, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        
        # Broadcast to UI
        try:
            from main import broadcast_chat_message
            broadcast_chat_message({
                "id": user_message_id,
                "type": "USER_MESSAGE",
                "timestamp": msg["timestamp"],
                "content": content,
            }, agent_id=agent_id)
        except Exception:
            pass
        
        # Subscribe to chat events for this agent
        # Use the main.py chat SSE mechanism
        try:
            from main import _chat_subscribers
            queue = asyncio.Queue(maxsize=100)
            subscriber_id = f"chat_stream_{user_message_id}"
            _chat_subscribers[subscriber_id] = queue
            
            try:
                # Wait for events with timeout
                timeout = 300  # 5 minutes max
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        yield f"data: {json.dumps({'type': 'timeout', 'data': {'message': 'Stream timeout'}, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                        break
                    
                    try:
                        event = asyncio.wait_for(queue.get(), timeout=30)
                        
                        # Filter events for this agent
                        if event.get("agent_id") == agent_id:
                            event["timestamp"] = datetime.utcnow().isoformat()
                            yield f"data: {json.dumps(event)}\n\n"
                            
                            # Check for completion signals
                            if event.get("type") in ("AGENT_DONE", "runtime_completed", "error"):
                                break
                    
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield f": keepalive\n\n"
                        
            finally:
                _chat_subscribers.pop(subscriber_id, None)
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
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


# ==================== History (v12: Use chat_messages table) ====================

@router.get("/history", response_model=HistoryResponse)
def get_history(agent_id: str = Query(..., description="Agent ID (required)")):
    """
    Get chat history.
    
    v12: Uses chat_messages table instead of NovAICAgent session.
    """
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    db = get_db()
    rows = db.fetchall(
        """
        SELECT id, type, content, timestamp, read 
        FROM chat_messages 
        WHERE agent_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 100
        """,
        (agent_id,)
    )
    
    messages = []
    for row in rows:
        messages.append({
            "id": row["id"],
            "type": row["type"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "read": bool(row["read"]),
        })
    
    return HistoryResponse(messages=list(reversed(messages)))


@router.post("/clear")
def clear_history(agent_id: str = Query(..., description="Agent ID (required)")):
    """
    Clear chat history.
    
    v12: Marks all messages as read instead of deleting.
    """
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    db = get_db()
    with db.transaction(lock_type="agent", resource_id=agent_id, timeout=10.0):
        db.execute(
            "UPDATE chat_messages SET read = 1 WHERE agent_id = ?",
            (agent_id,)
        )
    
    return {"status": "ok", "message": "History cleared (messages marked as read)"}


# ==================== Control (v12: Master-driven) ====================

@router.post("/interrupt")
def interrupt(agent_id: str = Query(..., description="Agent ID (required)")):
    """
    Interrupt current execution.
    
    v4.1: Gateway 不再直接调用 Queue Service。
    - Gateway 立即更新自己的数据库（runtimes, subagents）
    - 写入 INTERRUPT 消息，由 Watchdog 调用 QS cancel API
    
    这样用户得到立即响应，QS 的取消是异步处理。
    """
    from datetime import datetime
    from gateway.db.repositories.message import MessageRepository
    import uuid
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    db = get_db()
    now = datetime.utcnow().isoformat()
    
    interrupted_runtimes = 0
    
    # 1. 立即更新 Gateway 自己的数据库
    with db.transaction(lock_type="global", timeout=15.0):
        # Mark active runtimes as interrupted
        cursor = db.execute("""
            UPDATE agent_runtimes 
            SET status = 'completed', phase = 'completed', updated_at = ?
            WHERE status = 'active'
        """, (now,))
        interrupted_runtimes = cursor.rowcount
        
        # Set SubAgents to sleeping
        db.execute("""
            UPDATE subagents 
            SET status = 'sleeping', updated_at = ?
            WHERE status IN ('awake', 'awaking')
        """, (now,))
    
    # 2. 写入 INTERRUPT 消息，Watchdog 会调用 QS cancel API
    # v2.1: Gateway 不再直接调用 Queue Service
    message_repo = MessageRepository(db)
    
    msg = message_repo.add_message(
        agent_id=agent_id,
        type="INTERRUPT",
        content="User requested interrupt",
        status="sending",  # Watchdog 监测 sending 状态
        metadata={
            "action": "cancel_all",
            "target_agent_id": agent_id,
            "interrupted_runtimes": interrupted_runtimes,
        }
    )
    
    print(f"[Gateway] Created INTERRUPT message {msg['id']}, Watchdog will cancel tasks/sagas")
    
    return {
        "status": "ok",
        "message_id": msg["id"],
        "interrupted_runtimes": interrupted_runtimes,
        "note": "Tasks/sagas cancellation is async via Watchdog",
    }


@router.post("/init")
def init_agent():
    """
    Initialize the agent (for backward compatibility).
    
    v12: Not needed - Master handles initialization.
    """
    return {"status": "ok", "message": "v12: Agent initialization handled by Master"}


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



@router.get("/vnc/status")
def vnc_status():
    """Get VNC status - check vmcontrol service health"""
    try:
        from gateway.clients.vmcontrol import get_vmcontrol_client
        import asyncio
        client = get_vmcontrol_client()
        # Check if vmcontrol service is healthy
        healthy = asyncio.run(client.health_check())
        return {
            "running": healthy,
            "ready": healthy,
            "note": "VNC is provided via vmcontrol WebSocket (ws://localhost:8080/api/vms/{agent_id}/vnc)"
        }
    except Exception as e:
        return {
            "running": False,
            "ready": False,
            "error": str(e)
        }


@router.post("/vnc/start")
def start_vnc():
    """
    Start VNC - in the new architecture, VNC is provided via QEMU native VNC
    and exposed through vmcontrol WebSocket proxy.
    """
    try:
        from gateway.clients.vmcontrol import get_vmcontrol_client
        import asyncio
        client = get_vmcontrol_client()
        healthy = asyncio.run(client.health_check())
        
        if healthy:
            return {
                "status": "running",
                "message": "VNC is available via vmcontrol WebSocket",
                "note": "Connect to ws://localhost:8080/api/vms/{agent_id}/vnc"
            }
        else:
            return {
                "status": "waiting",
                "message": "vmcontrol service not ready. VM may still be starting."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check VNC status: {str(e)}"
        }


@router.post("/vnc/stop")
def stop_vnc():
    """
    Stop VNC - in the current architecture, VNC is managed by the VM.
    This is a no-op but provided for API compatibility.
    """
    return {
        "status": "ok",
        "message": "VNC is managed by the VM. Use VM controls to stop."
    }
