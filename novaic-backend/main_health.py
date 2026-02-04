"""
Health Worker 启动入口 (同步版本)

健康监控，恢复超时任务和 Saga。
"""

import os
import sys
import signal

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def main():
    from task_queue.workers.health_worker_sync import HealthWorkerSync
    
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", "http://127.0.0.1:19997")
    check_interval = float(os.environ.get("HEALTH_CHECK_INTERVAL", "30"))
    task_timeout = int(os.environ.get("TASK_TIMEOUT", "60"))
    saga_timeout = int(os.environ.get("SAGA_TIMEOUT", "120"))
    
    worker = HealthWorkerSync(
        queue_service_url=queue_service_url,
        check_interval=check_interval,
        task_timeout=task_timeout,
        saga_timeout=saga_timeout,
    )
    
    # 信号处理
    def shutdown_handler(signum, frame):
        print("[main_health] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[main_health] Starting HealthWorker (sync)...")
    print(f"[main_health] Queue Service URL: {queue_service_url}")
    print(f"[main_health] Check interval: {check_interval}s")
    print(f"[main_health] Task timeout: {task_timeout}s")
    print(f"[main_health] Saga timeout: {saga_timeout}s")
    
    worker.run()
    
    print("[main_health] Shutdown complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
