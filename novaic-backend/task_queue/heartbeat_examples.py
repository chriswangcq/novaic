"""
心跳器使用示例
"""

import asyncio
import httpx
from task_queue.heartbeat import Heartbeat, heartbeat, HeartbeatGroup


# ==================== 示例 1: 基本使用 ====================

async def example_basic():
    """基本用法：自动管理心跳"""
    
    client = httpx.AsyncClient(base_url="http://localhost:19999")
    
    async def send_heartbeat():
        """心跳函数：返回 bool 表示成功/失败"""
        try:
            resp = await client.post("/internal/tq/tasks/task-123/heartbeat")
            return resp.status_code == 200
        except:
            return False
    
    # 使用 async with，自动管理心跳
    async with Heartbeat("task-123", send_heartbeat, interval=10.0):
        print("心跳已启动（后台运行）")
        
        # 执行任务
        await asyncio.sleep(35)  # 模拟任务执行 35 秒
        # 在 10s, 20s, 30s 时自动发送 3 次心跳
        
        print("任务完成")
        # 退出时自动停止心跳
    
    await client.aclose()


# ==================== 示例 2: 获取统计信息 ====================

async def example_with_stats():
    """获取心跳统计信息"""
    
    client = httpx.AsyncClient(base_url="http://localhost:19999")
    
    async def send_heartbeat():
        resp = await client.post("/internal/tq/tasks/task-456/heartbeat")
        return resp.status_code == 200
    
    async with Heartbeat("task-456", send_heartbeat) as hb:
        await asyncio.sleep(35)
        
        # 检查心跳状态
        if hb.failed:
            print(f"⚠️  心跳失败了 {hb.failure_count} 次")
        
        # 获取详细统计
        stats = hb.get_stats()
        print(f"成功: {stats['success_count']}, 失败: {stats['failure_count']}")
    
    await client.aclose()


# ==================== 示例 3: 失败回调 ====================

async def example_with_callback():
    """心跳失败时的回调"""
    
    client = httpx.AsyncClient(base_url="http://localhost:19999")
    
    def on_failure(consecutive_failures: int):
        """失败回调"""
        print(f"⚠️  心跳连续失败 {consecutive_failures} 次")
        if consecutive_failures >= 3:
            print("❌ 连续失败过多，需要告警")
    
    async def send_heartbeat():
        resp = await client.post("/internal/tq/tasks/task-789/heartbeat")
        return resp.status_code == 200
    
    async with Heartbeat(
        "task-789",
        send_heartbeat,
        interval=5.0,
        fail_threshold=5,  # 连续失败 5 次后停止
        on_failure=on_failure
    ):
        await asyncio.sleep(30)
    
    await client.aclose()


# ==================== 示例 4: 在 TaskWorker 中使用 ====================

class TaskWorkerWithHeartbeat:
    """TaskWorker 集成心跳器"""
    
    def __init__(self, gateway_url: str):
        self.client = httpx.AsyncClient(base_url=gateway_url)
    
    async def _send_heartbeat(self, task_id: str) -> bool:
        """发送心跳"""
        try:
            resp = await self.client.post(f"/internal/tq/tasks/{task_id}/heartbeat")
            return resp.status_code == 200
        except:
            return False
    
    async def execute_task(self, task: dict):
        """执行任务（带自动心跳）"""
        task_id = task["id"]
        
        # 使用 lambda 绑定参数
        async with Heartbeat(task_id, lambda: self._send_heartbeat(task_id)):
            print(f"执行任务 {task_id}（心跳已启动）")
            
            # 执行实际任务
            try:
                result = await self._do_work(task)
                await self._complete_task(task_id, result)
            except Exception as e:
                await self._fail_task(task_id, str(e))
            
            # 退出时自动停止心跳
    
    async def _do_work(self, task: dict):
        """实际工作"""
        await asyncio.sleep(25)  # 模拟耗时任务
        return {"status": "ok"}
    
    async def _complete_task(self, task_id: str, result: dict):
        await self.client.post(f"/internal/tq/tasks/{task_id}/complete", json=result)
    
    async def _fail_task(self, task_id: str, error: str):
        await self.client.post(f"/internal/tq/tasks/{task_id}/fail", json={"error": error})


# ==================== 示例 5: 简化版（函数式） ====================

