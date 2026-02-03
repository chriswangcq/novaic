#!/usr/bin/env python3
"""
NovAIC Backend: Executor Service

处理 executor 类型任务：执行 LLM 调用、工具调用等。

Usage:
    python executor_main.py [--gateway-url http://127.0.0.1:19999] [--workers 3]
"""

import asyncio
import argparse
import signal
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services import GatewayClient, ExecutorWorker

# Register handlers
from services.executors import *


async def main(gateway_url: str, num_workers: int = 3):
    """Run Executor service with multiple parallel workers."""
    print(f"[ExecutorService] Starting {num_workers} workers...")
    print(f"[ExecutorService] Gateway: {gateway_url}")
    
    client = GatewayClient(gateway_url=gateway_url)
    
    # Create multiple workers for parallel execution
    workers = []
    for i in range(num_workers):
        worker = ExecutorWorker(client, {
            "gateway_url": gateway_url,
            "worker_id": f"executor-{i}-{uuid.uuid4().hex[:4]}",
        })
        workers.append(worker)
    
    # Signal handling
    stop_event = asyncio.Event()
    
    def signal_handler():
        print(f"\n[ExecutorService] Shutdown signal received")
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass
    
    # Run all workers in parallel
    worker_tasks = [asyncio.create_task(w.run()) for w in workers]
    
    try:
        await stop_event.wait()
        # Shutdown all workers
        for w in workers:
            await w.shutdown()
        await asyncio.gather(*worker_tasks, return_exceptions=True)
    finally:
        await client.close()
    
    print("[ExecutorService] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers (default: 3)")
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url, args.workers))
