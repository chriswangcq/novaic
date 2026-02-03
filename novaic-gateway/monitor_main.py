#!/usr/bin/env python3
"""
NovAIC Backend: Monitor Service (v18)

事件驱动的消息队列消费者：
1. 消费 sending 状态的消息 → sent
2. 尝试唤醒 SubAgent (sleeping/failed → awaking)
3. 创建 runtime_launcher 任务

Usage:
    python monitor_main.py [--gateway-url http://127.0.0.1:19999]
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services import GatewayClient
from services.monitor_worker import MonitorWorker


async def main(gateway_url: str):
    """Run Monitor service."""
    print(f"[MonitorService] Starting...")
    print(f"[MonitorService] Gateway: {gateway_url}")
    
    client = GatewayClient(gateway_url=gateway_url)
    worker = MonitorWorker(client)
    
    # Signal handling
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\n[MonitorService] Shutdown signal received")
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
    
    print("[MonitorService] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Service (v18)")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url))
