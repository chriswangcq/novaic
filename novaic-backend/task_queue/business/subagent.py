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
- wake 方法已废弃，用 get_or_create_runtime 原子操作替代
"""

from dataclasses import dataclass
from typing import Optional

from ..client import GatewayInternalClient


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
        >>> subagent_biz = SubAgentBusiness(db)
        >>> result = subagent_biz.wake(agent_id="agent-1", subagent_id="main")
        >>> if result.success:
        ...     print(f"Status: {result.previous_status} → {result.status}")
    """
    
    def __init__(self, gateway_url: str, client: Optional[GatewayInternalClient] = None):
        """
        Args:
            gateway_url: Gateway URL
            client: 可复用的 GatewayInternalClient
        """
        self.client = client or GatewayInternalClient(gateway_url)
    
    def wake(
        self,
        agent_id: str,
        subagent_id: str,
    ) -> SubAgentStateResult:
        """
        唤醒 SubAgent (sleeping/failed → awaking)
        
        用于消息触发时的第一步，锁定 SubAgent 防止并发唤醒。
        
        幂等性：
        - sleeping/failed → awaking: 成功
        - awaking: 正在启动，返回成功（幂等）
        - awake: 已经唤醒，返回成功（幂等）
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            
        Returns:
            SubAgentStateResult
        """
        response = self.client.wake_subagent(agent_id, subagent_id, target_status="awaking")
        if response.get("success"):
            status = response.get("status")
            if not status:
                status = self.get_status(agent_id, subagent_id) or "awaking"
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
            error=response.get("error", "Wake failed"),
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
        response = self.client.set_subagent_awake(agent_id, subagent_id)
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
        response = self.client.set_subagent_sleeping(agent_id, subagent_id)
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
        response = self.client.get_subagent(agent_id, subagent_id)
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
        response = self.client.get_subagent_status(agent_id, subagent_id)
        return response.get("status") if response else None
