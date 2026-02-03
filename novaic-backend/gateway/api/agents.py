"""
NovAIC Gateway（Backend 组件）- AIC Agent 管理 API.

提供 Agent 管理 REST 接口。
MCP 状态/运行时由另一 Backend 组件 MCP Gateway 提供；本进程通过代理转发。
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
)
from mcp_gateway.manager import get_mcp_manager
from gateway.db.access import get_db

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _get_mcp_gateway_url() -> Optional[str]:
    """MCP Gateway URL when MCP runs in separate process."""
    return os.environ.get("NOVAIC_MCP_GATEWAY_URL") or None


# ==================== Request/Response Models ====================

class CreateAgentRequest(BaseModel):
    """Request to create a new agent"""
    name: str
    backend: str = "qemu"
    os_type: str = "ubuntu"
    os_version: str = "24.04"
    memory: str = "4096"
    cpus: int = 4
    source_image: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    """Request to update an agent"""
    name: Optional[str] = None
    vm: Optional[dict] = None
    setup_complete: Optional[bool] = None


class AgentResponse(BaseModel):
    """Agent response (public view)"""
    id: str
    name: str
    created_at: str
    vm: VmConfig
    setup_complete: bool = False
    model_id: Optional[str] = None  # Selected LLM model ID


class SetAgentModelRequest(BaseModel):
    """Request to set agent's LLM model"""
    model_id: str


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    name: str
    provider_id: str
    provider_name: str
    provider_type: str  # openai, anthropic, google
    enabled: bool = True
    is_custom: bool = False
    # Alias for clarity: "available" means enabled
    available: bool = True


class AgentModelConfigResponse(BaseModel):
    """Agent's LLM model configuration"""
    agent_id: str
    model_id: Optional[str] = None
    model: Optional[ModelInfo] = None
    # Full config for LLM calls (only in internal API)
    api_key: Optional[str] = None
    api_base: Optional[str] = None


class AgentListResponse(BaseModel):
    """List of agents response"""
    agents: List[AgentResponse]
    current_agent_id: Optional[str] = None


class SetCurrentAgentRequest(BaseModel):
    """Request to set current agent"""
    agent_id: str


class AvailableImageResponse(BaseModel):
    """Available VM image info"""
    path: str
    name: str
    size: int
    source: str


# ==================== Endpoints ====================

@router.get("", response_model=AgentListResponse)
async def list_agents():
    """List all AIC agents"""
    manager = get_agent_config_manager()
    agents = manager.list_agents()
    current_agent = manager.get_current_agent()
    
    return AgentListResponse(
        agents=[AgentResponse(**agent.model_dump()) for agent in agents],
        current_agent_id=current_agent.id if current_agent else None
    )


@router.get("/current", response_model=Optional[AgentResponse])
async def get_current_agent():
    """Get the currently selected agent"""
    manager = get_agent_config_manager()
    agent = manager.get_current_agent()
    
    if agent is None:
        return None
    
    return AgentResponse(**agent.model_dump())


@router.post("/current")
async def set_current_agent(request: SetCurrentAgentRequest):
    """Set the current agent"""
    manager = get_agent_config_manager()
    
    if not manager.set_current_agent(request.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"status": "ok", "current_agent_id": request.agent_id}


@router.get("/images", response_model=List[AvailableImageResponse])
async def list_available_images():
    """List available VM images"""
    manager = get_agent_config_manager()
    images = manager.get_available_images()
    return [AvailableImageResponse(**img) for img in images]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    manager = get_agent_config_manager()
    agent = manager.get_agent(agent_id)
    
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(**agent.model_dump())


