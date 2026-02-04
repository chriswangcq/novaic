"""
Saga Worker 启动入口 (同步版本)

执行 Saga 流程编排。
"""

import os
import sys
import signal

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


# 默认处理的 saga types
DEFAULT_SAGA_TYPES = [
    "message_process",   # 消息处理入口
    "runtime_start",
    "react_think",
    "react_actions",
    "runtime_complete",
    "summarize",         # 异步摘要生成
]


def main():
    from task_queue.workers.saga_worker_sync import SagaWorkerSync
    from task_queue.sagas import get_all_saga_definitions
    
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    queue_service_url = os.environ.get("QUEUE_SERVICE_URL", "http://127.0.0.1:19997")
    saga_types_str = os.environ.get("SAGA_TYPES", "")
    max_concurrent = int(os.environ.get("MAX_CONCURRENT", "10"))
    
    saga_types = saga_types_str.split(",") if saga_types_str else DEFAULT_SAGA_TYPES
    
    worker = SagaWorkerSync(
        saga_types=saga_types,
        gateway_url=gateway_url,
        queue_service_url=queue_service_url,
        poll_interval=0.1,
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
