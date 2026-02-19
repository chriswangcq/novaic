"""
Runtime Orchestrator internal router.

This package is the canonical home for runtime-orchestrator-only internal APIs.
RO owns /internal/runtimes* and /internal/subagents* (and related /internal/agents/* subagent-facing).
"""

from fastapi import APIRouter

from .runtime import router as runtime_router
from .subagent import router as subagent_router

router = APIRouter(prefix="/internal", tags=["internal-runtime-orchestrator"])
router.include_router(runtime_router)
router.include_router(subagent_router)

