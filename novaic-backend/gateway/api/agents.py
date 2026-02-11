"""
NovAIC Gateway（Backend 组件）- AIC Agent 管理 API.

提供 Agent 管理 REST 接口。
"""

import os
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import httpx

from gateway.config.agents import (
    get_agent_config_manager,
    AICAgent,
    VmConfig,
    PortConfig,
    AndroidConfig,
)
from gateway.db.access import get_db

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _prepare_android_config(
    android_request: "AndroidConfigRequest",
    agent_name: str,
) -> AndroidConfig:
    """
    Prepare Android configuration from request.
    
    - If managed=True: auto-generate avd_name if not provided
    - If managed=False: validate device_serial is provided
    
    Returns AndroidConfig ready to be stored.
    """
    import re
    
    if android_request.managed:
        # Managed mode: novaic will create/manage the AVD
        avd_name = android_request.avd_name
        if not avd_name:
            # Auto-generate AVD name from agent name
            # Sanitize: only alphanumeric and underscores
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', agent_name.lower())
            avd_name = f"novaic_{safe_name}"
        
        # Preserve device_serial if provided (e.g., after emulator starts)
        device_serial = android_request.device_serial or ""
        
        return AndroidConfig(
            device_serial=device_serial,
            managed=True,
            avd_name=avd_name,
        )
    else:
        # External mode: user provides existing device
        if not android_request.device_serial:
            raise ValueError(
                "device_serial is required when managed=False"
            )
        
        return AndroidConfig(
            device_serial=android_request.device_serial,
            managed=False,
            avd_name=None,
        )


def _get_tools_server_url() -> Optional[str]:
    """Tools Server URL when tools are served from separate process."""
    return os.environ.get("NOVAIC_TOOLS_SERVER_URL") or None


# ==================== Request/Response Models ====================

class AndroidConfigRequest(BaseModel):
    """Android emulator configuration request"""
    managed: bool = True  # Whether novaic manages the AVD lifecycle
    avd_name: Optional[str] = None  # AVD name (required if managed=True, auto-generated if not provided)
    device_serial: Optional[str] = None  # Device serial (required if managed=False)


class VmConfigRequest(BaseModel):
    """VM configuration request (for Linux VM)"""
    backend: str = "qemu"
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    source_image: Optional[str] = None


class CreateAgentRequest(BaseModel):
    """
    Request to create a new agent.
    
    Agent types:
    - 'chat': Pure chat agent (no VM/AVD, just LLM)
    - 'linux': Linux VM agent
    - 'android': Android AVD agent
    - 'hybrid': Both Linux VM and Android AVD
    
    For 'chat' type, vm_config and android are ignored.
    For 'linux' type, vm_config is required (or uses defaults).
    For 'android' type, android is required.
    For 'hybrid' type, both vm_config and android are required.
    """
    name: str
    model: Optional[str] = None  # LLM model (e.g., "kimi-k2.5", "gpt-4o")
    agent_type: str = "linux"  # 'chat' | 'linux' | 'android' | 'hybrid'
    # Linux VM config (optional, used for 'linux' and 'hybrid' types)
    vm_config: Optional[VmConfigRequest] = None
    # Android config (optional, used for 'android' and 'hybrid' types)
    android: Optional[AndroidConfigRequest] = None
    # Legacy fields for backward compatibility (deprecated, use vm_config instead)
    backend: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    memory: Optional[str] = None
    cpus: Optional[int] = None
    source_image: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    """
    Request to update an agent.
    
    Supports partial updates:
    - name: Update agent name
    - vm_config: Update VM configuration (for Linux VM)
    - android: Update Android configuration
    - setup_complete: Mark VM setup as complete
    
    Each field can be updated independently.
    """
    name: Optional[str] = None
    vm_config: Optional[VmConfigRequest] = None  # Update VM config
    android: Optional[AndroidConfigRequest] = None  # Update Android config
    setup_complete: Optional[bool] = None
    # Legacy field for backward compatibility
    vm: Optional[dict] = None


class AndroidConfigResponse(BaseModel):
    """Android emulator configuration response"""
    device_serial: str = ""
    managed: bool = False
    avd_name: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent response (public view)"""
    id: str
    name: str
    created_at: str
    vm: VmConfig
    setup_complete: bool = False
    model_id: Optional[str] = None  # Selected LLM model ID
    android: Optional[AndroidConfigResponse] = None  # Android emulator config


class SetAgentModelRequest(BaseModel):
    """Request to set agent's LLM model"""
    model_id: str


