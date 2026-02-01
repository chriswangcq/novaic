#!/usr/bin/env python3
"""
NovAIC Backend - Unified Entry Point

Backend 由四个并列组件构成，均由 Tauri 统一拉起：
  - Gateway: API + DB
  - MCP Gateway: MCP 聚合与 Runtime/Agent MCP
  - Master: 编排（Monitor + Scheduler）
  - Worker: 执行 think/tool_call

Usage:
    novaic-backend gateway [--port PORT] [--data-dir PATH]
    novaic-backend mcp-gateway [--port PORT] [--data-dir PATH]
    novaic-backend master --gateway-url URL [--mcp-gateway-url URL]
    novaic-backend worker --gateway URL [--mcp-gateway-url URL] [--worker-id ID] [--max-concurrent N]

v2.11: 统一二进制，可运行 Backend 各组件（gateway / mcp-gateway / master / worker）。
"""

import sys
import os

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def print_usage():
    print("""
NovAIC Backend - Unified Entry Point

Backend 四组件（Gateway、MCP Gateway、Master、Worker）均由 Tauri 统一拉起。

Usage:
    novaic-backend gateway [options]    Backend 组件: Gateway (API+DB+Workers)
    novaic-backend mcp-gateway [options] Backend 组件: MCP Gateway (MCP only)
    novaic-backend master [options]     Backend 组件: Master (编排)
    novaic-backend worker [options]     Backend 组件: Worker（Tauri 统一拉起）

Gateway options:
    --port PORT         Port to listen on (default: 19999)
    --data-dir PATH     Data directory (default: from NOVAIC_DATA_DIR env)

MCP Gateway options:
    --port PORT         Port for MCP Gateway (default: 19998)
    --data-dir PATH     Data directory (与 Gateway 共用)

Master options:
    --gateway-url URL       Gateway URL (default: http://127.0.0.1:19999)
    --mcp-gateway-url URL   MCP Gateway URL (default: same as gateway-url)

Worker options:
    --gateway URL           Gateway URL (default: http://127.0.0.1:19999)
    --mcp-gateway-url URL   MCP Gateway URL (default: same as gateway)
    --worker-id ID          Worker ID (auto-generated if not provided)
    --max-concurrent N      Max concurrent tasks (default: 10)

Examples:
    novaic-backend gateway --port 19999
    novaic-backend mcp-gateway --port 19998
    novaic-backend master --gateway-url http://127.0.0.1:19999 --mcp-gateway-url http://127.0.0.1:19998
    novaic-backend worker --gateway http://127.0.0.1:19999 --mcp-gateway-url http://127.0.0.1:19998
""")


def run_gateway():
    """Run the Gateway server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Gateway Server")
    parser.add_argument("--port", type=int, default=19999, help="Port to listen on")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    args = parser.parse_args()
    
    # Set data directory
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    
    # Import and run gateway main
    # Note: main.py expects NOVAIC_DATA_DIR to be set
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[Gateway] ERROR: NOVAIC_DATA_DIR environment variable is required")
        print("[Gateway] Use --data-dir option or set NOVAIC_DATA_DIR environment variable")
        sys.exit(1)
    
    # Set port via environment
    os.environ["NOVAIC_PORT"] = str(args.port)
    
    # Import gateway main module
    from main import app
    import uvicorn
    
    print(f"[Gateway] Starting on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


def run_mcp_gateway():
    """Run the MCP Gateway server (MCP only, separate from Backend)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC MCP Gateway")
    parser.add_argument("--port", type=int, default=19998, help="Port for MCP Gateway (default: 19998)")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    args = parser.parse_args()
    
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[MCP Gateway] ERROR: NOVAIC_DATA_DIR required (use --data-dir or set env)")
        sys.exit(1)
    os.environ["NOVAIC_MCP_PORT"] = str(args.port)
    
    from mcp_main import main as mcp_main_run
    mcp_main_run()


def run_master():
    """Run the Master orchestrator."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Master Orchestrator")
    parser.add_argument(
        "--gateway-url",
        default="http://127.0.0.1:19999",
        help="Backend URL (default: http://127.0.0.1:19999)",
    )
    parser.add_argument(
        "--mcp-gateway-url",
        default=None,
        help="MCP Gateway URL when MCP runs in separate process (default: same as gateway-url)",
    )
    args = parser.parse_args()
    
    # Import and run master
    from master_main import MasterService
    
    service = MasterService(
        gateway_url=args.gateway_url,
        mcp_gateway_url=args.mcp_gateway_url,
    )
    
    try:
        asyncio.run(service.run_forever())
    except KeyboardInterrupt:
        print("\n[Master] Interrupted")


def run_worker():
    """Run a Worker process."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Worker Process")
    parser.add_argument("--gateway", default="http://127.0.0.1:19999", help="Backend URL")
    parser.add_argument("--mcp-gateway-url", default=None, help="MCP Gateway URL (default: same as gateway)")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Max concurrent tasks")
    parser.add_argument("--worker-id", help="Worker ID (auto-generated if not provided)")
    args = parser.parse_args()
    
    # Import and run worker
    from worker.worker import WorkerConfig, run_worker as worker_run
    
    config = WorkerConfig(
        gateway_url=args.gateway,
        mcp_gateway_url=args.mcp_gateway_url,
        max_concurrent=args.max_concurrent,
        worker_id=args.worker_id,
    )
    
    asyncio.run(worker_run(config))


def main():
    # Setup Python path for PyInstaller
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        sys.path.insert(0, bundle_dir)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, script_dir)
    
    # Parse mode
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    # Remove mode from argv so argparse in sub-commands works correctly
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    if mode == "gateway":
        run_gateway()
    elif mode == "mcp-gateway":
        run_mcp_gateway()
    elif mode == "master":
        run_master()
    elif mode == "worker":
        run_worker()
    elif mode in ["--help", "-h", "help"]:
        print_usage()
        sys.exit(0)
    else:
        print(f"Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
