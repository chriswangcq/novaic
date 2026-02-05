"""
Task Worker 启动入口 (同步版本)

通用任务执行器，处理所有 task_queue 中的任务。
"""

import os
import sys
import signal
import argparse

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

# Import unified configuration
from common.config import ServiceConfig


def main():
    from task_queue.workers.task_worker_sync import TaskWorkerSync
    from task_queue.handlers import get_all_topics, validate_topic_registration
    
    parser = argparse.ArgumentParser(description="Task Worker (sync)")
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--queue-service-url", default=ServiceConfig.QUEUE_SERVICE_URL, help="Queue Service URL")
    parser.add_argument("--num-workers", type=int, default=ServiceConfig.NUM_WORKERS, help="Number of workers")
    args = parser.parse_args()
    
    gateway_url = args.gateway_url
    queue_service_url = args.queue_service_url
    
    # 验证 Topic 注册一致性
    validation = validate_topic_registration()
    if not validation["valid"]:
        print(f"[WARNING] Topic validation failed: {validation}")
    
    # 自动从 handlers 注册表获取所有 topics
    topics = get_all_topics()
    print(f"[task-worker] Subscribed to {len(topics)} topics: {sorted(topics)}")
    
    worker = TaskWorkerSync(
        topics=topics,
        queue_service_url=queue_service_url,
        gateway_url=gateway_url,
    )
    
    # 信号处理
    def shutdown_handler(signum, frame):
        print("[main_task] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[main_task] Starting TaskWorker (sync)...")
    print(f"[main_task] Gateway URL: {gateway_url}")
    print(f"[main_task] Queue Service URL: {queue_service_url}")
    print(f"[main_task] Topics: {topics}")
    
    worker.run()
    
    print("[main_task] Shutdown complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
