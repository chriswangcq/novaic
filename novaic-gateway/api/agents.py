"""
NovAIC Gateway - AIC Agent Management API

Provides REST endpoints for managing AIC agents.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from config.agents import (
    get_agent_config_manager,
    AICAgent,
    VmConfig,
    PortConfig,
)
from mcp_gateway.manager import get_mcp_gateway_manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


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
        
        # Setup MCP Gateway for the new agent
        mcp_manager = get_mcp_gateway_manager()
        if mcp_manager:
            await mcp_manager.add_agent(
                agent_id=agent.id,
                agent_index=agent.vm.agent_index,
            )
        
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
    
    # If setup_complete changed to True, ensure MCP Gateway is setup and send bootstrap message
    if request.setup_complete is True and not was_setup_complete:
        # Setup MCP Gateway
        mcp_manager = get_mcp_gateway_manager()
        if mcp_manager and not mcp_manager.get_gateway(agent_id):
            await mcp_manager.add_agent(
                agent_id=agent.id,
                agent_index=agent.vm.agent_index,
            )
        
        # Send bootstrap message to Agent's inbox
        try:
            from api.inbox_service import get_inbox_service
            
            inbox_svc = get_inbox_service()
            await inbox_svc.add_message(
                msg_type="SYSTEM_MESSAGE",
                content="VM setup complete. Execute skill agent-bootstrap to configure the agent environment.",
                priority="high",
                source="system:bootstrap",
                metadata={
                    "action": "bootstrap",
                    "skill": "agent-bootstrap",
                    "reason": "setup_complete",
                },
                agent_id=agent_id,
            )
            print(f"[Agents] Sent bootstrap message to agent {agent_id}")
        except Exception as e:
            print(f"[Agents] Warning: Failed to send bootstrap message: {e}")
    
    return AgentResponse(**agent.model_dump())


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent and its VM files"""
    manager = get_agent_config_manager()
    
    # Remove MCP Gateway first
    mcp_manager = get_mcp_gateway_manager()
    if mcp_manager:
        await mcp_manager.remove_agent(agent_id)
    
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


# ==================== MCP Gateway Management ====================

@router.get("/{agent_id}/mcp/status")
async def get_agent_mcp_status(agent_id: str):
    """
    Get agent MCP Gateway status.
    
    Returns gateway stats including tool count, skill count, and mount path.
    """
    mcp_manager = get_mcp_gateway_manager()
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Gateway Manager not available")
    
    gateway = mcp_manager.get_gateway(agent_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="MCP Gateway not found for this agent")
    
    return {
        "agent_id": agent_id,
        "mount_path": mcp_manager.get_mount_path(agent_id),
        "stats": gateway.get_stats()
    }


@router.post("/{agent_id}/mcp/refresh")
async def refresh_agent_mcp(agent_id: str):
    """
    Refresh agent MCP Gateway.
    
    Re-discovers tools and skills from sub-servers.
    Use this after sub-MCP servers are restarted or updated.
    """
    mcp_manager = get_mcp_gateway_manager()
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Gateway Manager not available")
    
    success = await mcp_manager.refresh_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found or refresh failed")
    
    return {"status": "ok", "message": "MCP Gateway refreshed"}


@router.get("/mcp/list")
async def list_mcp_gateways():
    """
    List all MCP Gateways.
    
    Returns list of all mounted agent MCP gateways with their stats.
    """
    mcp_manager = get_mcp_gateway_manager()
    if not mcp_manager:
        raise HTTPException(status_code=503, detail="MCP Gateway Manager not available")
    
    return {
        "gateways": mcp_manager.list_agents(),
        "stats": mcp_manager.get_stats()
    }
