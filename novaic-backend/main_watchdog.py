"""
Watchdog Worker 启动入口

监控 sending 消息，触发 RuntimeStart Saga。
"""

import asyncio
import os
import sys
import signal

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


async def main():
    from task_queue.workers.watchdog import Watchdog
    
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    
    worker = Watchdog(
        gateway_url=gateway_url,
        poll_interval=0.1,
    )
    
    # 信号处理
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        print("[main_watchdog] Received shutdown signal")
        asyncio.create_task(worker.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler)
    
    print(f"[main_watchdog] Starting Watchdog...")
    print(f"[main_watchdog] Gateway URL: {gateway_url}")
    
    await worker.run()
    
    print("[main_watchdog] Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