async def example_simplified():
    """使用简化版 heartbeat() 函数"""
    
    client = httpx.AsyncClient(base_url="http://localhost:19999")
    
    async def send_hb():
        resp = await client.post("/internal/tq/tasks/task-999/heartbeat")
        return resp.status_code == 200
    
    # 更简洁的写法
    async with heartbeat("task-999", send_hb, interval=10.0):
        await asyncio.sleep(35)
    
    await client.aclose()


# ==================== 示例 6: 心跳组（管理多个心跳）====================

async def example_group():
    """同时管理多个心跳"""
    
    client = httpx.AsyncClient(base_url="http://localhost:19999")
    group = HeartbeatGroup()
    
    async def send_hb_task(task_id: str):
        resp = await client.post(f"/internal/tq/tasks/{task_id}/heartbeat")
        return resp.status_code == 200
    
    async def send_hb_saga(saga_id: str):
        resp = await client.post(f"/internal/tq/sagas/{saga_id}/heartbeat")
        return resp.status_code == 200
    
    # 嵌套使用，同时管理多个心跳
    async with group.add("task-1", lambda: send_hb_task("task-1")):
        async with group.add("saga-1", lambda: send_hb_saga("saga-1")):
            print("两个心跳同时运行")
            await asyncio.sleep(35)
            
            # 查看所有心跳的统计
            stats = group.get_all_stats()
            print(stats)
    
    await client.aclose()


# ==================== 示例 7: 在实际 Worker 中的完整用法 ====================

class TaskWorkerV2Improved:
    """改进版 TaskWorker（使用心跳器）"""
    
    def __init__(self, gateway_url: str):
        self.client = httpx.AsyncClient(base_url=gateway_url)
    
    async def run(self):
        """主循环"""
        while True:
            task = await self._claim_task()
            if task:
                await self._execute_task_with_heartbeat(task)
            else:
                await asyncio.sleep(0.1)
    
    async def _claim_task(self):
        """认领任务"""
        resp = await self.client.post("/internal/tq/tasks/claim", json={
            "topics": ["llm.call", "mcp.create"],
            "worker_id": "worker-1"
        })
        return resp.json().get("task") if resp.status_code == 200 else None
    
    async def _execute_task_with_heartbeat(self, task: dict):
        """执行任务（自动心跳）"""
        task_id = task["id"]
        
        # 定义心跳函数
        async def heartbeat_fn():
            try:
                resp = await self.client.post(f"/internal/tq/tasks/{task_id}/heartbeat")
                return resp.status_code == 200
            except:
                return False
        
        # 定义失败回调
        def on_failure(count: int):
            if count >= 3:
                print(f"⚠️  任务 {task_id} 心跳连续失败 {count} 次")
        
        # 使用心跳器
        try:
            async with Heartbeat(
                task_id,
                heartbeat_fn,
                interval=10.0,
                on_failure=on_failure
            ) as hb:
                # 执行任务
                result = await self._execute_handler(task)
                await self._complete_task(task_id, result)
                
                # 可选：检查心跳状态
                if hb.failure_count > 0:
                    print(f"⚠️  任务完成，但心跳失败了 {hb.failure_count} 次")
                    
        except Exception as e:
            await self._fail_task(task_id, str(e))
    
    async def _execute_handler(self, task: dict):
        """执行 Handler"""
        resp = await self.client.post("/internal/tq/handlers/execute", json=task)
        return resp.json()
    
    async def _complete_task(self, task_id: str, result: dict):
        await self.client.post(f"/internal/tq/tasks/{task_id}/complete", json={"result": result})
    
    async def _fail_task(self, task_id: str, error: str):
        await self.client.post(f"/internal/tq/tasks/{task_id}/fail", json={"error": error})


# ==================== 运行示例 ====================

async def main():
    print("=== 示例 1: 基本使用 ===")
    # await example_basic()
    
    print("\n=== 示例 2: 统计信息 ===")
    # await example_with_stats()
    
    print("\n=== 示例 3: 失败回调 ===")
    # await example_with_callback()
    
    print("\n=== 示例 4: TaskWorker 集成 ===")
    worker = TaskWorkerWithHeartbeat("http://localhost:19999")
    task = {"id": "task-demo", "topic": "llm.call", "payload": {}}
    await worker.execute_task(task)
    
    print("\n=== 示例 5: 简化版 ===")
    # await example_simplified()
    
    print("\n=== 示例 6: 心跳组 ===")
    # await example_group()


if __name__ == "__main__":
    asyncio.run(main())
