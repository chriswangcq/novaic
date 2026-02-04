"""
Runtime Business - Runtime 生命周期管理

业务逻辑：
- 创建 Runtime
- 更新 Phase (CAS)
- 设置 Status (CAS)
- 增加 Round
"""

from dataclasses import dataclass
from ..constants import PHASE_NEED_THINK
from typing import Dict, Any, List, Optional

from ..client import GatewayInternalClient


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
    - update_phase: 通过 CAS 检查
    - set_status: 通过 CAS 检查
    
    Example:
        >>> from task_queue.business import RuntimeBusiness
        >>> runtime_biz = RuntimeBusiness(db)
        >>> result = runtime_biz.create(agent_id="agent-1", subagent_id="main")
        >>> print(result.runtime_id)
    """
    
    def __init__(self, gateway_url: str, client: Optional[GatewayInternalClient] = None):
        """
        Args:
            gateway_url: Gateway URL
            client: 可复用的 GatewayInternalClient
        """
        self.client = client or GatewayInternalClient(gateway_url)
    
    def create(
        self,
        agent_id: str,
        subagent_id: str,
        *,
        idempotency_key: Optional[str] = None,
    ) -> RuntimeCreateResult:
        """
        创建 Runtime 记录
        
        幂等性：如果有 idempotency_key，检查是否已存在
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID
            idempotency_key: 幂等键
            
        Returns:
            RuntimeCreateResult
        """
        # 幂等检查：只复用 active 状态的 runtime
        if idempotency_key:
            existing = self.client.get_subagent_runtime(agent_id, subagent_id)
            if existing and existing.get("status") == "active":
                return RuntimeCreateResult(
                    success=True,
                    runtime_id=existing["runtime_id"],
                    created=False,
                    message="Runtime already exists",
                    status=existing.get("status", ""),
                    phase=existing.get("phase", ""),
                )

        # 创建空 runtime，所有消息由 context.read 统一读取
        runtime = self.client.create_runtime(agent_id, subagent_id, [])
        return RuntimeCreateResult(
            success=True,
            runtime_id=runtime.get("runtime_id", ""),
            created=True,
            status=runtime.get("status", "active"),
            phase=runtime.get("phase", PHASE_NEED_THINK),
        )
    
    def update_phase(
        self,
        runtime_id: str,
        expected_phase: str,
        new_phase: str,
        *,
        round_id: Optional[str] = None,
    ) -> RuntimeUpdateResult:
        """
        更新 Runtime phase (CAS)
        
        幂等性：如果已经是目标状态，返回成功
        
        Args:
            runtime_id: Runtime ID
            expected_phase: 期望的当前 phase
            new_phase: 目标 phase
            round_id: Round ID（可选）
            
        Returns:
            RuntimeUpdateResult
        """
        claim = self.client.claim_phase(runtime_id, expected_phase, new_phase, round_id)
        if claim.get("success"):
            return RuntimeUpdateResult(
                success=True,
                runtime_id=runtime_id,
                previous_value=expected_phase,
                new_value=new_phase,
            )

        # 检查当前状态（幂等）
        runtime = self.client.get_runtime(runtime_id)
        current_phase = runtime.get("phase") if runtime else "not_found"

        result = RuntimeUpdateResult(
            success=current_phase == new_phase,
            runtime_id=runtime_id,
            current_value=current_phase,
            new_value=new_phase,
            message="Already in target phase" if current_phase == new_phase else "Phase mismatch",
        )
        if not result.success:
            print(
                f"[Runtime] Phase mismatch: runtime_id={runtime_id}, "
                f"expected={expected_phase}, current={current_phase}, target={new_phase}"
            )
        return result
    
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
        
        resp = self.client.set_runtime_status(runtime_id, expected_list, new_status)
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
        result = self.client.advance_round(runtime_id)
        if not result.get("success"):
            return {"success": False, "runtime_id": runtime_id, "round_num": None}

        runtime = self.client.get_runtime(runtime_id)
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
        resp = self.client.set_runtime_summarized(runtime_id)
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
        resp = self.client.set_runtime_need_rest(runtime_id, value)
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
        return self.client.get_runtime(runtime_id)
