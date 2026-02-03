#!/usr/bin/env python3
"""
NovAIC Backend: Launcher Service

处理 launcher 类型任务：准备逻辑 + 创建 async tasks + 创建 collector。

v18: 移除 bootstrap monitor_launcher，改为独立的 Monitor 服务消费 sending 队列。

Usage:
    python launcher_main.py [--gateway-url http://127.0.0.1:19999]
"""

import asyncio
import argparse
import signal
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services import GatewayClient, LauncherWorker

# Register handlers (v18: monitor_launcher no longer needed as bootstrap)
from services.launchers import *


async def main(gateway_url: str, bootstrap: bool = False):
    """Run Launcher service."""
    print(f"[LauncherService] Starting...")
    print(f"[LauncherService] Gateway: {gateway_url}")
    
    client = GatewayClient(gateway_url=gateway_url)
    
    # v18: bootstrap 参数保留但不再创建 monitor_launcher
    # Monitor 服务现在独立运行，消费 sending 消息队列
    if bootstrap:
        print(f"[LauncherService] Bootstrap flag ignored (v18: use Monitor service instead)")
    
    worker = LauncherWorker(client, {
        "gateway_url": gateway_url,
        "worker_id": f"launcher-{uuid.uuid4().hex[:6]}",
    })
    
    # Signal handling
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\n[LauncherService] Shutdown signal received")
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass
    
    # Run worker
    worker_task = asyncio.create_task(worker.run())
    
    try:
        await stop_event.wait()
        await worker.shutdown()
        await worker_task
    finally:
        await client.close()
    
    print("[LauncherService] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launcher Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    parser.add_argument("--bootstrap", action="store_true", help="Create initial monitor_launcher task")
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url, args.bootstrap))
