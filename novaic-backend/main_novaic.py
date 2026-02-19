#!/usr/bin/env python3
"""
NovAIC Backend - Unified Entry Point

Backend v2 架构由以下组件构成：
  - Gateway: API + DB
  - Tools Server: HTTP API for tools (replaces MCP Gateway)
  - Queue Service: Task/Saga 队列管理
  - Watchdog: 监控 sending 消息，触发 MessageProcess Saga
  - Task Worker: 通用任务执行器
  - Saga Worker: Saga 流程编排
  - Health Worker: 监控并回收超时任务/Saga
  - Scheduler Worker: 定时唤醒 sleeping agents
  - VMControl: VM 管理服务 (Rust)

所有 Worker 通过 Gateway 和 Queue Service 通信。

Usage:
    novaic-backend gateway --host HOST --port PORT --data-dir PATH --runtime-orchestrator-url URL --queue-service-url URL --tools-server-url URL --vmcontrol-url URL --file-service-url URL --tool-result-service-url URL
    novaic-backend tools-server --host HOST --port PORT --data-dir PATH --gateway-url URL --runtime-orchestrator-url URL --tool-result-service-url URL
    novaic-backend queue-service --host HOST --port PORT --data-dir PATH
    novaic-backend watchdog --gateway-url URL --queue-service-url URL --runtime-orchestrator-url URL --data-dir PATH
    novaic-backend task-worker --gateway-url URL --queue-service-url URL --tools-server-url URL --runtime-orchestrator-url URL --tool-result-service-url URL --num-workers N --data-dir PATH
    novaic-backend saga-worker --gateway-url URL --queue-service-url URL --runtime-orchestrator-url URL --max-concurrent N --data-dir PATH
    novaic-backend health --gateway-url URL --queue-service-url URL --runtime-orchestrator-url URL --check-interval N --task-timeout N --saga-timeout N --data-dir PATH
    novaic-backend scheduler --gateway-url URL --runtime-orchestrator-url URL --check-interval N --data-dir PATH
    novaic-backend runtime-orchestrator --host HOST --port PORT --data-dir PATH
    novaic-backend vmcontrol --host HOST --port PORT [--vmcontrol-bin PATH]

v2.0: Saga/Task Architecture 替代旧的 Master/Worker/Launcher/Collector 架构
"""

import sys
import os

# Import unified configuration
from common.config import ServiceConfig


def print_usage():
    print("""
NovAIC Backend - Unified Entry Point (v2 Architecture)

Backend 八组件均由 Tauri 统一拉起。

Usage:
    novaic-backend gateway [options]       Backend 组件: Gateway (API+DB)
    novaic-backend tools-server [options]  Backend 组件: Tools Server (HTTP API for tools)
    novaic-backend queue-service [options] Backend 组件: Queue Service (Task/Saga 队列)
    novaic-backend watchdog [options]      Backend 组件: Watchdog (消息监控)
    novaic-backend task-worker [options]   Backend 组件: Task Worker (任务执行)
    novaic-backend saga-worker [options]   Backend 组件: Saga Worker (流程编排)
    novaic-backend health [options]        Backend 组件: Health Worker (超时回收)
    novaic-backend scheduler [options]     Backend 组件: Scheduler Worker (定时唤醒)
    novaic-backend runtime-orchestrator [options] Backend 组件: Runtime Orchestrator (internal API service)
    novaic-backend vmcontrol [options]     Backend 组件: VMControl (VM 管理服务)
    novaic-backend file-service [options]       Backend 组件: File Service (文件管理服务)
    novaic-backend tool-result-service [options] Backend 组件: Tool Result Service (结果规范化)

Gateway options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory

Tools Server options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory
    --gateway-url URL   Required gateway URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --tool-result-service-url URL Required tool result service URL

Queue Service options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory

Watchdog options:
    --gateway-url URL       Required gateway URL
    --queue-service-url URL Required queue service URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --data-dir PATH         Required data directory

Task Worker options:
    --gateway-url URL       Required gateway URL
    --queue-service-url URL Required queue service URL
    --tools-server-url URL  Required tools server URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --tool-result-service-url URL Required tool result service URL
    --num-workers N         Required worker thread count
    --data-dir PATH         Required data directory

Saga Worker options:
    --gateway-url URL       Required gateway URL
    --queue-service-url URL Required queue service URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --max-concurrent N      Required max concurrent sagas
    --data-dir PATH         Required data directory

Health Worker options:
    --gateway-url URL       Required gateway URL
    --queue-service-url URL Required queue service URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --check-interval N      Required check interval
    --task-timeout N        Required task timeout
    --saga-timeout N        Required saga timeout
    --data-dir PATH         Required data directory

Scheduler Worker options:
    --gateway-url URL       Required gateway URL
    --runtime-orchestrator-url URL Required runtime orchestrator URL
    --check-interval SECS   Required check interval in seconds
    --data-dir PATH         Required data directory

Runtime Orchestrator options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory

VMControl options:
    --host HOST         Required host
    --port PORT         Required port
    --vmcontrol-bin     Path to vmcontrol binary (default: auto-detect)

File Service options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory

Tool Result Service options:
    --host HOST         Required host
    --port PORT         Required port
    --data-dir PATH     Required data directory

Examples:
    novaic-backend queue-service --host 127.0.0.1 --port 19997 --data-dir /Users/me/.novaic
    novaic-backend runtime-orchestrator --host 127.0.0.1 --port 19993 --data-dir /Users/me/.novaic
    novaic-backend gateway --host 127.0.0.1 --port 19999 --data-dir /Users/me/.novaic --runtime-orchestrator-url http://127.0.0.1:19993 --queue-service-url http://127.0.0.1:19997 --tools-server-url http://127.0.0.1:19998 --vmcontrol-url http://127.0.0.1:19996 --file-service-url http://127.0.0.1:19995 --tool-result-service-url http://127.0.0.1:19994
    novaic-backend task-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 --tools-server-url http://127.0.0.1:19998 --runtime-orchestrator-url http://127.0.0.1:19993 --tool-result-service-url http://127.0.0.1:19994 --num-workers 5 --data-dir /Users/me/.novaic
    novaic-backend vmcontrol --host 127.0.0.1 --port 8080
""")


