"""
Saga Handlers - Saga 触发

Topics:
- saga.trigger: 触发新 Saga
"""

from typing import Dict, Any
from . import register_handler


@register_handler("saga.trigger")
def handle_saga_trigger(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    触发新 Saga
    
    幂等性：通过 idempotency_key 检查是否已创建
    
    Payload:
        saga_type: str (runtime_start / react_think / react_actions / runtime_complete)
        context: dict
        idempotency_key: str (可选)
    """
    saga_client = ctx.get("saga_client")
    
    saga_type = payload["saga_type"]
    saga_context = payload.get("context", {})
    idempotency_key = payload.get("idempotency_key")
    
    if not saga_client:
        return {
            "success": False,
            "error": "Saga client not configured",
        }
    
    try:
        # Prefer async create (non-blocking) when available.
        if hasattr(saga_client, "create") and callable(getattr(saga_client, "create")):
            saga_id = saga_client.create(
                saga_type=saga_type,
                context=saga_context,
                idempotency_key=idempotency_key,
            )
        else:
            saga_id = saga_client.start(
                saga_type=saga_type,
                context=saga_context,
                idempotency_key=idempotency_key,
            )
        
        return {
            "success": True,
            "saga_id": saga_id,
            "saga_type": saga_type,
        }
        
    except Exception as e:
        # 检查是否是幂等冲突
        if "already exists" in str(e).lower() or "unique constraint" in str(e).lower():
            return {
                "success": True,
                "saga_type": saga_type,
                "message": "Saga already exists (idempotent)",
            }
        
        return {
            "success": False,
            "error": str(e),
            "saga_type": saga_type,
        }
