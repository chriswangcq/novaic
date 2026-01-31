#!/usr/bin/env python3
"""
Entry point for novaic-worker binary.

This script sets up the Python path correctly and imports the worker module
to avoid relative import issues when running as a standalone PyInstaller binary.
"""

import sys
import os
import asyncio
import argparse

# Add parent directory to path so worker module can be found
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
else:
    # Running as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)

# Now import worker components
from worker.worker import WorkerConfig, run_worker


def main():
    parser = argparse.ArgumentParser(description="Run NovAIC Worker")
    parser.add_argument("--gateway", default="http://localhost:9527", help="Gateway URL")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Max concurrent tasks")
    parser.add_argument("--worker-id", help="Worker ID (auto-generated if not provided)")
    
    args = parser.parse_args()
    
    config = WorkerConfig(
        gateway_url=args.gateway,
        max_concurrent=args.max_concurrent,
        worker_id=args.worker_id,
    )
    
    asyncio.run(run_worker(config))


if __name__ == "__main__":
    main()