class CandidateModelResponse(BaseModel):
    """
    Candidate model response (unified model representation).
    
    Used for:
    - /models/available endpoint (list enabled models)
    - Agent model configuration
    """
    id: str
    name: str
    provider: str           # Provider type: openai, anthropic, google, etc.
    api_key_id: str         # API key ID this model belongs to
    api_key_name: str       # API key name for display
    enabled: bool = True    # Whether model is enabled for selection
    is_custom: bool = False # Custom model added by user


class AgentModelConfigResponse(BaseModel):
    """Agent's LLM model configuration"""
    agent_id: str
    model_id: Optional[str] = None
    model: Optional[CandidateModelResponse] = None
    # Full config for LLM calls (only in internal API)
    api_key: Optional[str] = None
    api_base: Optional[str] = None


class AgentListResponse(BaseModel):
    """List of agents response"""
    agents: List[AgentResponse]


class AvailableImageResponse(BaseModel):
    """Available VM image info"""
    path: str
    name: str
    size: int
    source: str


# ==================== Endpoints ====================

@router.get("", response_model=AgentListResponse)
def list_agents():
    """List all AIC agents"""
    manager = get_agent_config_manager()
    agents = manager.list_agents()
    
    response_agents = []
    for agent in agents:
        agent_dict = agent.model_dump()
        # Convert android config to response format
        if agent.vm.android:
            agent_dict['android'] = AndroidConfigResponse(
                device_serial=agent.vm.android.device_serial,
                managed=agent.vm.android.managed,
                avd_name=agent.vm.android.avd_name,
            )
        response_agents.append(AgentResponse(**agent_dict))
    
    return AgentListResponse(agents=response_agents)


@router.get("/images", response_model=List[AvailableImageResponse])
def list_available_images():
    """List available VM images"""
    manager = get_agent_config_manager()
    images = manager.get_available_images()
    return [AvailableImageResponse(**img) for img in images]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str):
    """Get agent by ID"""
    manager = get_agent_config_manager()
    agent = manager.get_agent(agent_id)
    
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_dict = agent.model_dump()
    # Convert android config to response format
    if agent.vm.android:
        agent_dict['android'] = AndroidConfigResponse(
            device_serial=agent.vm.android.device_serial,
            managed=agent.vm.android.managed,
            avd_name=agent.vm.android.avd_name,
        )
    
    return AgentResponse(**agent_dict)


