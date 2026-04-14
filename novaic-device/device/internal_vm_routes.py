"""
Internal VM API routes — SSH keys and VM tools discovery.

Extracted from gateway/api/internal/vm.py.
"""

from fastapi import APIRouter, HTTPException

from common.tools import VM_TOOLS

router = APIRouter(tags=["internal"])


@router.get("/vm/ssh/public-key/{agent_id}")
def get_ssh_public_key(agent_id: str):
    """Get SSH public key for the owner of agent_id."""
    from device.vm.ssh import get_ssh_key_manager
    manager = get_ssh_key_manager()
    public_key = manager.get_public_key_for_agent(agent_id)
    return {"public_key": public_key}


@router.get("/vm/ssh/private-key-path/{agent_id}")
def get_ssh_private_key_path(agent_id: str):
    """Get path to SSH private key file for the owner of agent_id."""
    from device.vm.ssh import get_ssh_key_manager
    manager = get_ssh_key_manager()
    key_path = manager.get_private_key_path_for_agent(agent_id)
    return {"key_path": str(key_path)}


@router.get("/subagents/{agent_id}/{subagent_id}/vm-tools")
async def get_subagent_vm_tools(agent_id: str, subagent_id: str):
    """Get SubAgent's VM tools list."""
    from device.entity_store import get_entity_store
    store = get_entity_store()
    if not store.get("subagents", "", subagent_id, params={"agent_id": agent_id}):
        raise HTTPException(status_code=404, detail="SubAgent not found")

    from device.config_agents import get_agent_config_manager
    config_mgr = get_agent_config_manager()
    try:
        agent = config_mgr.get_agent(agent_id)
    except Exception as e:
        return {
            "tools": [],
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "vm_available": False,
            "error": str(e),
        }

    if not getattr(agent, "vm", None) or not agent.vm:
        return {
            "tools": [],
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "vm_available": False,
        }

    try:
        return {
            "tools": VM_TOOLS,
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "vm_available": True,
        }
    except Exception as e:
        return {
            "tools": [],
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "vm_available": False,
            "error": str(e),
        }