@router.post("", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest):
    """Create a new AIC agent"""
    manager = get_agent_config_manager()
    
    try:
        agent = manager.create_agent(
            name=request.name,
            backend=request.backend,
            os_type=request.os_type,
            os_version=request.os_version,
            memory=request.memory,
            cpus=request.cpus,
            source_image=request.source_image,
        )
        
        # v2.7: MCP Gateways are created per-Runtime by Master, not per-Agent
        
        return AgentResponse(**agent.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: UpdateAgentRequest):
    """Update an existing agent"""
    manager = get_agent_config_manager()
    
    # Get old agent to check setup_complete change
    old_agent = manager.get_agent(agent_id)
    was_setup_complete = old_agent.setup_complete if old_agent else False
    
    update_data = request.model_dump(exclude_none=True)
    agent = manager.update_agent(agent_id, **update_data)
    
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # If setup_complete changed to True, send bootstrap message
    # v2.7: MCP Gateway is created per-Runtime by Master, not here
    if request.setup_complete is True and not was_setup_complete:
        # Send bootstrap message using v12 Master-driven architecture
        try:
            from gateway.db.repositories.message import MessageRepository
            
            db = get_db()
            msg_repo = MessageRepository(db)
            
            # Store message - Monitor will detect and create Runtime
            msg = await msg_repo.add_message(
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
    
    return AgentResponse(**agent.model_dump())


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
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
async def get_agent_status(agent_id: str):
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
# When MCP runs in separate process, proxy to MCP Gateway.

@router.get("/mcp/status")
async def get_mcp_status():
    """
    Get MCPManager status.
    Proxies to MCP Gateway when MCP runs in separate process.
    """
    mcp_manager = get_mcp_manager()
    if mcp_manager:
        return {"stats": mcp_manager.get_stats()}
    mcp_url = _get_mcp_gateway_url()
    if not mcp_url:
        raise HTTPException(status_code=503, detail="MCP not available (no MCP Gateway URL)")
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            r = await client.get(f"{mcp_url.rstrip('/')}/internal/mcp/stats")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MCP Gateway unreachable: {e}")


@router.get("/mcp/runtimes")
async def list_mcp_runtimes():
    """
    List all active Runtime MCP servers and their Aggregate Gateways.
    Proxies to MCP Gateway when MCP runs in separate process.
    """
    mcp_manager = get_mcp_manager()
    if mcp_manager:
        stats = mcp_manager.get_stats()
        runtimes = []
        for subagent_id in stats.get("runtime_servers", []):
            runtime_url = mcp_manager.get_runtime_mount_path(subagent_id)
            aggregate_url = mcp_manager.get_aggregate_mount_path(subagent_id)
            gateway = mcp_manager.get_aggregate_gateway(subagent_id)
            runtimes.append({
                "subagent_id": subagent_id,
                "runtime_url": runtime_url,
                "aggregate_url": aggregate_url,
                "gateway_stats": gateway.get_stats() if gateway else None,
            })
        return {"runtimes": runtimes, "total": len(runtimes)}
    mcp_url = _get_mcp_gateway_url()
    if not mcp_url:
        raise HTTPException(status_code=503, detail="MCP not available (no MCP Gateway URL)")
    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            r = await client.get(f"{mcp_url.rstrip('/')}/internal/mcp/runtimes")
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MCP Gateway unreachable: {e}")


# Note: Workers load tools from Aggregate Gateway URL stored in runtime record.
# Tool discovery is done via MCP protocol (tools/list).


# ==================== Model Selection (v20) ====================

@router.get("/models/available", response_model=List[ModelInfo])
async def list_available_models():
    """
    List all available models for selection.
    
    Returns models that are:
    1. In candidate_models table
    2. Marked available
    3. Have valid api_key configured
    """
    db = get_db()
    
    # Join candidate_models with api_keys to get full info
    cursor = await db.execute("""
        SELECT 
            m.id as model_id,
            m.name as model_name,
            m.available,
            m.is_custom,
            k.id as provider_id,
            k.name as provider_name,
            k.provider as provider_type,
            k.api_key
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.available = 1 AND k.api_key IS NOT NULL AND k.api_key != ''
        ORDER BY k.name, m.name
    """)
    rows = await cursor.fetchall()
    
    return [
        ModelInfo(
            id=row["model_id"],
            name=row["model_name"],
            provider_id=row["provider_id"],
            provider_name=row["provider_name"],
            provider_type=row["provider_type"],
            enabled=bool(row["available"]),
            is_custom=bool(row["is_custom"]),
            available=bool(row["available"]),
        )
        for row in rows
    ]


@router.get("/{agent_id}/model", response_model=AgentModelConfigResponse)
async def get_agent_model(agent_id: str):
    """
    Get agent's selected LLM model and configuration.
    
    Returns:
    - model_id: The selected model ID (null if not set, uses default)
    - model: Full model info including provider
    - api_key/api_base: Included for internal use (LLM calls)
    """
    from gateway.config import get_config_manager_db
    
    db = get_db()
    manager = get_agent_config_manager()
    
    agent = manager.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get agent's model_id from database
    cursor = await db.execute(
        "SELECT model_id FROM agents WHERE id = ?",
        (agent_id,)
    )
    row = await cursor.fetchone()
    model_id = row["model_id"] if row and row["model_id"] else None
    
    # If no model selected, use default from config
    if not model_id:
        config = await get_config_manager_db().load()
        model_id = config.default_model
    
    # Get model and provider info
    cursor = await db.execute("""
        SELECT 
            m.id as model_id,
            m.name as model_name,
            m.enabled,
            m.is_custom,
            k.id as provider_id,
            k.name as provider_name,
            k.provider as provider_type,
            k.api_key,
            k.api_base
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.name = ?
        LIMIT 1
    """, (model_id,))
    row = await cursor.fetchone()
    
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
        api_base = provider_defaults.get(row["provider_type"], "")
    
    return AgentModelConfigResponse(
        agent_id=agent_id,
        model_id=model_id,
        model=ModelInfo(
            id=row["model_id"],
            name=row["model_name"],
            provider_id=row["provider_id"],
            provider_name=row["provider_name"],
            provider_type=row["provider_type"],
            enabled=bool(row["available"]),
            is_custom=bool(row["is_custom"]),
            available=bool(row["available"]),
        ),
        api_key=row["api_key"],
        api_base=api_base,
    )


@router.put("/{agent_id}/model")
async def set_agent_model(agent_id: str, request: SetAgentModelRequest):
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
    cursor = await db.execute("""
        SELECT m.id, m.name, k.name as provider_name
        FROM candidate_models m
        JOIN api_keys k ON m.api_key_id = k.id
        WHERE m.name = ? AND m.available = 1
        LIMIT 1
    """, (request.model_id,))
    row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{request.model_id}' not found or not enabled"
        )
    
    # Update agent's model_id
    await db.execute(
        "UPDATE agents SET model_id = ? WHERE id = ?",
        (request.model_id, agent_id)
    )
    await db.commit()
    
    return {
        "success": True,
        "agent_id": agent_id,
        "model_id": request.model_id,
        "provider_name": row["provider_name"],
    }
