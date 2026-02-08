"""
Tools Server HTTP API（使用 FastAPI）

提供 Runtime 管理、工具调用、Skills 访问等 API 端点。
本模块由 main_tools.py 加载。
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ==================== Request/Response Models ====================

class CreateRuntimeRequest(BaseModel):
    """创建 Runtime 请求"""
    runtime_id: str
    agent_id: str
    subagent_id: str
    ports: dict = {}


class CallToolRequest(BaseModel):
    """工具调用请求"""
    name: str
    arguments: dict = {}


class CallToolResponse(BaseModel):
    """工具调用响应"""
    success: bool
    result: Any = None
    error: Optional[str] = None


class SkillInfo(BaseModel):
    """Skill 信息"""
    name: str
    path: str


# ==================== Routers ====================

router = APIRouter()
internal_router = APIRouter(prefix="/internal", tags=["internal-tools"])


# ==================== Helper Functions ====================

def _get_skills_directory() -> Path:
    """获取 Skills 目录路径"""
    # 默认路径: mcp_client/skills/
    base_dir = Path(__file__).parent.parent / "mcp_client" / "skills"
    
    # 支持环境变量覆盖
    custom_path = os.environ.get("NOVAIC_SKILLS_DIR")
    if custom_path:
        base_dir = Path(custom_path)
    
    return base_dir


def _list_skills() -> List[SkillInfo]:
    """列出所有可用的 Skills"""
    skills_dir = _get_skills_directory()
    skills = []
    
    if not skills_dir.exists():
        logger.warning(f"[ToolsAPI] Skills directory not found: {skills_dir}")
        return skills
    
    for item in skills_dir.iterdir():
        if item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                skills.append(SkillInfo(
                    name=item.name,
                    path=str(skill_file)
                ))
    
    return sorted(skills, key=lambda s: s.name)


def _get_skill_content(skill_name: str) -> Optional[str]:
    """获取 Skill 内容"""
    skills_dir = _get_skills_directory()
    skill_file = skills_dir / skill_name / "SKILL.md"
    
    if not skill_file.exists():
        return None
    
    try:
        return skill_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"[ToolsAPI] Failed to read skill {skill_name}: {e}")
        return None


# ==================== Health Check ====================

@router.get("/api/health")
async def health_check():
    """健康检查端点"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    
    return {
        "status": "healthy",
        "service": "tools-server",
        "manager_initialized": manager is not None,
        "runtime_count": len(manager.list_all()) if manager else 0,
    }


# ==================== Runtime Management ====================

