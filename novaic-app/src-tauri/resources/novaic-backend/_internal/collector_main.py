#!/usr/bin/env python3
"""
NovAIC Backend: Collector Service

处理 collector 类型任务：收集 async 结果 + 后处理 + 触发下一阶段。

Usage:
    python collector_main.py [--gateway-url http://127.0.0.1:19999]
"""

import asyncio
import argparse
import signal
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services import GatewayClient, CollectorWorker

# Register handlers
from services.collectors import *


async def main(gateway_url: str):
    """Run Collector service."""
    print(f"[CollectorService] Starting...")
    print(f"[CollectorService] Gateway: {gateway_url}")
    
    client = GatewayClient(gateway_url=gateway_url)
    
    worker = CollectorWorker(client, {
        "gateway_url": gateway_url,
        "worker_id": f"collector-{uuid.uuid4().hex[:6]}",
    })
    
    # Signal handling
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\n[CollectorService] Shutdown signal received")
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
    
    print("[CollectorService] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collector Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url))
