"""
同步心跳器 - 基于线程的心跳管理

使用方式:
    with HeartbeatSync(task_id, heartbeat_fn, interval=10.0):
        # 心跳在后台线程自动运行
        do_work()
        # 退出时自动停止心跳
"""

import time
import threading
from typing import Callable, Optional
from contextlib import contextmanager


class HeartbeatSync:
    """
    同步心跳上下文管理器（基于线程）
    
    示例 1: 基本使用
        def send_heartbeat(task_id: str) -> bool:
            resp = client.post(f"/tasks/{task_id}/heartbeat")
            return resp.status_code == 200
        
        with HeartbeatSync("task-123", send_heartbeat):
            do_work()  # 同步执行
    
    示例 2: 带错误处理
        with HeartbeatSync("task-123", send_heartbeat, interval=5.0) as hb:
            do_work()
            if hb.failed:
                logger.warning(f"心跳失败 {hb.failure_count} 次")
    
    示例 3: 传递参数
        with HeartbeatSync("task-123", lambda: client.heartbeat("task-123")):
            do_work()
    """
    
    def __init__(
        self,
        identifier: str,
        heartbeat_fn: Callable[[], bool],
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
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 统计信息（线程安全）
        self._lock = threading.Lock()
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
        return self._thread is not None and self._thread.is_alive()
    
    def __enter__(self):
        """进入上下文：启动心跳"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文：停止心跳"""
        self.stop()
        return False
    
    def start(self):
        """启动心跳线程"""
        if self._thread is not None:
            raise RuntimeError("Heartbeat already started")
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,  # 守护线程，主程序退出时自动结束
            name=f"heartbeat-{self.identifier}"
        )
        self._thread.start()
    
    def stop(self, timeout: float = 2.0):
        """停止心跳线程"""
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join(timeout=timeout)
    
    def _heartbeat_loop(self):
        """心跳循环（在后台线程运行）"""
        # 首次心跳延迟，避免刚启动就发送
        if self._stop_event.wait(timeout=self.interval):
            return  # 提前停止
        
        while not self._stop_event.is_set():
            try:
                # 发送心跳
                success = self.heartbeat_fn()
                
                with self._lock:
                    if success:
                        self.success_count += 1
                        self.consecutive_failures = 0
                        self.last_success_at = time.time()
                    else:
                        self._handle_failure()
                        
            except Exception as e:
                # 心跳函数抛异常也算失败
                with self._lock:
                    self._handle_failure(e)
            
            # 检查是否达到失败阈值
            with self._lock:
                if self.fail_threshold and self.consecutive_failures >= self.fail_threshold:
                    break
            
            # 等待下一次心跳
            if self._stop_event.wait(timeout=self.interval):
                break  # stop_event 被设置，退出
    
    def _handle_failure(self, exception: Optional[Exception] = None):
        """处理心跳失败（需在锁内调用）"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_at = time.time()
        
        if self.on_failure:
            # 在锁外调用回调，避免死锁
            try:
                self.on_failure(self.consecutive_failures)
            except:
                pass  # 忽略回调异常
    
    def get_stats(self) -> dict:
        """获取统计信息（线程安全）"""
        with self._lock:
            return {
                "identifier": self.identifier,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "consecutive_failures": self.consecutive_failures,
                "last_success_at": self.last_success_at,
                "last_failure_at": self.last_failure_at,
                "is_running": self.is_running,
            }


@contextmanager
def heartbeat_sync(
    identifier: str,
    heartbeat_fn: Callable[[], bool],
    interval: float = 10.0,
    **kwargs
):
    """
    简化版同步心跳上下文管理器（函数式）
    
    用法:
        with heartbeat_sync("task-123", send_fn):
            do_work()
    """
    hb = HeartbeatSync(identifier, heartbeat_fn, interval, **kwargs)
    hb.start()
    try:
        yield hb
    finally:
        hb.stop()


# ==================== 便利工具 ====================

class HeartbeatGroupSync:
    """
    同步心跳组 - 管理多个心跳
    
    用法:
        group = HeartbeatGroupSync()
        
        with group.add("task-1", fn1):
            with group.add("task-2", fn2):
                # 两个心跳同时运行
                do_work()
    """
    
    def __init__(self):
        self.heartbeats: dict[str, HeartbeatSync] = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def add(
        self,
        identifier: str,
        heartbeat_fn: Callable[[], bool],
        interval: float = 10.0,
    ):
        """添加一个心跳"""
        with self._lock:
            if identifier in self.heartbeats:
                raise ValueError(f"Heartbeat {identifier} already exists")
            
            hb = HeartbeatSync(identifier, heartbeat_fn, interval)
            self.heartbeats[identifier] = hb
        
        hb.start()
        try:
            yield hb
        finally:
            hb.stop()
            with self._lock:
                del self.heartbeats[identifier]
    
    def stop_all(self, timeout: float = 2.0):
        """停止所有心跳"""
        with self._lock:
            threads = list(self.heartbeats.values())
        
        for hb in threads:
            hb.stop(timeout=timeout)
    
    def get_all_stats(self) -> dict[str, dict]:
        """获取所有心跳的统计信息"""
        with self._lock:
            return {
                identifier: hb.get_stats()
                for identifier, hb in self.heartbeats.items()
            }
