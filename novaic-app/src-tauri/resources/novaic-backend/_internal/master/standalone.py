"""
Master Standalone Service Entry Point

v2.10: Run Master as a separate service.
Communicates with Gateway via HTTP internal API.

Usage:
    python -m master.standalone --gateway-url http://127.0.0.1:19999
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .client import MasterClient, set_master_client
from .master_remote import RemoteMaster


async def main(gateway_url: str):
    """Run Master as standalone service."""
    print(f"[Master Standalone] Starting with Gateway at {gateway_url}")
    
    # Create client
    client = MasterClient(gateway_url)
    set_master_client(client)
    
    # Create Master
    master = RemoteMaster(client)
    
    # Handle signals
    stop_event = asyncio.Event()
    
    def handle_signal():
        print("\n[Master Standalone] Shutting down...")
        stop_event.set()
    
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)
    
    try:
        async with client:
            # Start Master
            await master.start()
            
            print("[Master Standalone] Running. Press Ctrl+C to stop.")
            
            # Wait for stop signal
            await stop_event.wait()
            
            # Stop Master
            await master.stop()
    except Exception as e:
        print(f"[Master Standalone] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("[Master Standalone] Stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master Standalone Service")
    parser.add_argument(
        "--gateway-url",
        default="http://127.0.0.1:19999",
        help="Gateway URL (default: http://127.0.0.1:19999)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(args.gateway_url))
