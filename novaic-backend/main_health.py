"""
Health Worker v2 启动入口

健康监控，恢复超时任务和 Saga。
"""

import asyncio
import os
import sys
import signal

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


async def main():
    from task_queue.workers.health_worker_v2 import HealthWorkerV2
    
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    check_interval = float(os.environ.get("HEALTH_CHECK_INTERVAL", "30"))
    task_timeout = int(os.environ.get("TASK_TIMEOUT", "60"))
    saga_timeout = int(os.environ.get("SAGA_TIMEOUT", "120"))
    
    worker = HealthWorkerV2(
        gateway_url=gateway_url,
        check_interval=check_interval,
        task_timeout=task_timeout,
        saga_timeout=saga_timeout,
    )
    
    # 信号处理
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        print("[main_health] Received shutdown signal")
        asyncio.create_task(worker.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler)
    
    print(f"[main_health] Starting HealthWorker v2...")
    print(f"[main_health] Gateway URL: {gateway_url}")
    print(f"[main_health] Check interval: {check_interval}s")
    print(f"[main_health] Task timeout: {task_timeout}s")
    print(f"[main_health] Saga timeout: {saga_timeout}s")
    
    await worker.run()
    
    print("[main_health] Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
