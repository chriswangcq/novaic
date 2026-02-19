"""
Runtime Business - Runtime 生命周期管理

业务逻辑：
- 创建 Runtime
- 设置 Status (CAS)
- 增加 Round

DEPRECATED:
- 更新 Phase (CAS) - 已删除，Saga 步骤替代 phase 状态
"""

from dataclasses import dataclass
from common.enums import RuntimeStatus
from typing import Dict, Any, List, Optional

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..client import GatewayInternalClient, RuntimeOrchestratorClient


@dataclass
class RuntimeCreateResult:
    """创建 Runtime 结果"""
    success: bool
    runtime_id: str
    created: bool
    message: str = ""
    status: str = ""
    phase: str = ""


@dataclass
class RuntimeUpdateResult:
    """更新 Runtime 结果"""
    success: bool
    runtime_id: str
    previous_value: str = ""
    new_value: str = ""
    current_value: str = ""
    message: str = ""


class RuntimeBusiness:
    """
    Runtime 业务逻辑
    
    所有方法都是幂等的：
    - create: 通过 idempotency_key 检查
    - set_status: 通过 CAS 检查
    
    Example:
        >>> from task_queue.business import RuntimeBusiness
        >>> runtime_biz = RuntimeBusiness(db)
        >>> result = runtime_biz.create(agent_id="agent-1", subagent_id="main")
        >>> print(result.runtime_id)
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
            ro_client: RuntimeOrchestratorClient for RO-owned APIs (preferred)
            client: Legacy GatewayInternalClient; if provided, uses client.ro_client
        """
        if client is not None:
            self.ro_client = client.ro_client
        elif ro_client is not None:
            self.ro_client = ro_client
        else:
            raise ValueError(
                "RuntimeBusiness requires explicit ro_client (fallback creation is disabled)"
            )
    
    def create(
        self,
        agent_id: str,
        subagent_id: str,
        *,
        idempotency_key: Optional[str] = None,
        initial_context: Optional[List[Dict[str, Any]]] = None,
    ) -> RuntimeCreateResult:
        """
        创建 Runtime 记录
        
        幂等性：如果有 idempotency_key，检查是否已存在
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            idempotency_key: 幂等键
            initial_context: 可选的初始 context（历史摘要等）
            
        Returns:
            RuntimeCreateResult
        """
        # 幂等检查：只复用 active 状态的 runtime
        if idempotency_key:
            existing = self.ro_client.get_subagent_runtime(agent_id, subagent_id)
            if existing and existing.get("status") == RuntimeStatus.ACTIVE.value:
                return RuntimeCreateResult(
                    success=True,
                    runtime_id=existing["runtime_id"],
                    created=False,
                    message="Runtime already exists",
                    status=existing.get("status", ""),
                    phase=existing.get("phase", ""),
                )

        # 创建 runtime，传入 initial_context（可能包含历史摘要）
        runtime = self.ro_client.create_runtime(agent_id, subagent_id, initial_context or [])
        return RuntimeCreateResult(
            success=True,
            runtime_id=runtime.get("runtime_id", ""),
            created=True,
            status=runtime.get("status", RuntimeStatus.ACTIVE.value),
            phase=runtime.get("phase", ""),  # phase 已废弃，保留字段兼容
        )
    
    # DEPRECATED: update_phase 已删除，Saga 步骤替代 phase 状态
    
    def set_status(
        self,
        runtime_id: str,
        expected_status,  # str 或 List[str]
        new_status: str,
    ) -> RuntimeUpdateResult:
        """
        设置 Runtime status (CAS)
        
        幂等性：如果已经是目标状态，返回成功
        
        Args:
            runtime_id: Runtime ID
            expected_status: 期望的当前 status（字符串或列表）
            new_status: 目标 status
            
        Returns:
            RuntimeUpdateResult
        """
        # 支持单个状态或状态列表
        if isinstance(expected_status, str):
            expected_list = [expected_status]
        else:
            expected_list = expected_status
        
        resp = self.ro_client.set_runtime_status(runtime_id, expected_list, new_status)
        if resp.get("success"):
            return RuntimeUpdateResult(
                success=True,
                runtime_id=runtime_id,
                previous_value=str(expected_list),
                new_value=new_status,
            )

        current_status = resp.get("current_status", "not_found")
        return RuntimeUpdateResult(
            success=current_status == new_status,
            runtime_id=runtime_id,
            current_value=current_status,
            new_value=new_status,
            message="Already in target status" if current_status == new_status else "Status mismatch",
        )
    
    def increment_round(self, runtime_id: str) -> Dict[str, Any]:
        """
        增加 Runtime round 计数
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            {"success": bool, "round_num": int}
        """
        result = self.ro_client.advance_round(runtime_id)
        if not result.get("success"):
            return {"success": False, "runtime_id": runtime_id, "round_num": None}

        runtime = self.ro_client.get_runtime(runtime_id)
        return {
            "success": True,
            "runtime_id": runtime_id,
            "round_num": runtime.get("current_round_num") if runtime else None,
        }
    
    def set_summarized(self, runtime_id: str) -> RuntimeUpdateResult:
        """
        设置 Runtime 已生成摘要
        
        幂等性：如果已经是 summarized=1，返回成功
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            RuntimeUpdateResult
        """
        resp = self.ro_client.set_runtime_summarized(runtime_id)
        if resp.get("success"):
            return RuntimeUpdateResult(
                success=True,
                runtime_id=runtime_id,
                previous_value="0",
                new_value="1",
            )

        return RuntimeUpdateResult(
            success=resp.get("current_value") == "1",
            runtime_id=runtime_id,
            current_value=resp.get("current_value", ""),
            new_value="1",
            message=resp.get("message", ""),
        )
    
    def set_need_rest(self, runtime_id: str, value: bool = True) -> RuntimeUpdateResult:
        """
        设置 Runtime need_rest 标志
        
        幂等性：如果已经是目标值，返回成功
        
        Args:
            runtime_id: Runtime ID
            value: 目标值（默认 True）
            
        Returns:
            RuntimeUpdateResult
        """
        resp = self.ro_client.set_runtime_need_rest(runtime_id, value)
        target = "1" if value else "0"
        return RuntimeUpdateResult(
            success=resp.get("success") or resp.get("current_value") == target,
            runtime_id=runtime_id,
            current_value=resp.get("current_value", ""),
            new_value=target,
            message=resp.get("message", ""),
        )
    
    def get(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Runtime 信息
        
        Args:
            runtime_id: Runtime ID
            
        Returns:
            Runtime 信息或 None
        """
        return self.ro_client.get_runtime(runtime_id)
