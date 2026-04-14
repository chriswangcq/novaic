"""Business Internal API — all /internal/* endpoints live here."""

from fastapi import APIRouter

from .agent import router as agent_router
from .config import router as config_router
from .entity import router as entity_router
from .health import router as health_router
from .message import router as message_router
from .subagent import router as subagent_router
from .task import router as task_router

router = APIRouter(prefix="/internal", tags=["internal"])

router.include_router(agent_router)
router.include_router(config_router)
router.include_router(entity_router)
router.include_router(health_router)
router.include_router(message_router)
router.include_router(subagent_router)
router.include_router(task_router)