@router.post("", response_model=AgentResponse)
def create_agent(request: CreateAgentRequest):
    """
    Create a new AIC agent.
    
    Supports different agent types:
    - 'chat': Pure chat agent (no VM/AVD)
    - 'linux': Linux VM agent
    - 'android': Android AVD agent  
    - 'hybrid': Both Linux VM and Android AVD
    """
    manager = get_agent_config_manager()
    
    try:
        agent_type = request.agent_type
        
        # Prepare Android config if needed
        android_config = None
        if agent_type in ("android", "hybrid") and request.android:
            android_config = _prepare_android_config(request.android, request.name)
        
        # Prepare VM config if needed
        # Support both new vm_config and legacy fields
        vm_params = {}
        if agent_type in ("linux", "hybrid"):
            if request.vm_config:
                vm_params = {
                    "backend": request.vm_config.backend,
                    "os_type": request.vm_config.os_type,
                    "os_version": request.vm_config.os_version,
                    "memory": request.vm_config.memory,
                    "cpus": request.vm_config.cpus,
                    "source_image": request.vm_config.source_image,
                }
            else:
                # Use legacy fields or defaults
                vm_params = {
                    "backend": request.backend or "qemu",
                    "os_type": request.os_type or "ubuntu",
                    "os_version": request.os_version or "24.04",
                    "memory": request.memory or "4096",
                    "cpus": request.cpus or 4,
                    "source_image": request.source_image,
                }
        
        # Create agent with appropriate configuration
        agent = manager.create_agent(
            name=request.name,
            agent_type=agent_type,
            android_config=android_config,
            **vm_params,
        )
        
        # Auto-create main SubAgent for the new agent
        from gateway.db.repositories import SubAgentRepository
        from gateway.db.access import get_database
        
        db = get_database()
        subagent_repo = SubAgentRepository(db)
        subagent_repo.get_or_create_main_subagent(agent.id)
        
        # Set model_id if provided
        if request.model:
            with db.transaction(lock_type="agent", resource_id=agent.id):
                db.execute(
                    "UPDATE agents SET model_id = ? WHERE id = ?",
                    (request.model, agent.id)
                )
        
        # v2.7: Tools contexts are created per-Runtime by Master, not per-Agent
        
        # Re-fetch agent to get model_id
        response_dict = agent.model_dump()
        if request.model:
            response_dict['model_id'] = request.model
        
        # Add android config to response
        if agent.vm.android:
            response_dict['android'] = AndroidConfigResponse(
                device_serial=agent.vm.android.device_serial,
                managed=agent.vm.android.managed,
                avd_name=agent.vm.android.avd_name,
            )
        
        return AgentResponse(**response_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, request: UpdateAgentRequest):
    """
    Update an existing agent.
    
    Supports partial updates:
    - name: Update agent name
    - vm_config: Add or update Linux VM configuration
    - android: Add or update Android configuration
    - setup_complete: Mark VM setup as complete
    """
    manager = get_agent_config_manager()
    
    # Get old agent to check setup_complete change
    old_agent = manager.get_agent(agent_id)
    if old_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    was_setup_complete = old_agent.setup_complete
    
    # Build update data
    update_kwargs = {}
    
    if request.name is not None:
        update_kwargs["name"] = request.name
    
    if request.setup_complete is not None:
        update_kwargs["setup_complete"] = request.setup_complete
    
    # Handle VM config update (new format)
    if request.vm_config is not None:
        vm_config_dict = request.vm_config.model_dump(exclude_none=True)
        update_kwargs["vm_config"] = vm_config_dict
    # Handle legacy vm field
    elif request.vm is not None:
        update_kwargs["vm_config"] = request.vm
    
    # Handle Android config update
    if request.android is not None:
        android_config = _prepare_android_config(request.android, old_agent.name)
        update_kwargs["android_config"] = android_config
    
    agent = manager.update_agent(agent_id, **update_kwargs)
    
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # If setup_complete changed to True, send bootstrap message
    # v2.7: Tools context is created per-Runtime by Master, not here
    if request.setup_complete is True and not was_setup_complete:
        # Send bootstrap message using v12 Master-driven architecture
        try:
            from gateway.db.repositories.message import MessageRepository
            
            db = get_db()
            msg_repo = MessageRepository(db)
            
            # Store message - Monitor will detect and create Runtime
            msg = msg_repo.add_message(
                agent_id=agent_id,
                type="SYSTEM_MESSAGE",
                content="VM setup complete. Execute skill agent-bootstrap to configure the agent environment.",
                metadata={
                    "action": "bootstrap",
                    "skill": "agent-bootstrap",
                    "reason": "setup_complete",
                    "priority": "high",
                    "source": "system:bootstrap",
                },
            )
            
            # v12: No broadcast_new_message needed
            # Monitor polls for unread messages and creates Runtimes
            
            print(f"[Agents] Bootstrap message stored for agent {agent_id}, Monitor will process")
        except Exception as e:
            print(f"[Agents] Warning: Failed to store bootstrap message: {e}")
    
    # Build response
    response_dict = agent.model_dump()
    if agent.vm.android:
        response_dict['android'] = AndroidConfigResponse(
            device_serial=agent.vm.android.device_serial,
            managed=agent.vm.android.managed,
            avd_name=agent.vm.android.avd_name,
        )
    
    return AgentResponse(**response_dict)


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """Delete an agent and its VM files"""
    manager = get_agent_config_manager()
    
    # v2.7: Aggregate Gateways are cleaned up when Runtimes are destroyed
    # No need to remove per-agent gateway here
    
    if not manager.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "ok", "message": "Agent deleted"}


# ==================== VM Control (delegated to Tauri) ====================
# Note: VM start/stop is handled by Tauri, not Gateway.
# These endpoints are placeholders for status queries.

@router.get("/{agent_id}/status")
def get_agent_status(agent_id: str):
    """
    Get agent setup status.
    
    Note: Actual VM status should come from Tauri via IPC.
    """
    manager = get_agent_config_manager()
    agent = manager.get_agent(agent_id)
    
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "setup_complete": agent.setup_complete,
        "ports": agent.vm.ports.model_dump()
    }


# ==================== MCP Management (v2.7) ====================
# Deprecated: Legacy MCP proxy endpoints.

@router.get("/mcp/status")
def get_mcp_status():
    """Get MCP status.
    
    NOTE: Legacy MCP Gateway has been deprecated.
    Tools are now served via Tools Server (HTTP API).
    """
    return {
        "status": "deprecated",
        "message": "Legacy MCP Gateway has been replaced by Tools Server",
        "tools_server_url": os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL),
    }


