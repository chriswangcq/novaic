"""
Message Business - 消息处理

业务逻辑：
- 处理用户消息
- 认领消息 (CAS)
- 追加消息到 context
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GatewayInternalClient, GatewayBusinessClient, RuntimeOrchestratorClient


@dataclass
class MessageProcessResult:
    """消息处理结果"""
    success: bool
    message_id: str
    action: str = ""  # wake_only, runtime_start, append_to_runtime, pending, skipped
    runtime_id: str = ""
    saga_id: str = ""
    error: str = ""
    message: str = ""


@dataclass
class ContextAppendResult:
    """追加 Context 结果"""
    success: bool
    runtime_id: str
    appended: bool = False
    context_length: int = 0
    message: str = ""
    error: str = ""


class MessageBusiness:
    """
    消息业务逻辑
    
    Example:
        >>> from task_queue.business import MessageBusiness
        >>> msg_biz = MessageBusiness(db)
        >>> result = msg_biz.append_to_context(
        ...     runtime_id="rt-123",
        ...     message={"role": "assistant", "content": "Hello"},
        ...     idempotency_key="rt-123-round1-response",
        ... )
    """
    
    def __init__(
        self,
        gateway_url: str,
        gateway_client: "GatewayBusinessClient" = None,
        ro_client: "RuntimeOrchestratorClient" = None,
        client: Optional["GatewayInternalClient"] = None,
    ):
        """
        Args:
            gateway_url: Gateway URL (used when clients not provided)
            gateway_client: GatewayBusinessClient for messages (preferred)
            ro_client: RuntimeOrchestratorClient for runtime/subagent (preferred)
            client: Legacy GatewayInternalClient; if provided, extracts .gateway_client and .ro_client
        """
        if client is not None:
            self.gateway_client = client.gateway_client
            self.ro_client = client.ro_client
        elif gateway_client is not None and ro_client is not None:
            self.gateway_client = gateway_client
            self.ro_client = ro_client
        else:
            raise ValueError(
                "MessageBusiness requires explicit gateway_client and ro_client "
                "(fallback creation is disabled)"
            )
    
    def append_to_context(
        self,
        runtime_id: str,
        message: Dict[str, Any],
        *,
        message_type: str = "unknown",
        round_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ContextAppendResult:
        """
        追加消息到 runtime context
        
        幂等性：通过 idempotency_key 检查
        
        Args:
            runtime_id: Runtime ID
            message: 消息内容
            message_type: 消息类型 (llm_response / tool_result / user / etc.)
            round_id: Round ID
            idempotency_key: 幂等键
            
        Returns:
            ContextAppendResult
        """
        response = self.ro_client.append_context(
            runtime_id=runtime_id,
            message=message,
            message_type=message_type,
            round_id=round_id,
            idempotency_key=idempotency_key,
        )

        if not response.get("success"):
            return ContextAppendResult(
                success=False,
                runtime_id=runtime_id,
                error=response.get("error", "Append failed"),
            )

        return ContextAppendResult(
            success=True,
            runtime_id=runtime_id,
            appended=response.get("appended", False),
            context_length=response.get("context_length", 0),
            message=response.get("message", ""),
        )
    
    def get_context(self, runtime_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取 runtime context
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            Context 列表或 None
        """
        runtime = self.ro_client.get_runtime(runtime_id)
        if not runtime:
            return None
        return runtime.get("context") or []
    
    def claim_message(self, message_id: str) -> Dict[str, Any]:
        """
        认领消息 (sending → sent)
        
        幂等性：CAS 检查
        
        Args:
            message_id: 消息 ID
            
        Returns:
            {"success": bool, "claimed": bool, "current_status": str}
        """
        return self.gateway_client.claim_message(message_id)
    
    def find_active_runtime(
        self,
        agent_id: str,
        subagent_id: str,
    ) -> Optional[str]:
        """
        查找活跃的 Runtime
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            
        Returns:
            Runtime ID 或 None
        """
        runtime = self.ro_client.get_subagent_runtime(agent_id, subagent_id)
        return runtime.get("runtime_id") if runtime else None
