"""
MCP Handlers - MCP Server 管理

Topics:
- mcp.create: 创建 MCP Server
- mcp.destroy: 销毁 MCP Server

使用 task_queue.business.MCPBusiness 业务逻辑层。
"""

from typing import Dict, Any
from . import register_handler
from ..business import MCPBusiness
from ..topics import TaskTopics


@register_handler(TaskTopics.MCP_CREATE)
def handle_mcp_create(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    创建 MCP Server
    
    幂等性：检查是否已存在
    
    Payload:
        runtime_id: str
        agent_id: str
    """
    biz = MCPBusiness(
        gateway_url=ctx["gateway_url"],
        gateway_client=ctx.get("gateway_client"),
        ro_client=ctx.get("ro_client"),
    )
    result = biz.create(
        runtime_id=payload["runtime_id"],
        agent_id=payload["agent_id"],
    )
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.mcp_url:
        response["mcp_url"] = result.mcp_url
    if result.created is not None:
        response["created"] = result.created
    if result.message:
        response["message"] = result.message
    if result.error:
        response["error"] = result.error
    
    return response


@register_handler(TaskTopics.MCP_DESTROY)
def handle_mcp_destroy(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    销毁 MCP Server
    
    幂等性：检查是否已不存在
    
    Payload:
        runtime_id: str
    """
    biz = MCPBusiness(
        gateway_url=ctx["gateway_url"],
        gateway_client=ctx.get("gateway_client"),
        ro_client=ctx.get("ro_client"),
    )
    result = biz.destroy(payload["runtime_id"])
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.destroyed is not None:
        response["destroyed"] = result.destroyed
    if result.message:
        response["message"] = result.message
    if result.error:
        response["error"] = result.error
    
    return response
