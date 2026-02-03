"""
TaskQueueClient - 通过 HTTP API 访问 Gateway 的 TaskQueue

提供和 TaskQueue 相同的接口，但通过 HTTP 调用 Gateway API。
用于 Worker 进程，避免直接访问数据库。
"""

import json
import aiohttp
from typing import Optional, List, Dict, Any

from .exceptions import TaskQueueError, TaskNotFoundError


class TaskQueueClient:
    """
    TaskQueue HTTP 客户端
    
    使用方式：
        client = TaskQueueClient("http://localhost:8716")
        
        # 和 TaskQueue 相同的接口
        task_id = await client.publish("my_topic", {"key": "value"})
        task = await client.claim(["my_topic"], "worker-1")
        await client.complete(task["id"], {"result": "ok"})
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
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self):
        """关闭 HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        """发送 HTTP 请求"""
        session = await self._get_session()
        url = f"{self.gateway_url}{path}"
        
        try:
            async with session.request(method, url, json=json_data) as resp:
                data = await resp.json()
                
                if resp.status >= 400:
                    error_msg = data.get("detail", str(data))
                    if resp.status == 404:
                        raise TaskNotFoundError(error_msg)
                    raise TaskQueueError(f"API error ({resp.status}): {error_msg}")
                
                return data
                
        except aiohttp.ClientError as e:
            raise TaskQueueError(f"HTTP error: {e}")
    
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
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
        data = await self._request("POST", "/internal/tq/tasks/publish", {
            "topic": topic,
            "payload": payload,
            "idempotency_key": idempotency_key,
            "max_retries": max_retries,
        })
        return data["task_id"]
    
    async def claim(
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
        data = await self._request("POST", "/internal/tq/tasks/claim", {
            "topics": topics,
            "worker_id": worker_id,
        })
        return data.get("task")
    
    async def complete(
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
        data = await self._request("POST", f"/internal/tq/tasks/{task_id}/complete", {
            "result": result,
        })
        return data.get("success", False)
    
    async def fail(
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
        data = await self._request("POST", f"/internal/tq/tasks/{task_id}/fail", {
            "error": error,
            "retry": retry,
        })
        return data.get("final_status", "unknown")
    
    async def heartbeat(self, task_id: str) -> bool:
        """
        更新心跳
        
        Args:
            task_id: 任务 ID
            
        Returns:
            success: 是否成功
        """
        data = await self._request("POST", f"/internal/tq/tasks/{task_id}/heartbeat", {})
        return data.get("success", False)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务详情
        
        Args:
            task_id: 任务 ID
            
        Returns:
            task: 任务字典
        """
        try:
            data = await self._request("GET", f"/internal/tq/tasks/{task_id}", None)
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
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
    ) -> dict:
        session = await self._get_session()
        url = f"{self.gateway_url}{path}"
        
        try:
            async with session.request(method, url, json=json_data) as resp:
                data = await resp.json()
                
                if resp.status >= 400:
                    error_msg = data.get("detail", str(data))
                    raise TaskQueueError(f"API error ({resp.status}): {error_msg}")
                
                return data
                
        except aiohttp.ClientError as e:
            raise TaskQueueError(f"HTTP error: {e}")
    
    async def start(
        self,
        saga_type: str,
        context: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> str:
        """创建 Saga"""
        data = await self._request("POST", "/internal/tq/sagas/start", {
            "saga_type": saga_type,
            "context": context,
            "idempotency_key": idempotency_key,
        })
        return data["saga_id"]
    
    async def claim(
        self,
        saga_types: List[str],
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """认领 Saga"""
        data = await self._request("POST", "/internal/tq/sagas/claim", {
            "saga_types": saga_types,
            "worker_id": worker_id,
        })
        return data.get("saga")
    
    async def heartbeat(self, saga_id: str) -> bool:
        """更新心跳"""
        data = await self._request("POST", f"/internal/tq/sagas/{saga_id}/heartbeat", {})
        return data.get("success", False)
    
    async def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga 状态"""
        try:
            data = await self._request("GET", f"/internal/tq/sagas/{saga_id}", None)
            return data.get("saga")
        except TaskQueueError as e:
            if "404" in str(e):
                return None
            raise
    
    # 兼容旧接口
    async def get_saga(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga 状态 (兼容)"""
        return await self.get(saga_id)
    
    async def update_progress(
        self,
        saga_id: str,
        current_step: int,
        step_results: Dict[str, Any],
        status: str = "running",
    ):
        """更新 Saga 进度"""
        await self._request("POST", f"/internal/tq/sagas/{saga_id}/progress", {
            "current_step": current_step,
            "step_results": step_results,
            "status": status,
        })
    
    async def mark_completed(
        self,
        saga_id: str,
        step_results: Dict[str, Any],
    ):
        """标记 Saga 完成"""
        await self._request("POST", f"/internal/tq/sagas/{saga_id}/complete", {
            "step_results": step_results,
        })
    
    async def mark_failed(
        self,
        saga_id: str,
        error: str,
    ):
        """标记 Saga 失败"""
        await self._request("POST", f"/internal/tq/sagas/{saga_id}/fail", {
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
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, method: str, path: str, json_data: Optional[dict] = None) -> dict:
        session = await self._get_session()
        url = f"{self.gateway_url}{path}"
        try:
            async with session.request(method, url, json=json_data) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    error_msg = data.get("detail", str(data))
                    raise TaskQueueError(f"API error ({resp.status}): {error_msg}")
                return data
        except aiohttp.ClientError as e:
            raise TaskQueueError(f"HTTP error: {e}")

    # ---------- Runtime ----------
    async def get_runtime(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/internal/runtimes/{runtime_id}", None)
        return data.get("runtime") if isinstance(data, dict) and "runtime" in data else data

    async def create_runtime(self, agent_id: str, subagent_id: str, initial_context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload = {
            "agent_id": agent_id,
            "subagent_id": subagent_id,
            "initial_context": initial_context or [],
        }
        return await self._request("POST", "/internal/runtimes", payload)

    async def update_runtime(self, runtime_id: str, data: Dict[str, Any]) -> dict:
        return await self._request("PATCH", f"/internal/runtimes/{runtime_id}", data)

    async def claim_phase(self, runtime_id: str, expected_phase: str, new_phase: str, round_id: Optional[str] = None) -> dict:
        payload: Dict[str, Any] = {
            "expected_phase": expected_phase,
            "new_phase": new_phase,
        }
        if round_id:
            payload["round_id"] = round_id
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/claim-phase", payload)

    async def advance_round(self, runtime_id: str, expected_round_num: Optional[int] = None) -> dict:
        payload = {"expected_round_num": expected_round_num} if expected_round_num is not None else {}
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/advance", payload)

    async def get_subagent_runtime(self, agent_id: str, subagent_id: str) -> Optional[Dict[str, Any]]:
        data = await self._request("GET", f"/internal/runtimes/subagent/{agent_id}/{subagent_id}", None)
        return data.get("runtime")

    async def append_context(self, runtime_id: str, message: Dict[str, Any], message_type: str, round_id: Optional[str], idempotency_key: Optional[str]) -> dict:
        payload = {
            "message": message,
            "message_type": message_type,
            "round_id": round_id,
            "idempotency_key": idempotency_key,
        }
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/context/append", payload)

    # ---------- Messages ----------
    async def claim_message(self, message_id: str) -> dict:
        return await self._request("POST", f"/internal/messages/{message_id}/claim", {})

    async def has_new_messages(self, agent_id: str) -> dict:
        return await self._request("GET", f"/internal/messages/has-new/{agent_id}", None)

    async def get_unread_sent_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        data = await self._request("GET", f"/internal/messages/unread-sent/{agent_id}", None)
        return data.get("messages", [])

    async def mark_messages_read(self, message_ids: List[str]) -> dict:
        return await self._request("PATCH", "/internal/messages/mark-read", {"message_ids": message_ids})

    # ---------- SubAgents ----------
    async def wake_subagent(self, agent_id: str, subagent_id: str, target_status: str = "awaking") -> dict:
        return await self._request(
            "POST",
            f"/internal/subagents/{agent_id}/{subagent_id}/wake?target_status={target_status}",
            {},
        )

    async def set_subagent_awake(self, agent_id: str, subagent_id: str) -> dict:
        return await self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/awake", {})

    async def set_subagent_sleeping(self, agent_id: str, subagent_id: str) -> dict:
        return await self._request("POST", f"/internal/subagents/{agent_id}/{subagent_id}/sleeping", {})

    async def get_subagent(self, agent_id: str, subagent_id: str) -> dict:
        return await self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}", None)

    async def get_subagent_status(self, agent_id: str, subagent_id: str) -> dict:
        return await self._request("GET", f"/internal/subagents/{agent_id}/{subagent_id}/status", None)

    # ---------- MCP ----------
    async def create_aggregate_mcp(self, agent_id: str, runtime_id: str, subagent_id: str) -> dict:
        return await self._request("POST", "/internal/mcp/aggregate", {
            "agent_id": agent_id,
            "runtime_id": runtime_id,
            "subagent_id": subagent_id,
        })

    async def destroy_aggregate_mcp(self, agent_id: str, runtime_id: str) -> dict:
        return await self._request("DELETE", f"/internal/mcp/aggregate/{agent_id}/{runtime_id}", None)

    # ---------- Runtime flags ----------
    async def set_runtime_summarized(self, runtime_id: str) -> dict:
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/summarized", {})

    async def set_runtime_need_rest(self, runtime_id: str, value: bool) -> dict:
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/need-rest", {"value": value})

    async def set_runtime_status(self, runtime_id: str, expected_status: List[str], new_status: str, error: Optional[str] = None) -> dict:
        payload: Dict[str, Any] = {
            "expected_status": expected_status,
            "new_status": new_status,
        }
        if error:
            payload["error"] = error
        return await self._request("POST", f"/internal/runtimes/{runtime_id}/set-status", payload)
