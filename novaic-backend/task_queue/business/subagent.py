"""
SubAgent Business - SubAgent 状态管理 (v3)

业务逻辑：
- 设置 awake (sleeping → awake)
- 设置 sleeping (any → sleeping)

状态转换图 (v3 简化)：
    sleeping ──(set_awake)──> awake
        ^                        │
        └────(set_sleeping)──────┘

v3 变更：
- 删除 awaking 中间状态
- 删除 wake 方法，用 get_or_create_runtime 原子操作替代
"""

from dataclasses import dataclass
from typing import Optional

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GatewayInternalClient, RuntimeOrchestratorClient


@dataclass
class SubAgentStateResult:
    """SubAgent 状态更新结果"""
    success: bool
    subagent_id: str
    previous_status: str = ""
    status: str = ""
    message: str = ""
    error: str = ""


class SubAgentBusiness:
    """
    SubAgent 业务逻辑
    
    所有方法都是幂等的，通过 CAS 保证。
    
    Example:
        >>> from task_queue.business import SubAgentBusiness
        >>> subagent_biz = SubAgentBusiness(gateway_url)
        >>> result = subagent_biz.set_awake(agent_id="agent-1", subagent_id="main", runtime_id="rt-xxx")
        >>> if result.success:
        ...     print(f"Status: {result.previous_status} → {result.status}")
    """
    
    def __init__(
        self,
        gateway_url: str,
        ro_client: "RuntimeOrchestratorClient" = None,
        client: Optional["GatewayInternalClient"] = None,
    ):
        """
        Args:
            gateway_url: Gateway URL (used when ro_client not provided)
            ro_client: RuntimeOrchestratorClient (preferred)
            client: Legacy GatewayInternalClient; if provided, uses client.ro_client
        """
        if client is not None:
            self.ro_client = client.ro_client
        elif ro_client is not None:
            self.ro_client = ro_client
        else:
            raise ValueError(
                "SubAgentBusiness requires explicit ro_client (fallback creation is disabled)"
            )
    
    def set_awake(
        self,
        agent_id: str,
        subagent_id: str,
        runtime_id: str,
    ) -> SubAgentStateResult:
        """
        设置 SubAgent 为 awake (sleeping → awake)
        
        用于 RuntimeStart Saga 完成后，确认 Runtime 启动成功。
        
        幂等性：
        - sleeping → awake: 成功
        - awake: 已经是目标状态（幂等）
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            runtime_id: Runtime ID
            
        Returns:
            SubAgentStateResult
        """
        # 直接设置为 awake（v3: 删除 awaking 中间状态）
        response = self.ro_client.set_subagent_awake(agent_id, subagent_id)
        if response.get("success"):
            status = response.get("status")
            if not status:
                status = self.get_status(agent_id, subagent_id) or "awake"
            return SubAgentStateResult(
                success=True,
                subagent_id=subagent_id,
                previous_status=response.get("previous_status", ""),
                status=status,
                message=response.get("message", ""),
            )

        return SubAgentStateResult(
            success=False,
            subagent_id=subagent_id,
            previous_status=response.get("previous_status", ""),
            status=response.get("status", ""),
            error=response.get("error", "Set awake failed"),
        )
    
    def set_sleeping(
        self,
        agent_id: str,
        subagent_id: str,
    ) -> SubAgentStateResult:
        """
        设置 SubAgent 为 sleeping
        
        用于 RuntimeComplete Saga 完成后，让 SubAgent 进入休眠。
        
        幂等性：无论当前状态，都设置为 sleeping
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            
        Returns:
            SubAgentStateResult
        """
        response = self.ro_client.set_subagent_sleeping(agent_id, subagent_id)
        status = response.get("status")
        if not status and response.get("success"):
            status = self.get_status(agent_id, subagent_id) or "sleeping"
        return SubAgentStateResult(
            success=response.get("success", False),
            subagent_id=subagent_id,
            previous_status=response.get("previous_status", ""),
            status=status or "sleeping",
            message=response.get("message", ""),
            error=response.get("error", ""),
        )
    
    def set_completed(
        self,
        agent_id: str,
        subagent_id: str,
        result: Optional[str] = None,
    ) -> SubAgentStateResult:
        """
        设置 Sub SubAgent 为 completed（带 result）
        
        用于 RuntimeComplete Saga 完成后，将 Sub SubAgent 的结果写入。
        仅用于 Sub SubAgent（subagent_id 以 'sub-' 开头）。
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            result: 任务执行结果
            
        Returns:
            SubAgentStateResult
        """
        response = self.ro_client.set_subagent_completed(agent_id, subagent_id, result=result)
        status = response.get("status")
        if not status and response.get("success"):
            status = self.get_status(agent_id, subagent_id) or "completed"
        return SubAgentStateResult(
            success=response.get("success", True),
            subagent_id=subagent_id,
            previous_status=response.get("previous_status", ""),
            status=status or "completed",
            message=response.get("message", ""),
            error=response.get("error", ""),
        )
    
    def get(
        self,
        agent_id: str,
        subagent_id: str,
    ) -> Optional[dict]:
        """
        获取 SubAgent 信息
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            
        Returns:
            SubAgent 信息或 None
        """
        response = self.ro_client.get_subagent(agent_id, subagent_id)
        return response.get("subagent") if response else None
    
    def get_status(
        self,
        agent_id: str,
        subagent_id: str,
    ) -> Optional[str]:
        """
        获取 SubAgent 状态
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            
        Returns:
            状态字符串或 None
        """
        response = self.ro_client.get_subagent_status(agent_id, subagent_id)
        return response.get("status") if response else None
