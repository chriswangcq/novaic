"""
Saga Worker v2 启动入口

执行 Saga 流程编排。
"""

import asyncio
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


async def main():
    from task_queue.workers.saga_worker_v2 import SagaWorkerV2
    from task_queue.sagas import get_all_saga_definitions
    
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    saga_types_str = os.environ.get("SAGA_TYPES", "")
    
    saga_types = saga_types_str.split(",") if saga_types_str else DEFAULT_SAGA_TYPES
    
    worker = SagaWorkerV2(
        saga_types=saga_types,
        gateway_url=gateway_url,
        poll_interval=0.1,
        heartbeat_interval=10.0,
    )
    
    # 注册 Saga 定义
    for saga_def in get_all_saga_definitions():
        worker.register_definition(saga_def.name, saga_def)
        print(f"[main_saga] Registered: {saga_def.name} ({len(saga_def.steps)} steps)")
    
    # 信号处理
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        print("[main_saga] Received shutdown signal")
        asyncio.create_task(worker.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler)
    
    print(f"[main_saga] Starting SagaWorker v2...")
    print(f"[main_saga] Gateway URL: {gateway_url}")
    print(f"[main_saga] Saga types: {saga_types}")
    
    await worker.run()
    
    print("[main_saga] Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