def run_gateway():
    """Run the Gateway server."""
    import argparse

    parser = argparse.ArgumentParser(description="NovAIC Gateway Server")
    parser.add_argument("--host", required=True, help="Gateway host")
    parser.add_argument("--port", required=True, type=int, help="Gateway port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
    parser.add_argument("--tools-server-url", required=True, help="Tools Server URL")
    parser.add_argument("--vmcontrol-url", required=True, help="VMControl URL")
    parser.add_argument("--file-service-url", required=True, help="File Service URL")
    parser.add_argument("--tool-result-service-url", required=True, help="Tool Result Service URL")
    args = parser.parse_args()

    # Apply runtime config from CLI (no fallback).
    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_HOST = args.host
    ServiceConfig.GATEWAY_PORT = args.port
    ServiceConfig.GATEWAY_URL = f"http://{args.host}:{args.port}"
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
    ServiceConfig.TOOLS_SERVER_URL = args.tools_server_url
    ServiceConfig.VMCONTROL_URL = args.vmcontrol_url
    ServiceConfig.FILE_SERVICE_URL = args.file_service_url
    ServiceConfig.TOOL_RESULT_SERVICE_URL = args.tool_result_service_url

    # Import gateway main module (v4: renamed from main.py to main_gateway.py)
    from main_gateway import app
    import uvicorn
    
    print(f"[Gateway] Starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def run_tools_server():
    """Run the Tools Server (HTTP API for tools, replaces MCP Gateway)."""
    import argparse
    import httpx

    parser = argparse.ArgumentParser(description="NovAIC Tools Server")
    parser.add_argument("--host", required=True, help="Tools Server host")
    parser.add_argument("--port", required=True, type=int, help="Tools Server port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--tool-result-service-url", required=True, help="Tool Result Service URL")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.TOOLS_SERVER_HOST = args.host
    ServiceConfig.TOOLS_SERVER_PORT = args.port
    ServiceConfig.TOOLS_SERVER_URL = f"http://{args.host}:{args.port}"
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    ServiceConfig.TOOL_RESULT_SERVICE_URL = args.tool_result_service_url

    # Fail fast on misconfigured/unreachable Runtime Orchestrator.
    ro_health_url = f"{args.runtime_orchestrator_url.rstrip('/')}/api/health"
    try:
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            response = client.get(ro_health_url)
            response.raise_for_status()
    except Exception as exc:
        print(f"[Tools Server] ERROR: Runtime Orchestrator health check failed: {ro_health_url} ({exc})")
        sys.exit(1)

    # Fail fast on misconfigured/unreachable Tool Result Service.
    trs_health_url = f"{args.tool_result_service_url.rstrip('/')}/api/health"
    try:
        with httpx.Client(timeout=5.0, trust_env=False) as client:
            response = client.get(trs_health_url)
            response.raise_for_status()
    except Exception as exc:
        print(f"[Tools Server] ERROR: Tool Result Service health check failed: {trs_health_url} ({exc})")
        sys.exit(1)
    
    from main_tools import app
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def run_queue_service():
    """Run the Queue Service (Task/Saga queue management)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Queue Service")
    parser.add_argument("--host", required=True, help="Queue Service host")
    parser.add_argument("--port", required=True, type=int, help="Queue Service port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.QUEUE_SERVICE_HOST = args.host
    ServiceConfig.QUEUE_SERVICE_PORT = args.port
    ServiceConfig.QUEUE_SERVICE_URL = f"http://{args.host}:{args.port}"
    
    from queue_service.main import app
    import uvicorn
    
    print(f"[Queue Service] Starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def run_watchdog():
    """Run the Watchdog service (message monitor)."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Watchdog Service")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL")
    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    _setup_worker_logging("watchdog")
    
    from task_queue.workers.watchdog_sync import WatchdogSync

    worker = WatchdogSync(
        gateway_url=args.gateway_url,
        queue_service_url=args.queue_service_url,
        poll_interval=ServiceConfig.POLL_INTERVAL,
    )
    
    def shutdown_handler(signum, frame):
        print("[watchdog] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[watchdog] Starting...")
    print(f"[watchdog] Gateway URL: {args.gateway_url}")
    print(f"[watchdog] Queue Service URL: {args.queue_service_url}")
    
    worker.run()
    print("[watchdog] Shutdown complete")


def run_task_worker():
    """Run the Task Worker service."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Task Worker Service")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL")
    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
    parser.add_argument("--tools-server-url", required=True, help="Tools Server URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--tool-result-service-url", required=True, help="Tool Result Service URL")
    parser.add_argument("--num-workers", type=int, required=True, help="Number of worker threads")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
    ServiceConfig.TOOLS_SERVER_URL = args.tools_server_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    ServiceConfig.TOOL_RESULT_SERVICE_URL = args.tool_result_service_url
    ServiceConfig.NUM_WORKERS = args.num_workers
    _setup_worker_logging("task-worker")
    
    from task_queue.workers.task_worker_sync import TaskWorkerSync
    from task_queue.handlers import get_all_topics
    
    # 自动从 handlers 注册表获取所有 topics
    topics = get_all_topics()
    print(f"[task-worker] Subscribed to {len(topics)} topics: {sorted(topics)}")
    
    worker = TaskWorkerSync(
        topics=topics,
        queue_service_url=args.queue_service_url,
        gateway_url=args.gateway_url,
    )
    
    def shutdown_handler(signum, frame):
        print("[task-worker] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[task-worker] Starting...")
    print(f"[task-worker] Gateway URL: {args.gateway_url}")
    print(f"[task-worker] Queue Service URL: {args.queue_service_url}")
    print(f"[task-worker] Tools Server URL: {args.tools_server_url}")
    print(f"[task-worker] Num workers: {args.num_workers} (reserved)")
    
    worker.run()
    print("[task-worker] Shutdown complete")


def run_saga_worker():
    """Run the Saga Worker service."""
    import argparse

    parser = argparse.ArgumentParser(description="NovAIC Saga Worker Service")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL")
    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--max-concurrent", type=int, required=True, help="Max concurrent sagas")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    ServiceConfig.MAX_CONCURRENT_SAGAS = args.max_concurrent
    _setup_worker_logging("saga-worker")

    # Forward required CLI args to main_saga (no defaults).
    sys.argv = [
        sys.argv[0],
        "--gateway-url", args.gateway_url,
        "--queue-service-url", args.queue_service_url,
        "--runtime-orchestrator-url", args.runtime_orchestrator_url,
        "--max-concurrent", str(args.max_concurrent),
    ]
    from main_saga import main as saga_run
    saga_run()


def run_health():
    """Run the Health Worker service."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Health Worker Service")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL (accepted but not used)")
    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--check-interval", type=float, required=True, help="Health check interval in seconds")
    parser.add_argument("--task-timeout", type=int, required=True, help="Task timeout in seconds")
    parser.add_argument("--saga-timeout", type=int, required=True, help="Saga timeout in seconds")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    ServiceConfig.TASK_TIMEOUT = args.task_timeout
    ServiceConfig.SAGA_TIMEOUT = args.saga_timeout
    _setup_worker_logging("health")
    
    from task_queue.workers.health_worker_sync import HealthWorkerSync
    
    worker = HealthWorkerSync(
        queue_service_url=args.queue_service_url,
        check_interval=args.check_interval,
        task_timeout=args.task_timeout,
        saga_timeout=args.saga_timeout,
    )
    
    def shutdown_handler(signum, frame):
        print("[health] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[health] Starting...")
    print(f"[health] Queue Service URL: {args.queue_service_url}")
    
    worker.run()
    print("[health] Shutdown complete")


