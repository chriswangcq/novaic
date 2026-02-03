#!/usr/bin/env python3
"""
NovAIC Backend - Unified Entry Point

Backend 由六个并列组件构成，均由 Tauri 统一拉起：
  - Gateway: API + DB + MCP Proxy
  - MCP Gateway: MCP 聚合与 Runtime/Agent MCP
  - Launcher: Stage 前置处理 + 创建任务
  - Collector: 收集结果 + 触发下一阶段
  - Executor: 执行 LLM/工具调用
  - Health: 监控并回收超时任务

所有 Service 只与 Gateway 通信，MCP 管理操作通过 Gateway 代理。

Usage:
    novaic-backend gateway [--port PORT] [--data-dir PATH]
    novaic-backend mcp-gateway [--port PORT] [--data-dir PATH]
    novaic-backend launcher --gateway-url URL [--bootstrap]
    novaic-backend collector --gateway-url URL
    novaic-backend executor --gateway-url URL [--workers N]
    novaic-backend health --gateway-url URL

v3.0: Three-Task Architecture（Launcher + Collector + Executor + Health）取代 Master + Worker。
"""

import sys
import os

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def print_usage():
    print("""
NovAIC Backend - Unified Entry Point

Backend 七组件（Gateway、MCP Gateway、Monitor、Launcher、Collector、Executor、Health）均由 Tauri 统一拉起。
所有 Service 只与 Gateway 通信。

Usage:
    novaic-backend gateway [options]     Backend 组件: Gateway (API+DB+MCP Proxy)
    novaic-backend mcp-gateway [options] Backend 组件: MCP Gateway (MCP only)
    novaic-backend monitor [options]     Backend 组件: Monitor (事件驱动消息队列消费者)
    novaic-backend launcher [options]    Backend 组件: Launcher (前置处理+创建任务)
    novaic-backend collector [options]   Backend 组件: Collector (收集结果+触发下一阶段)
    novaic-backend executor [options]    Backend 组件: Executor (执行 LLM/工具调用)
    novaic-backend health [options]      Backend 组件: Health (回收超时任务)

Gateway options:
    --port PORT         Port to listen on (default: 19999)
    --data-dir PATH     Data directory (default: from NOVAIC_DATA_DIR env)

MCP Gateway options:
    --port PORT         Port for MCP Gateway (default: 19998)
    --data-dir PATH     Data directory (与 Gateway 共用)

Launcher/Collector/Executor/Health/Monitor options:
    --gateway-url URL   Gateway URL (default: http://127.0.0.1:19999)

Executor options:
    --workers N         Number of parallel workers (default: 3)

Examples:
    novaic-backend gateway --port 19999
    novaic-backend mcp-gateway --port 19998
    novaic-backend monitor --gateway-url http://127.0.0.1:19999
    novaic-backend launcher --gateway-url http://127.0.0.1:19999
    novaic-backend collector --gateway-url http://127.0.0.1:19999
    novaic-backend executor --gateway-url http://127.0.0.1:19999 --workers 3
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


def run_launcher():
    """Run the Launcher service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Launcher Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    # v18: --bootstrap removed, Monitor service now handles message queue
    args = parser.parse_args()
    
    from launcher_main import main as launcher_run
    asyncio.run(launcher_run(args.gateway_url, bootstrap=False))


def run_collector():
    """Run the Collector service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Collector Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    from collector_main import main as collector_run
    asyncio.run(collector_run(args.gateway_url))


def run_executor():
    """Run the Executor service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Executor Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers (default: 3)")
    args = parser.parse_args()
    
    from executor_main import main as executor_run
    asyncio.run(executor_run(args.gateway_url, args.workers))


def run_health():
    """Run the Health Monitor service."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Health Monitor Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    from health_main import main as health_run
    asyncio.run(health_run(args.gateway_url))


def run_monitor():
    """Run the Monitor service (v18: event-driven message queue consumer)."""
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="NovAIC Monitor Service")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999")
    args = parser.parse_args()
    
    from monitor_main import main as monitor_run
    asyncio.run(monitor_run(args.gateway_url))


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
    elif mode == "monitor":
        run_monitor()
    elif mode == "launcher":
        run_launcher()
    elif mode == "collector":
        run_collector()
    elif mode == "executor":
        run_executor()
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