@internal_router.post("/runtimes")
async def create_runtime(request: CreateRuntimeRequest):
    """创建 Runtime 工具上下文"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    try:
        # 检查是否已存在
        existing = manager.get(request.runtime_id)
        if existing:
            return {
                "status": "ok",
                "runtime_id": request.runtime_id,
                "agent_id": request.agent_id,
                "subagent_id": request.subagent_id,
                "message": "Runtime already exists",
            }
        
        # 创建新 Runtime
        runtime = manager.create(
            runtime_id=request.runtime_id,
            agent_id=request.agent_id,
            subagent_id=request.subagent_id,
            ports=request.ports,
        )
        
        # 启动外部工具发现
        await manager.start_discovery(request.runtime_id)
        
        return {
            "status": "ok",
            "runtime_id": request.runtime_id,
            "agent_id": request.agent_id,
            "subagent_id": request.subagent_id,
        }
        
    except ValueError as e:
        # Runtime 已存在
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"[ToolsAPI] Failed to create runtime {request.runtime_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal_router.delete("/runtimes/{runtime_id}")
async def delete_runtime(runtime_id: str):
    """删除 Runtime 工具上下文"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    try:
        success = manager.delete(runtime_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
        
        return {"status": "ok", "runtime_id": runtime_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ToolsAPI] Failed to delete runtime {runtime_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal_router.get("/runtimes")
async def list_runtimes():
    """列出所有 Runtime"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        return {"runtimes": [], "total": 0}
    
    runtimes = manager.list_all()
    
    return {
        "runtimes": [
            {
                "runtime_id": rt.runtime_id,
                "agent_id": rt.agent_id,
                "subagent_id": rt.subagent_id,
                "ports": rt.ports,
                "created_at": rt.created_at.isoformat() if rt.created_at else None,
            }
            for rt in runtimes
        ],
        "total": len(runtimes),
    }


@internal_router.get("/runtimes/{runtime_id}")
async def get_runtime(runtime_id: str):
    """获取单个 Runtime 信息"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    runtime = manager.get(runtime_id)
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
    
    return {
        "runtime_id": runtime.runtime_id,
        "agent_id": runtime.agent_id,
        "subagent_id": runtime.subagent_id,
        "ports": runtime.ports,
        "created_at": runtime.created_at.isoformat() if runtime.created_at else None,
    }


# ==================== Tools API ====================

@internal_router.get("/runtimes/{runtime_id}/tools")
async def get_tools(runtime_id: str):
    """获取工具列表（内置 + 外部）"""
    from tools_server.runtime_manager import get_runtime_manager
    from tools_server.tools import get_all_tools
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    runtime = manager.get(runtime_id)
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
    
    try:
        # 获取内置工具
        builtin_tools = get_all_tools()
        
        # Phase 5: Per-agent tool filtering
        agent_id = getattr(runtime, "agent_id", None)
        if agent_id:
            try:
                import httpx
                gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
                with httpx.Client(timeout=5.0, trust_env=False) as client:
                    resp = client.get(f"{gateway_url}/api/agents/{agent_id}/tools-config")
                    if resp.status_code == 200:
                        config = resp.json()
                        enabled_cats = config.get("enabled_tool_categories", [])
                        disabled = set(config.get("disabled_tools", []))
                        
                        if enabled_cats or disabled:
                            from tools_server.tools import BUILTIN_TOOLS
                            filtered = []
                            for tool in builtin_tools:
                                tool_name = tool.get("name", "")
                                # Check category filter
                                if enabled_cats:
                                    tool_in_enabled = False
                                    for cat, cat_tools in BUILTIN_TOOLS.items():
                                        if cat in enabled_cats:
                                            if any(t["name"] == tool_name for t in cat_tools):
                                                tool_in_enabled = True
                                                break
                                    if not tool_in_enabled:
                                        continue
                                # Check disabled list
                                if tool_name in disabled:
                                    continue
                                filtered.append(tool)
                            builtin_tools = filtered
            except Exception as e:
                logger.warning(f"[ToolsAPI] Failed to filter tools for agent {agent_id}: {e}")
        
        # 获取外部工具（从 RuntimeManager 的发现结果）
        external_tools = manager.get_external_tools(runtime_id)
        
        # 合并工具列表
        tools = []
        
        # 添加内置工具
        for tool in builtin_tools:
            tools.append({
                "name": tool.get("name"),
                "description": tool.get("description"),
                "input_schema": tool.get("inputSchema"),
                "source": "builtin",
            })
        
        # 添加外部工具
        for tool in external_tools:
            tools.append({
                "name": tool.get("name"),
                "description": tool.get("description"),
                "input_schema": tool.get("inputSchema"),
                "source": "external",
            })
        
        return {
            "runtime_id": runtime_id,
            "tools": tools,
            "total": len(tools),
            "builtin_count": len(builtin_tools),
            "external_count": len(external_tools),
        }
        
    except Exception as e:
        logger.error(f"[ToolsAPI] Failed to get tools for {runtime_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@internal_router.post("/runtimes/{runtime_id}/tools/call")
async def call_tool(runtime_id: str, request: CallToolRequest):
    """调用工具"""
    from tools_server.runtime_manager import get_runtime_manager
    from tools_server.executor import ToolExecutor
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    runtime = manager.get(runtime_id)
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
    
    try:
        # 为每次调用创建新的 ToolExecutor
        executor = ToolExecutor(runtime=runtime, manager=manager)
        
        result = await executor.execute(
            tool_name=request.name,
            arguments=request.arguments,
        )
        
        # 解包工具返回的 {success, result, error} 格式（避免双层嵌套）
        if isinstance(result, dict):
            if "result" in result:
                # 工具返回了 {success, result} 格式，解包
                actual_result = result.get("result")
                actual_success = result.get("success", True)
                actual_error = result.get("error")
            else:
                # 工具返回了直接数据（无包装）
                actual_result = result
                actual_success = result.get("success", True) if "success" in result else True
                actual_error = result.get("error")
        else:
            # 非字典结果，直接使用
            actual_result = result
            actual_success = True
            actual_error = None
        
        return CallToolResponse(
            success=actual_success,
            result=actual_result,
            error=actual_error,
        )
        
    except Exception as e:
        logger.error(f"[ToolsAPI] Tool call failed: {request.name} - {e}")
        return CallToolResponse(
            success=False,
            result=None,
            error=str(e),
        )


# ==================== Skills API ====================

@internal_router.get("/runtimes/{runtime_id}/skills")
async def get_skills(runtime_id: str):
    """获取 Skills 列表"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    runtime = manager.get(runtime_id)
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
    
    skills = _list_skills()
    
    return {
        "runtime_id": runtime_id,
        "skills": [
            {"name": skill.name, "path": skill.path}
            for skill in skills
        ],
        "total": len(skills),
    }


@internal_router.get("/runtimes/{runtime_id}/skills/{skill_name}")
async def get_skill(runtime_id: str, skill_name: str):
    """获取 Skill 内容"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="RuntimeManager not available")
    
    runtime = manager.get(runtime_id)
    if not runtime:
        raise HTTPException(status_code=404, detail=f"Runtime {runtime_id} not found")
    
    content = _get_skill_content(skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    
    return {
        "runtime_id": runtime_id,
        "skill_name": skill_name,
        "content": content,
    }


# ==================== Stats API ====================

@internal_router.get("/stats")
async def get_stats():
    """获取服务统计"""
    from tools_server.runtime_manager import get_runtime_manager
    
    manager = get_runtime_manager()
    if not manager:
        return {
            "status": "not_initialized",
            "runtime_count": 0,
            "skills_count": 0,
        }
    
    # 使用 RuntimeManager 的 get_stats 方法
    manager_stats = manager.get_stats()
    skills = _list_skills()
    
    return {
        "status": "ok",
        "runtime_count": manager_stats.get("total_runtimes", 0),
        "skills_count": len(skills),
        "active_discoveries": manager_stats.get("active_discoveries", 0),
        "total_external_tools": manager_stats.get("total_external_tools", 0),
        "runtimes": manager_stats.get("runtimes", []),
        "skills": [s.name for s in skills],
    }
