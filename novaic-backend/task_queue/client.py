"""
TaskQueueClient - 通过 HTTP API 访问 Gateway 的 TaskQueue

提供和 TaskQueue 相同的接口，但通过 HTTP 调用 Gateway API。
用于 Worker 进程，避免直接访问数据库。
"""

import json
import os
import httpx
from typing import Optional, List, Dict, Any

from .exceptions import TaskQueueError, TaskNotFoundError
from common.config import ServiceConfig
from common.utils.time import utc_now_iso


class TaskQueueClient:
    """
    TaskQueue HTTP 客户端
    
    使用方式：
        client = TaskQueueClient("http://localhost:8716")
        
        # 和 TaskQueue 相同的接口
        task_id = client.publish("my_topic", {"key": "value"})
        task = client.claim(["my_topic"], "worker-1")
        client.complete(task["id"], {"result": "ok"})
    """
    
    def __init__(
        self,
        gateway_url: str,
        timeout: float = 30.0,
    ):
        """
        初始化客户端
        
        Args:
            gateway_url: Gateway 地址，如 "http://localhost:8716"
            timeout: 请求超时时间（秒）
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[httpx.Client] = None
    
    def _get_session(self) -> httpx.Client:
        """获取或创建 HTTP session"""
        if self._session is None:
            self._session = httpx.Client(timeout=self.timeout, trust_env=False)
        return self._session
    
    def close(self):
        """关闭 HTTP session"""
        if self._session:
            self._session.close()
    
    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        """发送 HTTP 请求"""
        session = self._get_session()
        url = f"{self.gateway_url}{path}"
        
        try:
            resp = session.request(method, url, json=json_data)
            
            # 调试：检查响应
            if not resp.content:
                raise TaskQueueError(f"Empty response from {url} (status: {resp.status_code})")
            
            try:
                data = resp.json()
            except Exception as json_err:
                raise TaskQueueError(f"Failed to parse JSON from {url}: {json_err}, content: {resp.text[:200]}")
            
            if resp.status_code >= 400:
                error_msg = data.get("detail", str(data))
                if resp.status_code == 404:
                    raise TaskNotFoundError(error_msg)
                raise TaskQueueError(f"API error ({resp.status_code}): {error_msg}")
            
            return data
                
        except httpx.HTTPError as e:
            raise TaskQueueError(f"HTTP error: {e}")
    
    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = None,
    ) -> str:
        """
        发布任务
        
        Args:
            topic: 任务主题
            payload: 任务参数
            idempotency_key: 幂等键
            max_retries: 最大重试次数
            
        Returns:
            task_id: 任务 ID
        """
        if max_retries is None:
            max_retries = ServiceConfig.DEFAULT_MAX_RETRIES
        
        data = self._request("POST", "/api/queue/tasks/publish", {
            "topic": topic,
            "payload": payload,
            "idempotency_key": idempotency_key,
            "max_retries": max_retries,
        })
        return data["task_id"]
    
    def claim(
        self,
        topics: List[str],
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        认领任务
        
        Args:
            topics: 要认领的主题列表
            worker_id: Worker 标识
            
        Returns:
            task: 任务字典，或 None
        """
        data = self._request("POST", "/api/queue/tasks/claim", {
            "topics": topics,
            "worker_id": worker_id,
        })
        return data.get("task")
    
    def complete(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        标记任务完成
        
        Args:
            task_id: 任务 ID
            result: 执行结果
            
        Returns:
            success: 是否成功
        """
        data = self._request("POST", f"/api/queue/tasks/{task_id}/complete", {
            "result": result,
        })
        return data.get("success", False)
    
    def fail(
        self,
        task_id: str,
        error: str,
        retry: bool = True,
    ) -> str:
        """
        标记任务失败
        
        Args:
            task_id: 任务 ID
            error: 错误信息
            retry: 是否允许重试
            
        Returns:
            final_status: 最终状态
        """
        data = self._request("POST", f"/api/queue/tasks/{task_id}/fail", {
            "error": error,
            "retry": retry,
        })
        return data.get("final_status", "unknown")
    
    def heartbeat(self, task_id: str) -> bool:
        """
        更新心跳
        
        Args:
            task_id: 任务 ID
            
        Returns:
            success: 是否成功
        """
        data = self._request("POST", f"/api/queue/tasks/{task_id}/heartbeat", {})
        return data.get("success", False)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情
        
        Args:
            task_id: 任务 ID
            
        Returns:
            task: 任务字典
        """
        try:
            data = self._request("GET", f"/api/queue/tasks/{task_id}", None)
            return data.get("task")
        except TaskNotFoundError:
            return None


class SagaClient:
    """
    Saga HTTP 客户端
    
    实现 SagaClientProtocol，用于 Saga Worker 进程与 Gateway 通信。
    """
    
    def __init__(
        self,
        gateway_url: str,
        timeout: float = 30.0,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[httpx.Client] = None
    
    def _get_session(self) -> httpx.Client:
        if self._session is None:
            self._session = httpx.Client(timeout=self.timeout, trust_env=False)
        return self._session
    
    def close(self):
        if self._session:
            self._session.close()
    
    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        session = self._get_session()
        url = f"{self.gateway_url}{path}"
        
        try:
            resp = session.request(method, url, json=json_data)
            
            # 检查空响应
            if not resp.text or not resp.text.strip():
                raise TaskQueueError(f"Empty response from {url} (status: {resp.status_code})")
            
            try:
                data = resp.json()
            except Exception as json_err:
                raise TaskQueueError(f"Failed to parse JSON from {url}: {json_err}, content: {resp.text[:200]}")
            
            if resp.status_code >= 400:
                error_msg = data.get("detail", str(data))
                raise TaskQueueError(f"API error ({resp.status_code}): {error_msg}")
            
            return data
                
        except httpx.HTTPError as e:
            raise TaskQueueError(f"HTTP error: {e}")
    
    def start(
        self,
        saga_type: str,
        context: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> str:
        """创建 Saga"""
        data = self._request("POST", "/api/queue/sagas/start", {
            "saga_type": saga_type,
            "context": context,
            "idempotency_key": idempotency_key,
        })
        return data["saga_id"]
    
    def claim(
        self,
        saga_types: List[str],
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """认领 Saga"""
        data = self._request("POST", "/api/queue/sagas/claim", {
            "saga_types": saga_types,
            "worker_id": worker_id,
        })
        return data.get("saga")
    
    def heartbeat(self, saga_id: str) -> bool:
        """更新心跳"""
        data = self._request("POST", f"/api/queue/sagas/{saga_id}/heartbeat", {})
        return data.get("success", False)
    
    def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga 状态"""
        try:
            data = self._request("GET", f"/api/queue/sagas/{saga_id}", None)
            return data.get("saga")
        except TaskQueueError as e:
            if "404" in str(e):
                return None
            raise
    
    # 兼容旧接口
    def get_saga(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga 状态 (兼容)"""
        return self.get(saga_id)
    
    def update_progress(
        self,
        saga_id: str,
        current_step: int,
        step_results: Dict[str, Any],
        status: str = "running",
    ):
        """更新 Saga 进度"""
        self._request("POST", f"/api/queue/sagas/{saga_id}/progress", {
            "current_step": current_step,
            "step_results": step_results,
            "status": status,
        })
    
    def mark_completed(
        self,
        saga_id: str,
        step_results: Dict[str, Any],
    ):
        """标记 Saga 完成"""
        self._request("POST", f"/api/queue/sagas/{saga_id}/complete", {
            "step_results": step_results,
        })
    
    def mark_failed(
        self,
        saga_id: str,
        error: str,
    ):
        """标记 Saga 失败"""
        self._request("POST", f"/api/queue/sagas/{saga_id}/fail", {
            "error": error,
        })


class GatewayInternalClient:
    """
    Gateway Internal API 客户端

    供非 Gateway 代码调用 /internal/* 接口，避免直接访问 DB。
    """

    def __init__(
        self,
        gateway_url: str,
        timeout: float = 30.0,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[httpx.Client] = None

    def _get_session(self) -> httpx.Client:
        if self._session is None:
            self._session = httpx.Client(timeout=self.timeout, trust_env=False)
        return self._session

    def close(self):
        if self._session:
            self._session.close()

    def _request(self, method: str, path: str, json_data: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        session = self._get_session()
        url = f"{self.gateway_url}{path}"
        try:
            resp = session.request(method, url, json=json_data, params=params)
            
            # 检查空响应
            if not resp.text or not resp.text.strip():
                raise TaskQueueError(f"Empty response from {url} (status: {resp.status_code})")
            
            try:
                data = resp.json()
            except Exception as json_err:
                raise TaskQueueError(f"Failed to parse JSON from {url}: {json_err}, content: {resp.text[:200]}")
            
            if resp.status_code >= 400:
                error_msg = data.get("detail", str(data))
                raise TaskQueueError(f"API error ({resp.status_code}): {error_msg}")
            return data
        except httpx.HTTPError as e:
            raise TaskQueueError(f"HTTP error: {e}")

    # ---------- Runtime ----------
    def get_runtime(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        data = self._request("GET", f"/internal/runtimes/{runtime_id}", None)
        return data.get("runtime") if isinstance(data, dict) and "runtime" in data else data

    def create_runtime(self, agent_id: str, subagent_id: str, initial_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload = {
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "initial_context": initial_context or [],
        }
        return self._request("POST", "/internal/runtimes", payload)

    def get_or_create_runtime(self, agent_id: str, subagent_id: str, initial_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """原子操作：获取或创建 active runtime。
        
        Returns:
            dict with runtime fields + just_created: bool
        """
        payload = {
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "initial_context": initial_context or [],
        }
        return self._request("POST", "/internal/runtimes/get-or-create", payload)

    def update_runtime(self, runtime_id: str, data: Dict[str, Any]) -> dict:
        return self._request("PATCH", f"/internal/runtimes/{runtime_id}", data)

    # DEPRECATED: claim_phase 已删除，Saga 步骤替代 phase 状态

    def advance_round(self, runtime_id: str, expected_round_num: Optional[int] = None) -> dict:
        payload = {"expected_round_num": expected_round_num} if expected_round_num is not None else {}
        return self._request("POST", f"/internal/runtimes/{runtime_id}/advance", payload)

    def get_subagent_runtime(self, agent_id: str, subagent_id: str) -> Optional[Dict[str, Any]]:
        data = self._request("GET", f"/internal/runtimes/subagent/{agent_id}/{subagent_id}", None)
        return data.get("runtime")

    def append_context(self, runtime_id: str, message: Dict[str, Any], message_type: str, round_id: Optional[str], idempotency_key: Optional[str]) -> dict:
        payload = {
            "message": message,
            "message_type": message_type,
            "round_id": round_id,
            "idempotency_key": idempotency_key,
        }
        return self._request("POST", f"/internal/runtimes/{runtime_id}/context/append", payload)

    # ---------- Messages ----------
    def claim_message(self, message_id: str) -> dict:
        return self._request("POST", f"/internal/messages/{message_id}/claim", {})

    def has_new_messages(self, agent_id: str) -> dict:
        return self._request("GET", f"/internal/messages/has-new/{agent_id}", None)

    def get_unread_sent_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/internal/messages/unread-sent/{agent_id}", None)
        return data.get("messages", [])

    def mark_messages_read(self, message_ids: List[str]) -> dict:
        return self._request("PATCH", "/internal/messages/mark-read", {"message_ids": message_ids})

    # ---------- SubAgents ----------
    def wake_subagent(self, agent_id: str, subagent_id: str, target_status: str = "awaking") -> dict:
        return self._request(
            "POST",
            f"/internal/subagents/{agent_id}/{subagent_id}/wake?target_status={target_status}",
            {},
        )

    def set_subagent_awake(self, agent_id: str, subagent_id: str) -> dict:
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/awake", {})

    def set_subagent_sleeping(self, agent_id: str, subagent_id: str) -> dict:
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/sleeping", {})

    def get_subagent(self, agent_id: str, subagent_id: str) -> dict:
        return self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}", None)

    def get_subagent_status(self, agent_id: str, subagent_id: str) -> dict:
        return self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}/status", None)

    # ---------- Tools Server ----------
    def create_runtime_tools(self, runtime_id: str, agent_id: str, subagent_id: str, ports: dict = None) -> dict:
        """在 Tools Server 创建 Runtime 工具上下文"""
        tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
        with httpx.Client(timeout=30.0, trust_env=False) as client:
            resp = client.post(f"{tools_server_url}/internal/runtimes", json={
                "runtime_id": runtime_id,
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "ports": ports or {},
            })
            resp.raise_for_status()
            return resp.json()

    def destroy_runtime_tools(self, runtime_id: str) -> dict:
        """在 Tools Server 删除 Runtime 工具上下文"""
        tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
        with httpx.Client(timeout=ServiceConfig.HTTP_TIMEOUT_SHORT, trust_env=False) as client:
            resp = client.delete(f"{tools_server_url}/internal/runtimes/{runtime_id}")
            resp.raise_for_status()
            return resp.json()

    def list_runtime_tools(self, runtime_id: str) -> dict:
        """获取 Runtime 的工具列表"""
        tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
        with httpx.Client(timeout=ServiceConfig.HTTP_TIMEOUT_SHORT, trust_env=False) as client:
            resp = client.get(f"{tools_server_url}/internal/runtimes/{runtime_id}/tools")
            resp.raise_for_status()
            return resp.json()

    def call_runtime_tool(self, runtime_id: str, tool_name: str, arguments: dict) -> dict:
        """调用 Runtime 的工具"""
        tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
        with httpx.Client(timeout=30.0, trust_env=False) as client:
            resp = client.post(f"{tools_server_url}/internal/runtimes/{runtime_id}/tools/call", json={
                "name": tool_name,
                "arguments": arguments,
            })
            resp.raise_for_status()
            return resp.json()

    # 向后兼容别名
    def create_aggregate_mcp(self, agent_id: str, runtime_id: str, subagent_id: str) -> dict:
        """向后兼容：创建 Runtime 工具上下文"""
        return self.create_runtime_tools(runtime_id, agent_id, subagent_id)

    def destroy_aggregate_mcp(self, agent_id: str, runtime_id: str) -> dict:
        """向后兼容：删除 Runtime 工具上下文"""
        return self.destroy_runtime_tools(runtime_id)

    # ---------- Runtime flags ----------
    def set_runtime_summarized(self, runtime_id: str) -> dict:
        return self._request("POST", f"/internal/runtimes/{runtime_id}/summarized", {})
    
    def set_runtime_hot_cold_summary(self, runtime_id: str, hot_summary: str, cold_summary: str) -> dict:
        """Set both hot and cold summaries for a runtime."""
        return self._request("POST", f"/internal/runtimes/{runtime_id}/hot-cold-summary", {
            "hot_summary": hot_summary,
            "cold_summary": cold_summary,
        })

    def set_runtime_need_rest(self, runtime_id: str, value: bool) -> dict:
        return self._request("POST", f"/internal/runtimes/{runtime_id}/need-rest", {"value": value})

    def set_runtime_status(self, runtime_id: str, expected_status: List[str], new_status: str, error: Optional[str] = None) -> dict:
        payload: Dict[str, Any] = {
            "expected_status": expected_status,
            "new_status": new_status,
        }
        if error:
            payload["error"] = error
        return self._request("POST", f"/internal/runtimes/{runtime_id}/set-status", payload)
    
    # ---------- Scheduler (Wake) ----------
    def get_due_for_wake(self) -> list:
        """Get sleeping SubAgents whose wake_at has passed."""
        data = self._request("GET", "/internal/subagents/due-wake", None)
        return data.get("subagents", [])
    
    def inject_wake_message(self, agent_id: str, metadata: dict = None) -> dict:
        """Inject a SYSTEM_WAKE message to trigger scheduled wake."""
        return self._request("POST", "/internal/messages/inject-wake", {
            "agent_id": agent_id,
            "metadata": metadata or {},
        })

    # ---------- Messages (Watchdog) ----------
    def claim_and_prepare_message(self) -> Optional[Dict[str, Any]]:
        """Claim 并准备一条 sending 消息"""
        data = self._request("POST", "/internal/messages/claim-and-prepare", {})
        return data.get("message")
    
    # ---------- Execution Log Broadcast (Worker -> Gateway -> SSE) ----------
    def broadcast_log(
        self,
        agent_id: str,
        log_type: str = None,
        data: Dict[str, Any] = None,
        timestamp: Optional[str] = None,
        *,
        subagent_id: str = "main",
        kind: str = None,
        status: str = "complete",
        event_key: str = None,
        input_data: Dict[str, Any] = None,
        result_data: Dict[str, Any] = None,
    ) -> bool:
        """
        向 Gateway 发送执行日志，Gateway 会写入 DB 并推给 SSE 订阅者（Execute Log 窗口）。
        Worker 同步调用，无需 async。
        
        Args:
            agent_id: Agent ID
            log_type: 日志类型（保留兼容）
            data: 日志数据（保留兼容）
            timestamp: 时间戳
            subagent_id: SubAgent ID，默认 "main"
            kind: 事件类型（think/tool/message 等）
            status: 状态（running/complete）
            event_key: 事件唯一标识（如 "think:runtime_id:round_id"）
            input_data: 输入数据
            result_data: 结果数据
        """
        payload = {
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "timestamp": timestamp or utc_now_iso(),
        }
        
        # 兼容旧格式
        if log_type:
            payload["type"] = log_type
        if data:
            payload["data"] = data
            
        # 新事件模型字段
        if kind:
            payload["kind"] = kind
        if status:
            payload["status"] = status
        if event_key:
            payload["event_key"] = event_key
        if input_data:
            payload["input_data"] = input_data
        if result_data:
            payload["result_data"] = result_data
        
        try:
            self._request("POST", "/api/logs/broadcast", payload)
            return True
        except Exception:
            return False

    # ---------- Task Queue Recovery ----------
    def recover_all(self, task_timeout: int = 60, saga_timeout: int = 120) -> Dict[str, Any]:
        """恢复所有超时的 Task 和 Saga"""
        return self._request("POST", "/internal/tq/recover/all", None, params={
            "task_timeout": task_timeout,
            "saga_timeout": saga_timeout,
        })

    # ---------- HRL and Summary Lock Operations (v24) ----------
    def get_hrl(self, agent_id: str, subagent_id: str) -> dict:
        """Get Hot Runtime List for a SubAgent.
        
        Returns:
            dict with 'hrl' (list) and 'length' (int)
        """
        return self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}/hrl", None)

    def add_to_hrl(self, agent_id: str, subagent_id: str, runtime_id: str) -> dict:
        """Add a runtime to HRL.
        
        Returns:
            dict with 'success', 'hrl', 'length'
        """
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/hrl/add", {
            "runtime_id": runtime_id
        })

    def get_summary_lock(self, agent_id: str, subagent_id: str) -> dict:
        """Get summary_lock status for a SubAgent.
        
        Returns:
            dict with 'summary_lock' (0 or 1)
        """
        return self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}/summary-lock", None)

    def acquire_summary_lock(self, agent_id: str, subagent_id: str) -> dict:
        """Try to acquire summary_lock using CAS.
        
        Returns:
            dict with 'success' (bool)
        """
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/summary-lock/acquire", {})

    def release_summary_lock(self, agent_id: str, subagent_id: str) -> dict:
        """Release summary_lock.
        
        Returns:
            dict with 'success' (bool)
        """
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/summary-lock/release", {})

    def atomic_merge_history(
        self,
        agent_id: str,
        subagent_id: str,
        new_history: str,
        remove_runtime_ids: List[str]
    ) -> dict:
        """Atomically update historical_summary and remove runtimes from HRL.
        
        Returns:
            dict with 'success' (bool)
        """
        return self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/merge-history", {
            "new_history": new_history,
            "remove_runtime_ids": remove_runtime_ids,
        })

    # ---------- Runtime Batch Operations (v24) ----------
    def get_runtimes_by_ids(self, runtime_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple runtimes by IDs (for context building).
        
        Args:
            runtime_ids: List of runtime IDs to fetch
            
        Returns:
            List of runtime dicts with summaries, in input order
        """
        if not runtime_ids:
            return []
        
        data = self._request("POST", "/internal/runtimes/batch", {
            "runtime_ids": runtime_ids
        })
        return data.get("runtimes", [])

    # ---------- Drive (Phase 3) ----------
    def get_agent_drive(self, agent_id: str) -> dict:
        """Get agent drive configuration (auto-creates default if missing)."""
        return self._request("GET", f"/internal/agents/{agent_id}/drive", None)

    def get_notebook_summary(self, agent_id: str) -> dict:
        """Get notebook summary for an agent."""
        return self._request("GET", f"/internal/agents/{agent_id}/notebook-summary", None)

    def get_agent_state(self, agent_id: str) -> dict:
        """Get agent state (sleep/wake status, last_active_at, etc)."""
        # agent_state is stored via the subagent main endpoint
        try:
            main_subagent = self._request("GET", f"/internal/subagents/{agent_id}/main", None)
            return {
                "status": main_subagent.get("status"),
                "last_active_at": main_subagent.get("updated_at"),
                "wake_triggers": main_subagent.get("wake_triggers"),
                "handoff_notes": main_subagent.get("handoff_notes"),
            }
        except Exception:
            return {}

    # ---------- Drive Lifecycle (Phase 4) ----------
    def increment_drive_interaction(self, agent_id: str) -> dict:
        """Increment agent drive interaction count and reset no-response streak."""
        return self._request("POST", f"/internal/agents/{agent_id}/drive/increment-interaction", {})

    def get_agent_info(self, agent_id: str) -> dict:
        """Get basic agent info (name, os) for system prompt."""
        try:
            return self._request("GET", f"/internal/agents/{agent_id}/info", None)
        except Exception:
            return {"name": "NovAIC Agent", "os": "unknown"}

    def get_agent_skills(self, agent_id: str) -> dict:
        """Get assigned skills for an agent."""
        try:
            return self._request("GET", f"/api/agents/{agent_id}/skills", None)
        except Exception:
            return {"skills": []}
    
    def match_skills_for_task(self, task: str, max_skills: int = 3) -> dict:
        """
        Match skills based on task description using keywords.
        
        Args:
            task: Task description to match against
            max_skills: Maximum number of skills to return
            
        Returns:
            dict with matched_skills list
        """
        try:
            return self._request("POST", "/api/skills/match", {
                "task": task,
                "max_skills": max_skills,
            })
        except Exception as e:
            print(f"[client] Failed to match skills for task: {e}")
            return {"matched_skills": []}

    # ========================================
    # Self-Drive System Methods
    # ========================================
    
    def get_main_subagent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取 main subagent 信息"""
        try:
            return self._request("GET", f"/internal/subagents/{agent_id}/main", None)
        except Exception:
            return None
    
    def get_quadrant_task_board(self, agent_id: str) -> Dict[str, Any]:
        """获取四象限任务看板"""
        # 需要先获取 runtime_id，这里使用 agent_id 作为 runtime_id 的一部分
        # 实际上应该通过 subagent 获取，这里简化处理
        try:
            # 尝试获取 main subagent
            subagent = self.get_main_subagent(agent_id)
            if subagent:
                runtime_id = f"{agent_id}:{subagent.get('id', 'main')}:0"
            else:
                runtime_id = f"{agent_id}:main:0"
            
            resp = self._request("GET", f"/internal/rt/{runtime_id}/quadrant-tasks/board")
            return resp
        except Exception as e:
            print(f"[client] get_quadrant_task_board failed: {e}")
            return {"q1": {"count": 0, "tasks": []}, "q2": {"count": 0, "tasks": []}, "q3": {"count": 0, "tasks": []}, "q4": {"count": 0, "tasks": []}}
    
    def get_growth_log(self, agent_id: str, limit: int = 10, category: str = None) -> Dict[str, Any]:
        """获取成长日志"""
        try:
            subagent = self.get_main_subagent(agent_id)
            if subagent:
                runtime_id = f"{agent_id}:{subagent.get('id', 'main')}:0"
            else:
                runtime_id = f"{agent_id}:main:0"
            
            params = {"limit": limit}
            if category:
                params["category"] = category
            
            resp = self._request("GET", f"/internal/rt/{runtime_id}/self-drive/growth-log", params=params)
            return resp
        except Exception as e:
            print(f"[client] get_growth_log failed: {e}")
            return {"entries": [], "total_count": 0}
    
    def get_drive_config(self, agent_id: str) -> Dict[str, Any]:
        """获取内驱力配置"""
        try:
            subagent = self.get_main_subagent(agent_id)
            if subagent:
                runtime_id = f"{agent_id}:{subagent.get('id', 'main')}:0"
            else:
                runtime_id = f"{agent_id}:main:0"
            
            resp = self._request("GET", f"/internal/rt/{runtime_id}/self-drive/config")
            return resp
        except Exception as e:
            print(f"[client] get_drive_config failed: {e}")
            return {
                "success": True,
                "config": {
                    "core_value": "为用户服务是第一目标",
                    "curiosity": 0.7,
                    "knowledge": 0.6,
                    "growth": 0.5,
                    "proactive_level": 0.5,
                    "reflection_frequency": "daily",
                }
            }
    
    def get_self_drive_state(self, agent_id: str) -> Dict[str, Any]:
        """获取完整的自驱系统状态"""
        try:
            subagent = self.get_main_subagent(agent_id)
            if subagent:
                runtime_id = f"{agent_id}:{subagent.get('id', 'main')}:0"
            else:
                runtime_id = f"{agent_id}:main:0"
            
            resp = self._request("GET", f"/internal/rt/{runtime_id}/self-drive/state")
            return resp
        except Exception as e:
            print(f"[client] get_self_drive_state failed: {e}")
            return {"success": False, "error": str(e)}