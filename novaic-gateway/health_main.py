#!/usr/bin/env python3
"""
NovAIC Backend: Health Monitor Service

监控并回收超时任务，保证系统可恢复。

Usage:
    python health_main.py [--gateway-url http://127.0.0.1:19999]
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services import GatewayClient, HealthMonitor


async def main(gateway_url: str):
    """Run Health Monitor service."""
    print(f"[HealthService] Starting...")
    print(f"[HealthService] Gateway: {gateway_url}")
    
    client = GatewayClient(gateway_url=gateway_url)
    
    monitor = HealthMonitor(client, {
        "check_interval": 30.0,
        "launcher_timeout": 60,
        "collector_timeout": 60,
        "async_timeout": 300,
    })
    
    # Signal handling
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\n[HealthService] Shutdown signal received")
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass
    
    # Run monitor
    monitor_task = asyncio.create_task(monitor.run())
    
    try:
        await stop_event.wait()
        await monitor.shutdown()
        await monitor_task
    finally:
        await client.close()
    
    print("[HealthService] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Health Monitor Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url))