@router.get("/mcp/runtimes")
def list_mcp_runtimes():
    """List MCP runtimes.
    
    NOTE: Legacy MCP Gateway has been deprecated.
    Use Tools Server APIs instead.
    """
    return {
        "status": "deprecated",
        "message": "Legacy MCP Gateway has been replaced by Tools Server",
        "runtimes": [],
        "total": 0,
        "tools_server_url": os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL),
    }


# Note: Workers load tools from Aggregate Gateway URL stored in runtime record.
# Tool discovery is done via MCP protocol (tools/list).


# ==================== Model Selection (v20) ====================

@router.get("/models/available", response_model=List[CandidateModelResponse])
def list_available_models():
    """
    List all available (enabled) models for selection.
    
    Returns CandidateModel entries that are:
    1. In candidate_models table with enabled=true
    2. Have valid api_key configured
    
    This is the unified API for getting models that can be used.
    """
    from gateway.config import get_config_manager
    
    # Use repository method that joins with api_keys
    config_manager = get_config_manager()
    models_data = config_manager.repo.list_models_with_key_name(enabled_only=True)
    
    return [
        CandidateModelResponse(
            id=row["id"],
            name=row["name"],
            provider=row["provider"],
            api_key_id=row["api_key_id"],
            api_key_name=row.get("api_key_name", ""),
            enabled=True,  # Only enabled models are returned
            is_custom=bool(row.get("is_custom", 0)),
        )
        for row in models_data
    ]


@router.get("/{agent_id}/model", response_model=AgentModelConfigResponse)
def get_agent_model(agent_id: str):
    """
    Get agent's selected LLM model and configuration.
    
    Returns:
    - model_id: The selected model ID (null if not set, uses default)
    - model: Full model info including provider
    - api_key/api_base: Included for internal use (LLM calls)
    """
    from gateway.config import get_config_manager
    
    db = get_db()
    manager = get_agent_config_manager()
    
    agent = manager.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get agent's model_id from database
    cursor = db.execute(
        "SELECT model_id FROM agents WHERE id = ?",
        (agent_id,)
    )
    row = cursor.fetchone()
    model_id = row["model_id"] if row and row["model_id"] else None
    
    # If no model selected, use default from config
    if not model_id:
        config = get_config_manager().load()
        model_id = config.default_model
    
    # Get model and provider info (DB field is 'available', maps to 'enabled')
    cursor = db.execute("""
        SELECT 
            m.id as model_id,
            m.name as model_name,
            m.provider,
            m.api_key_id,
            m.available,
            m.is_custom,
            k.name as api_key_name,
            k.api_key,
            k.api_base
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.id = ?
        LIMIT 1
    """, (model_id,))
    row = cursor.fetchone()
    
    if not row:
        return AgentModelConfigResponse(
            agent_id=agent_id,
            model_id=model_id,
            model=None,
        )
    
    # Determine effective api_base
    api_base = row["api_base"]
    if not api_base:
        # Use default base URL for provider
        provider_defaults = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            "google": "https://generativelanguage.googleapis.com/v1beta",
        }
        api_base = provider_defaults.get(row["provider"], "")
    
    return AgentModelConfigResponse(
        agent_id=agent_id,
        model_id=model_id,
        model=CandidateModelResponse(
            id=row["model_id"],
            name=row["model_name"],
            provider=row["provider"],
            api_key_id=row["api_key_id"],
            api_key_name=row["api_key_name"],
            enabled=bool(row["available"]),
            is_custom=bool(row["is_custom"]),
        ),
        api_key=row["api_key"],
        api_base=api_base,
    )


@router.put("/{agent_id}/model")
def set_agent_model(agent_id: str, request: SetAgentModelRequest):
    """
    Set agent's LLM model.
    
    The model must be in candidate_models and available.
    """
    db = get_db()
    manager = get_agent_config_manager()
    
    agent = manager.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Verify model exists and is enabled
    cursor = db.execute("""
        SELECT m.id, m.name, k.name as provider_name
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.id = ? AND m.available = 1
        LIMIT 1
    """, (request.model_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{request.model_id}' not found or not enabled"
        )
    
    # Update agent's model_id
    with db.transaction(lock_type="agent", resource_id=agent_id):
        db.execute(
            "UPDATE agents SET model_id = ? WHERE id = ?",
            (request.model_id, agent_id)
        )
    
    return {
        "success": True,
        "agent_id": agent_id,
        "model_id": request.model_id,
        "provider_name": row["provider_name"],
    }
