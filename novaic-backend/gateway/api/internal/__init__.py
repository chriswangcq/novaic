"""
Internal API - Gateway business router

Gateway process only mounts business-domain internal APIs.
/internal/runtimes* and /internal/subagents* are NOT exposed by Gateway; RO (runtime_orchestrator) owns those domains.
"""

from fastapi import APIRouter

from .agent import router as agent_router
from .broadcast import router as broadcast_router
from .config import router as config_router
from .health import router as health_router
from .llm import router as llm_router
from .message import router as message_router
from .task import router as task_router
from .vm import router as vm_router
from .web import router as web_router

router = APIRouter(prefix="/internal", tags=["internal"])

router.include_router(agent_router)
router.include_router(broadcast_router)
router.include_router(config_router)
router.include_router(health_router)
router.include_router(llm_router)
router.include_router(message_router)
router.include_router(task_router)
router.include_router(vm_router)
router.include_router(web_router)
