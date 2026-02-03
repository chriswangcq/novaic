#!/usr/bin/env python3
"""
NovAIC Backend - Unified Entry Point

Backend v2 架构由以下组件构成：
  - Gateway: API + DB
  - MCP Gateway: MCP 聚合与 Runtime/Agent MCP
  - Watchdog: 监控 sending 消息，触发 MessageProcess Saga
  - Task Worker: 通用任务执行器
  - Saga Worker: Saga 流程编排
  - Health Worker: 监控并回收超时任务/Saga

所有 Service 只与 Gateway 通信。

Usage:
    novaic-backend gateway [--port PORT] [--data-dir PATH]
    novaic-backend mcp-gateway [--port PORT] [--data-dir PATH]
    novaic-backend watchdog --gateway-url URL
    novaic-backend task-worker --gateway-url URL
    novaic-backend saga-worker --gateway-url URL
    novaic-backend health --gateway-url URL

v2.0: Saga/Task Architecture 替代旧的 Master/Worker/Launcher/Collector 架构
"""

import sys
import os

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def print_usage():
    print("""
NovAIC Backend - Unified Entry Point (v2 Architecture)

Backend 六组件均由 Tauri 统一拉起，所有 Service 只与 Gateway 通信。

Usage:
    novaic-backend gateway [options]      Backend 组件: Gateway (API+DB)
    novaic-backend mcp-gateway [options]  Backend 组件: MCP Gateway (MCP only)
    novaic-backend watchdog [options]     Backend 组件: Watchdog (消息监控)
    novaic-backend task-worker [options]  Backend 组件: Task Worker (任务执行)
    novaic-backend saga-worker [options]  Backend 组件: Saga Worker (流程编排)
    novaic-backend health [options]       Backend 组件: Health Worker (超时回收)

Gateway options:
    --port PORT         Port to listen on (default: 19999)
    --data-dir PATH     Data directory (default: from NOVAIC_DATA_DIR env)

MCP Gateway options:
    --port PORT         Port for MCP Gateway (default: 19998)
    --data-dir PATH     Data directory (与 Gateway 共用)

Worker options (watchdog/task-worker/saga-worker/health):
    --gateway-url URL   Gateway URL (default: http://127.0.0.1:19999)

Examples:
    novaic-backend gateway --port 19999
    novaic-backend mcp-gateway --port 19998
    novaic-backend watchdog --gateway-url http://127.0.0.1:19999
    novaic-backend task-worker --gateway-url http://127.0.0.1:19999
    novaic-backend saga-worker --gateway-url http://127.0.0.1:19999
    novaic-backend health --gateway-url http://127.0.0.1:19999
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
    # Note: main_gateway.py expects NOVAIC_DATA_DIR to be set
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[Gateway] ERROR: NOVAIC_DATA_DIR environment variable is required")
        print("[Gateway] Use --data-dir option or set NOVAIC_DATA_DIR environment variable")
        sys.exit(1)
    
    # Set port via environment
    os.environ["NOVAIC_PORT"] = str(args.port)
    
    # Import gateway main module (v4: renamed from main.py to main_gateway.py)
    from main_gateway import app
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
    
    from main_mcp import main as mcp_main_run
    mcp_main_run()


def run_watchdog():
    """Run the Watchdog service (message monitor)."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Watchdog Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    os.environ["NOVAIC_GATEWAY_URL"] = args.gateway_url
    
    from main_watchdog import main as watchdog_run
    asyncio.run(watchdog_run())


def run_task_worker():
    """Run the Task Worker service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Task Worker Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    os.environ["NOVAIC_GATEWAY_URL"] = args.gateway_url
    
    from main_task import main as task_run
    asyncio.run(task_run())


def run_saga_worker():
    """Run the Saga Worker service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Saga Worker Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    os.environ["NOVAIC_GATEWAY_URL"] = args.gateway_url
    
    from main_saga import main as saga_run
    asyncio.run(saga_run())


def run_health():
    """Run the Health Worker service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Health Worker Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    os.environ["NOVAIC_GATEWAY_URL"] = args.gateway_url
    
    from main_health import main as health_run
    asyncio.run(health_run())


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
    elif mode == "watchdog":
        run_watchdog()
    elif mode == "task-worker":
        run_task_worker()
    elif mode == "saga-worker":
        run_saga_worker()
    elif mode == "health":
        run_health()
    elif mode in ["--help", "-h", "help"]:
        print_usage()
        sys.exit(0)
    else:
        print(f"Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
