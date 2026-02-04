"""
异步心跳器 - 自动管理心跳的启动和停止

使用方式:
    async with Heartbeat(task_id, heartbeat_fn, interval=10.0):
        # 心跳自动在后台运行
        await do_work()
        # 退出时自动停止心跳
"""

import asyncio
import time
from typing import Callable, Optional, Awaitable
from contextlib import asynccontextmanager


class Heartbeat:
    """
    异步心跳上下文管理器
    
    示例 1: 简单使用
        async def send_heartbeat(task_id: str):
            await client.post(f"/tasks/{task_id}/heartbeat")
        
        async with Heartbeat("task-123", send_heartbeat):
            await do_work()
    
    示例 2: 带错误处理
        async with Heartbeat("task-123", send_heartbeat, interval=5.0) as hb:
            await do_work()
            if hb.failed:
                logger.warning(f"心跳失败 {hb.failure_count} 次")
    
    示例 3: 传递参数
        async with Heartbeat("task-123", lambda: client.heartbeat("task-123")):
            await do_work()
    """
    
    def __init__(
        self,
        identifier: str,
        heartbeat_fn: Callable[[], Awaitable[bool]],
        interval: float = 10.0,
        fail_threshold: Optional[int] = None,
        on_failure: Optional[Callable[[int], None]] = None,
    ):
        """
        初始化心跳器
        
        Args:
            identifier: 标识符（task_id, saga_id 等）
            heartbeat_fn: 心跳函数，返回 bool 表示成功/失败
            interval: 心跳间隔（秒）
            fail_threshold: 连续失败多少次后停止（None = 永不停止）
            on_failure: 失败回调函数，接收失败次数
        """
        self.identifier = identifier
        self.heartbeat_fn = heartbeat_fn
        self.interval = interval
        self.fail_threshold = fail_threshold
        self.on_failure = on_failure
        
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        self.last_success_at: Optional[float] = None
        self.last_failure_at: Optional[float] = None
    
    @property
    def failed(self) -> bool:
        """是否有失败记录"""
        return self.failure_count > 0
    
    @property
    def is_running(self) -> bool:
        """心跳是否正在运行"""
        return self._task is not None and not self._task.done()
    
    async def __aenter__(self):
        """进入上下文：启动心跳"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出上下文：停止心跳"""
        await self.stop()
        return False
    
    async def start(self):
        """启动心跳任务"""
        if self._task is not None:
            raise RuntimeError("Heartbeat already started")
        
        self._stop_event.clear()
        self._task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """停止心跳任务"""
        if self._task is None:
            return
        
        self._stop_event.set()
        
        # 等待任务结束（最多等 1 秒）
        try:
            await asyncio.wait_for(self._task, timeout=1.0)
        except asyncio.TimeoutError:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        # 首次心跳延迟，避免刚启动就发送
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self.interval
            )
            return  # 提前停止
        except asyncio.TimeoutError:
            pass
        
        while not self._stop_event.is_set():
            try:
                # 发送心跳
                success = await self.heartbeat_fn()
                
                if success:
                    self.success_count += 1
                    self.consecutive_failures = 0
                    self.last_success_at = time.time()
                else:
                    self._handle_failure()
                    
            except Exception as e:
                # 心跳函数抛异常也算失败
                self._handle_failure(e)
            
            # 检查是否达到失败阈值
            if self.fail_threshold and self.consecutive_failures >= self.fail_threshold:
                break
            
            # 等待下一次心跳
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval
                )
                break  # stop_event 被设置，退出
            except asyncio.TimeoutError:
                continue
    
    def _handle_failure(self, exception: Optional[Exception] = None):
        """处理心跳失败"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_at = time.time()
        
        if self.on_failure:
            self.on_failure(self.consecutive_failures)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "identifier": self.identifier,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "is_running": self.is_running,
        }


@asynccontextmanager
async def heartbeat(
    identifier: str,
    heartbeat_fn: Callable[[], Awaitable[bool]],
    interval: float = 10.0,
    **kwargs
):
    """
    简化版心跳上下文管理器（函数式）
    
    用法:
        async with heartbeat("task-123", send_fn):
            await do_work()
    """
    hb = Heartbeat(identifier, heartbeat_fn, interval, **kwargs)
    await hb.start()
    try:
        yield hb
    finally:
        await hb.stop()


# ==================== 便利工具 ====================

class HeartbeatGroup:
    """
    心跳组 - 管理多个心跳
    
    用法:
        group = HeartbeatGroup()
        
        async with group.add("task-1", fn1):
            async with group.add("task-2", fn2):
                # 两个心跳同时运行
                await do_work()
    """
    
    def __init__(self):
        self.heartbeats: dict[str, Heartbeat] = {}
    
    @asynccontextmanager
    async def add(
        self,
        identifier: str,
        heartbeat_fn: Callable[[], Awaitable[bool]],
        interval: float = 10.0,
    ):
        """添加一个心跳"""
        if identifier in self.heartbeats:
            raise ValueError(f"Heartbeat {identifier} already exists")
        
        hb = Heartbeat(identifier, heartbeat_fn, interval)
        self.heartbeats[identifier] = hb
        
        await hb.start()
        try:
            yield hb
        finally:
            await hb.stop()
            del self.heartbeats[identifier]
    
    async def stop_all(self):
        """停止所有心跳"""
        await asyncio.gather(
            *[hb.stop() for hb in self.heartbeats.values()],
            return_exceptions=True
        )
    
    def get_all_stats(self) -> dict[str, dict]:
        """获取所有心跳的统计信息"""
        return {
            identifier: hb.get_stats()
            for identifier, hb in self.heartbeats.items()
        }
