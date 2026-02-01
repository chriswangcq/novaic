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

from config.agents import (
    get_agent_config_manager,
    AICAgent,
    VmConfig,
    PortConfig,
)
from mcp_servers.manager import get_mcp_manager

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
            from db.database import get_database
            from db.repositories.message import MessageRepository
            
            db = get_database()
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
