"""
Internal API for MCP Gateway（Backend 组件）— MCP 生命周期与统计。

Master 调用本 API 创建/删除 MCP；Gateway 代理 /api/agents/mcp/* 时请求本 API。
本模块仅由 mcp_main.py 加载。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os

router = APIRouter(prefix="/internal", tags=["internal-mcp"])


def _get_mcp_gateway_base() -> str:
    """Base URL of this MCP Gateway (for returning full mcp_url)."""
    base = os.environ.get("NOVAIC_MCP_GATEWAY_URL")
    if base:
        return base.rstrip("/")
    port = int(os.environ.get("NOVAIC_PORT", "19998"))
    return f"http://127.0.0.1:{port}"


# ==================== MCP Operations ====================

@router.post("/mcp/agent-shared")
async def create_agent_shared_mcp(data: Dict[str, Any]):
    """Create agent shared layer MCP servers."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        raise HTTPException(status_code=503, detail="MCP Manager not available")

    agent_id = data.get("agent_id")
    agent_index = data.get("agent_index", 0)

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    await mcp_mgr.create_agent_shared_servers(agent_id, agent_index)

    return {"status": "ok"}


@router.get("/mcp/agent-shared/{agent_id}/exists")
async def has_agent_shared_mcp(agent_id: str):
    """Check if agent shared MCP servers exist."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"exists": False}

    return {"exists": mcp_mgr.has_agent_shared_servers(agent_id)}


@router.delete("/mcp/agent-shared/{agent_id}")
async def remove_agent_shared_mcp(agent_id: str):
    """Remove agent shared MCP servers."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"status": "ok"}

    await mcp_mgr.remove_agent_shared_servers(agent_id)

    return {"status": "ok"}


@router.post("/mcp/runtime")
async def create_runtime_mcp(data: Dict[str, Any]):
    """Create runtime MCP server."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        raise HTTPException(status_code=503, detail="MCP Manager not available")

    agent_id = data.get("agent_id")
    runtime_id = data.get("runtime_id")
    subagent_id = data.get("subagent_id")
    agent_index = data.get("agent_index", 0)

    if not agent_id or not runtime_id or not subagent_id:
        raise HTTPException(status_code=400, detail="agent_id, runtime_id and subagent_id required")

    await mcp_mgr.create_runtime_server(agent_id, runtime_id, subagent_id, agent_index)

    return {"status": "ok"}


@router.delete("/mcp/runtime/{runtime_id}")
async def remove_runtime_mcp(runtime_id: str):
    """Remove runtime MCP server."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"status": "ok"}

    await mcp_mgr.remove_runtime_server(runtime_id)

    return {"status": "ok"}


@router.delete("/mcp/runtime/{agent_id}/{runtime_id}")
async def remove_runtime_mcp_with_agent(agent_id: str, runtime_id: str):
    """Remove runtime MCP server (with agent_id for Gateway proxy)."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"status": "ok"}

    await mcp_mgr.remove_runtime_server(runtime_id)

    return {"status": "ok"}


@router.post("/mcp/aggregate")
async def create_aggregate_mcp(data: Dict[str, Any]):
    """Create aggregate MCP gateway. Returns full mcp_url for Worker/LLM."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        raise HTTPException(status_code=503, detail="MCP Manager not available")

    agent_id = data.get("agent_id")
    runtime_id = data.get("runtime_id")
    subagent_id = data.get("subagent_id")
    agent_index = data.get("agent_index", 0)

    if not agent_id or not runtime_id or not subagent_id:
        raise HTTPException(status_code=400, detail="agent_id, runtime_id and subagent_id required")

    await mcp_mgr.create_aggregate_gateway(agent_id, runtime_id, subagent_id, agent_index)

    base = _get_mcp_gateway_base()
    mcp_url = f"{base}/mcp/aggregate/{runtime_id}/"

    return {"status": "ok", "mcp_url": mcp_url}


@router.delete("/mcp/aggregate/{runtime_id}")
async def remove_aggregate_mcp(runtime_id: str):
    """Remove aggregate MCP gateway."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"status": "ok"}

    await mcp_mgr.remove_aggregate_gateway(runtime_id)

    return {"status": "ok"}


@router.delete("/mcp/aggregate/{agent_id}/{runtime_id}")
async def remove_aggregate_mcp_with_agent(agent_id: str, runtime_id: str):
    """Remove aggregate MCP gateway (with agent_id for Gateway proxy)."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"status": "ok"}

    await mcp_mgr.remove_aggregate_gateway(runtime_id)

    return {"status": "ok"}


@router.get("/mcp/aggregate/{subagent_id}/exists")
async def has_aggregate_mcp(subagent_id: str):
    """Check if aggregate MCP exists."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"exists": False}

    return {"exists": mcp_mgr.get_aggregate_gateway(subagent_id) is not None}


@router.get("/mcp/aggregate/{subagent_id}/url")
async def get_aggregate_mcp_url(subagent_id: str):
    """Get aggregate MCP full URL."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        raise HTTPException(status_code=503, detail="MCP Manager not available")

    base = _get_mcp_gateway_base()
    mcp_url = f"{base}/mcp/aggregate/{subagent_id}/"

    return {"mcp_url": mcp_url}


# ==================== Stats (for Backend proxy) ====================

@router.get("/mcp/stats")
async def get_mcp_stats():
    """Get MCPManager stats. Used by Backend to proxy /api/agents/mcp/status."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"stats": {}}

    return {"stats": mcp_mgr.get_stats()}


@router.get("/mcp/runtimes")
async def get_mcp_runtimes():
    """List Runtime MCP servers and Aggregate Gateways. Used by Backend to proxy /api/agents/mcp/runtimes."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"runtimes": [], "total": 0}

    stats = mcp_mgr.get_stats()
    runtimes = []
    for subagent_id in stats.get("runtime_servers", []):
        runtime_url = mcp_mgr.get_runtime_mount_path(subagent_id)
        aggregate_url = mcp_mgr.get_aggregate_mount_path(subagent_id)
        gateway = mcp_mgr.get_aggregate_gateway(subagent_id)
        runtimes.append({
            "subagent_id": subagent_id,
            "runtime_url": runtime_url,
            "aggregate_url": aggregate_url,
            "gateway_stats": gateway.get_stats() if gateway else None,
        })

    return {"runtimes": runtimes, "total": len(runtimes)}


@router.get("/mcp/servers")
async def list_mcp_servers():
    """List all active MCP servers (alias for stats + runtimes)."""
    from mcp_servers.manager import get_mcp_manager

    mcp_mgr = get_mcp_manager()
    if not mcp_mgr:
        return {"stats": {}, "runtimes": []}

    stats = mcp_mgr.get_stats()
    runtimes = []
    for subagent_id in stats.get("runtime_servers", []):
        runtime_url = mcp_mgr.get_runtime_mount_path(subagent_id)
        aggregate_url = mcp_mgr.get_aggregate_mount_path(subagent_id)
        runtimes.append({
            "subagent_id": subagent_id,
            "runtime_url": runtime_url,
            "aggregate_url": aggregate_url,
        })

    return {
        "stats": stats,
        "runtimes": runtimes,
        "agent_shared": stats.get("agent_shared_agents", []),
    }
