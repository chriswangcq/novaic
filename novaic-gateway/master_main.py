#!/usr/bin/env python3
"""
NovAIC Backend 组件: Master - 编排入口。

Backend 四组件（Gateway、MCP Gateway、Master、Worker）均由 Tauri 统一拉起。
本进程为 Master：Monitor + Scheduler，通过 HTTP 调 Gateway（DB/任务等）与 MCP Gateway（MCP 生命周期）。

Usage:
    python master_main.py [--gateway-url http://127.0.0.1:19999] [--mcp-gateway-url http://127.0.0.1:19998]
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from master.master import Master, MasterConfig, set_master


class MasterService:
    """Standalone Master service."""
    
    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:19999",
        mcp_gateway_url: str = None,
    ):
        self.gateway_url = gateway_url
        self.mcp_gateway_url = mcp_gateway_url or gateway_url
        self.master: Master = None
        self._running = False
    
    async def start(self):
        """Start the Master service."""
        print("[MasterService] Starting...")
        print(f"[MasterService] Gateway URL: {self.gateway_url}")
        print(f"[MasterService] MCP Gateway URL: {self.mcp_gateway_url}")
        
        # Create and start Master
        self.master = Master(
            gateway_url=self.gateway_url,
            config=MasterConfig(
                monitor_interval=1.0,
                scheduler_interval=0.1,
            ),
            mcp_gateway_url=self.mcp_gateway_url,
        )
        set_master(self.master)
        
        await self.master.start()
        
        self._running = True
        print("[MasterService] Started")
    
    async def stop(self):
        """Stop the Master service."""
        if not self._running:
            return
        
        print("[MasterService] Stopping...")
        
        if self.master:
            await self.master.stop()
        
        self._running = False
        print("[MasterService] Stopped")
    
    async def run_forever(self):
        """Run until interrupted."""
        await self.start()
        
        # Wait for shutdown signal
        stop_event = asyncio.Event()
        
        def signal_handler():
            print("\n[MasterService] Received shutdown signal")
            stop_event.set()
        
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass
        
        try:
            await stop_event.wait()
        finally:
            await self.stop()


def main():
    parser = argparse.ArgumentParser(description="Master Service")
    parser.add_argument(
        "--gateway-url",
        default="http://127.0.0.1:19999",
        help="Backend (Gateway) URL (default: http://127.0.0.1:19999)",
    )
    parser.add_argument(
        "--mcp-gateway-url",
        default=None,
        help="MCP Gateway URL when MCP runs in separate process (default: same as gateway-url)",
    )
    args = parser.parse_args()
    
    service = MasterService(
        gateway_url=args.gateway_url,
        mcp_gateway_url=args.mcp_gateway_url,
    )
    
    try:
        asyncio.run(service.run_forever())
    except KeyboardInterrupt:
        print("\n[MasterService] Interrupted")


if __name__ == "__main__":
    main()
