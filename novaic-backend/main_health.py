"""
Health Worker 启动入口 (同步版本)

健康监控，恢复超时任务和 Saga。
"""

import os
import sys
import signal
import argparse

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def main():
    from task_queue.workers.health_worker_sync import HealthWorkerSync
    
    parser = argparse.ArgumentParser(description="Health Worker (sync)")
    parser.add_argument("--queue-service-url", default="http://127.0.0.1:19997", help="Queue Service URL")
    parser.add_argument("--check-interval", type=float, default=30, help="Health check interval in seconds")
    parser.add_argument("--task-timeout", type=int, default=60, help="Task timeout in seconds")
    parser.add_argument("--saga-timeout", type=int, default=300, help="Saga timeout in seconds")
    args = parser.parse_args()
    
    queue_service_url = args.queue_service_url
    check_interval = args.check_interval
    task_timeout = args.task_timeout
    saga_timeout = args.saga_timeout
    
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