def run_scheduler():
    """Run the Scheduler Worker service (scheduled agent wake-up)."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Scheduler Worker Service")
    parser.add_argument("--gateway-url", required=True, help="Gateway URL")
    parser.add_argument("--runtime-orchestrator-url", required=True, help="Runtime Orchestrator URL")
    parser.add_argument("--check-interval", type=float, required=True, help="Check interval in seconds")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.GATEWAY_URL = args.gateway_url
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = args.runtime_orchestrator_url
    _setup_worker_logging("scheduler")
    
    from task_queue.workers.scheduler_worker_sync import SchedulerWorkerSync
    
    worker = SchedulerWorkerSync(
        gateway_url=args.gateway_url,
        check_interval=args.check_interval,
    )
    
    def shutdown_handler(signum, frame):
        print("[scheduler] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[scheduler] Starting...")
    print(f"[scheduler] Gateway URL: {args.gateway_url}")
    print(f"[scheduler] Check interval: {args.check_interval}s")
    
    worker.run()
    print("[scheduler] Shutdown complete")


def run_file_service():
    """Run the File Service (file storage, URL management)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC File Service")
    parser.add_argument("--host", required=True, help="File Service host")
    parser.add_argument("--port", type=int, required=True, help="File Service port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.FILE_SERVICE_HOST = args.host
    ServiceConfig.FILE_SERVICE_PORT = args.port
    ServiceConfig.FILE_SERVICE_URL = f"http://{args.host}:{args.port}"
    
    from file_service.main import create_app
    import uvicorn
    
    base_dir = args.data_dir
    app = create_app(base_dir=base_dir)
    
    print(f"[File Service] Starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def run_tool_result_service():
    """Run the Tool Result Service (result normalization)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Tool Result Service")
    parser.add_argument("--host", required=True, help="Tool Result Service host")
    parser.add_argument("--port", type=int, required=True, help="Tool Result Service port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.TOOL_RESULT_SERVICE_HOST = args.host
    ServiceConfig.TOOL_RESULT_SERVICE_PORT = args.port
    ServiceConfig.TOOL_RESULT_SERVICE_URL = f"http://{args.host}:{args.port}"
    
    from tool_result_service.main import create_app
    import uvicorn
    
    app = create_app()
    print(f"[Tool Result Service] Starting on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


def run_vmcontrol():
    """Run the VMControl service (Rust binary)."""
    import argparse
    import subprocess
    import shutil
    from pathlib import Path
    import time
    import requests
    
    parser = argparse.ArgumentParser(description="NovAIC VMControl Service")
    parser.add_argument("--port", type=int, required=True, help="Port for VMControl")
    parser.add_argument("--host", required=True, help="Host to bind to")
    parser.add_argument("--vmcontrol-bin", help="Path to vmcontrol binary (default: auto-detect)")
    args = parser.parse_args()
    
    # Find vmcontrol binary
    vmcontrol_bin = args.vmcontrol_bin
    if not vmcontrol_bin:
        # Try multiple locations
        script_dir = Path(__file__).parent
        candidates = [
            # Relative to novaic-backend
            script_dir.parent / "novaic-app" / "src-tauri" / "target" / "release" / "vmcontrol",
            script_dir.parent / "novaic-app" / "src-tauri" / "target" / "debug" / "vmcontrol",
            # From PATH
            shutil.which("vmcontrol"),
            # Check if we're in a packaged environment (PyInstaller)
            Path(sys.executable).parent / "vmcontrol",
        ]
        
        for candidate in candidates:
            if candidate and Path(candidate).exists() and Path(candidate).is_file():
                vmcontrol_bin = str(candidate)
                print(f"[VMControl] Found binary at: {vmcontrol_bin}")
                break
    
    if not vmcontrol_bin or not Path(vmcontrol_bin).exists():
        print("[VMControl] ERROR: vmcontrol binary not found")
        print("[VMControl] Searched locations:")
        for candidate in candidates:
            if candidate:
                print(f"[VMControl]   - {candidate}")
        print("[VMControl] Please build vmcontrol or specify --vmcontrol-bin")
        print("[VMControl] Build command: cd novaic-app/src-tauri/vmcontrol && cargo build --release")
        sys.exit(1)
    
    # Set environment variables for Rust service
    env = os.environ.copy()
    env["RUST_LOG"] = env.get("RUST_LOG", "vmcontrol=info,tower_http=debug")
    
    print(f"[VMControl] Starting on {args.host}:{args.port}")
    print(f"[VMControl] Binary: {vmcontrol_bin}")
    print(f"[VMControl] RUST_LOG: {env['RUST_LOG']}")
    
    # Build command with arguments
    cmd = [
        vmcontrol_bin,
        "--port", str(args.port),
        "--host", args.host,
    ]
    
    print(f"[VMControl] Command: {' '.join(cmd)}")
    
    # Start the vmcontrol process
    try:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        # Wait for service to be ready
        print("[VMControl] Waiting for service to be ready...")
        max_wait = 30
        start_time = time.time()
        ready = False
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"http://{args.host}:{args.port}/api/health",
                    timeout=2
                )
                if response.status_code == 200:
                    ready = True
                    print("[VMControl] Service is ready!")
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        if not ready:
            print(f"[VMControl] WARNING: Service not responding after {max_wait}s")
        
        # Stream logs
        print("[VMControl] Streaming logs (Ctrl+C to stop)...")
        try:
            for line in process.stdout:
                print(f"[VMControl] {line.rstrip()}")
        except KeyboardInterrupt:
            print("\n[VMControl] Received interrupt signal")
        finally:
            print("[VMControl] Shutting down...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("[VMControl] Force killing process...")
                process.kill()
                process.wait()
            print("[VMControl] Shutdown complete")
    
    except FileNotFoundError:
        print(f"[VMControl] ERROR: Could not execute {vmcontrol_bin}")
        sys.exit(1)
    except Exception as e:
        print(f"[VMControl] ERROR: {e}")
        sys.exit(1)


def run_runtime_orchestrator():
    """Run Runtime Orchestrator service."""
    import argparse

    parser = argparse.ArgumentParser(description="NovAIC Runtime Orchestrator")
    parser.add_argument("--host", required=True, help="Runtime Orchestrator host")
    parser.add_argument("--port", type=int, required=True, help="Runtime Orchestrator port")
    parser.add_argument("--data-dir", required=True, help="Data directory")
    args = parser.parse_args()

    ServiceConfig.DATA_DIR = args.data_dir
    ServiceConfig.RUNTIME_ORCHESTRATOR_HOST = args.host
    ServiceConfig.RUNTIME_ORCHESTRATOR_PORT = args.port
    ServiceConfig.RUNTIME_ORCHESTRATOR_URL = f"http://{args.host}:{args.port}"

    from main_runtime_orchestrator import app
    import uvicorn

    print(f"[Runtime Orchestrator] Starting on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


def _setup_worker_logging(mode: str):
    """Setup file logging for worker processes.
    
    Worker processes in binary mode have stdout/stderr set to null by Tauri.
    This redirects output to a log file so we can debug startup failures.
    """
    data_dir = ServiceConfig.DATA_DIR
    if not data_dir:
        return  # Can't log without data dir
    
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    from datetime import datetime as dt
    log_file = os.path.join(log_dir, f"{mode}-{dt.now().strftime('%Y%m%d')}.log")
    
    try:
        fh = open(log_file, 'a', encoding='utf-8', buffering=1)
        
        class TeeStream:
            def __init__(self, file, stream):
                self.file = file
                self.stream = stream
            
            def write(self, data):
                if data:
                    self.file.write(data)
                    try:
                        self.stream.write(data)
                    except Exception:
                        pass
            
            def flush(self):
                self.file.flush()
                try:
                    self.stream.flush()
                except Exception:
                    pass
        
        sys.stdout = TeeStream(fh, sys.__stdout__)
        sys.stderr = TeeStream(fh, sys.__stderr__)
    except Exception:
        pass  # Best-effort: don't crash if log setup fails


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
    elif mode in ("tools-server", "mcp-gateway"):
        run_tools_server()
    elif mode == "queue-service":
        run_queue_service()
    elif mode == "watchdog":
        run_watchdog()
    elif mode == "task-worker":
        run_task_worker()
    elif mode == "saga-worker":
        run_saga_worker()
    elif mode == "health":
        run_health()
    elif mode == "scheduler":
        run_scheduler()
    elif mode == "vmcontrol":
        run_vmcontrol()
    elif mode == "runtime-orchestrator":
        run_runtime_orchestrator()
    elif mode == "file-service":
        run_file_service()
    elif mode == "tool-result-service":
        run_tool_result_service()
    elif mode in ["--help", "-h", "help"]:
        print_usage()
        sys.exit(0)
    else:
        print(f"Unknown mode: {mode}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
