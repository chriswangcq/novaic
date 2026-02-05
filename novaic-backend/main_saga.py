"""
Saga Worker 启动入口 (同步版本)

执行 Saga 流程编排。
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
    from task_queue.workers.saga_worker_sync import SagaWorkerSync
    from task_queue.sagas import get_all_saga_definitions, get_all_saga_types, validate_saga_registration
    
    parser = argparse.ArgumentParser(description="Saga Worker (sync)")
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--queue-service-url", default=ServiceConfig.QUEUE_SERVICE_URL, help="Queue Service URL")
    parser.add_argument("--max-concurrent", type=int, default=ServiceConfig.MAX_CONCURRENT_SAGAS, help="Max concurrent sagas")
    args = parser.parse_args()
    
    gateway_url = args.gateway_url
    queue_service_url = args.queue_service_url
    max_concurrent = args.max_concurrent
    
    # 验证并获取所有已注册的 Saga 类型（自动发现）
    validate_saga_registration()
    saga_types = get_all_saga_types()
    
    worker = SagaWorkerSync(
        saga_types=saga_types,
        gateway_url=gateway_url,
        queue_service_url=queue_service_url,
        poll_interval=ServiceConfig.POLL_INTERVAL,
        max_concurrent=max_concurrent,
    )
    
    # 注册 Saga 定义
    for saga_def in get_all_saga_definitions():
        worker.register_definition(saga_def.name, saga_def)
        print(f"[main_saga] Registered: {saga_def.name} ({len(saga_def.steps)} steps)")
    
    # 信号处理
    def shutdown_handler(signum, frame):
        print("[main_saga] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[main_saga] Starting SagaWorker (sync)...")
    print(f"[main_saga] Gateway URL: {gateway_url}")
    print(f"[main_saga] Queue Service URL: {queue_service_url}")
    print(f"[main_saga] Saga types: {saga_types}")
    
    worker.run()
    
    print("[main_saga] Shutdown complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
