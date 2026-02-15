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
    novaic-backend gateway [--port PORT] [--data-dir PATH]
    novaic-backend tools-server [--port PORT] [--data-dir PATH] [--gateway-url URL]
    novaic-backend queue-service [--port PORT] [--data-dir PATH]
    novaic-backend watchdog --gateway-url URL --queue-service-url URL
    novaic-backend task-worker --gateway-url URL --queue-service-url URL [--num-workers N]
    novaic-backend saga-worker --gateway-url URL --queue-service-url URL [--max-concurrent N]
    novaic-backend health --queue-service-url URL
    novaic-backend scheduler --gateway-url URL
    novaic-backend vmcontrol [--port PORT] [--host HOST]

v2.0: Saga/Task Architecture 替代旧的 Master/Worker/Launcher/Collector 架构
"""

import sys
import os

# Set no_proxy to avoid proxy issues with local services
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'

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
    novaic-backend vmcontrol [options]     Backend 组件: VMControl (VM 管理服务)
    novaic-backend file-service [options]       Backend 组件: File Service (文件管理服务)
    novaic-backend tool-result-service [options] Backend 组件: Tool Result Service (结果规范化)

Gateway options:
    --port PORT         Port to listen on (default: 19999)
    --data-dir PATH     Data directory (default: from NOVAIC_DATA_DIR env)

Tools Server options:
    --port PORT         Port for Tools Server (default: 19998)
    --data-dir PATH     Data directory (与 Gateway 共用)
    --gateway-url URL   Gateway URL (default: http://127.0.0.1:19999)

Queue Service options:
    --port PORT         Port for Queue Service (default: 19997)
    --data-dir PATH     Data directory (与 Gateway 共用)

Watchdog options:
    --gateway-url URL       Gateway URL (default: http://127.0.0.1:19999)
    --queue-service-url URL Queue Service URL (default: http://127.0.0.1:19997)

Task Worker options:
    --gateway-url URL       Gateway URL (default: http://127.0.0.1:19999)
    --queue-service-url URL Queue Service URL (default: http://127.0.0.1:19997)
    --num-workers N         Number of worker threads (default: 5)

Saga Worker options:
    --gateway-url URL       Gateway URL (default: http://127.0.0.1:19999)
    --queue-service-url URL Queue Service URL (default: http://127.0.0.1:19997)
    --max-concurrent N      Max concurrent sagas (default: 10)

Health Worker options:
    --queue-service-url URL Queue Service URL (default: http://127.0.0.1:19997)

Scheduler Worker options:
    --gateway-url URL       Gateway URL (default: http://127.0.0.1:19999)
    --check-interval SECS   Check interval in seconds (default: 10.0)

VMControl options:
    --port PORT         Port for VMControl (default: 8080)
    --host HOST         Host to bind to (default: 127.0.0.1)
    --vmcontrol-bin     Path to vmcontrol binary (default: auto-detect)

File Service options:
    --port PORT         Port for File Service (default: 19995)
    --base-dir PATH     Base data directory (default: NOVAIC_DATA_DIR/files)

Tool Result Service options:
    --port PORT         Port (default: 19994)
    --data-dir PATH     Data directory (sets NOVAIC_DATA_DIR)

Examples:
    novaic-backend gateway --port 19999
    novaic-backend tools-server --port 19998
    novaic-backend queue-service --port 19997
    novaic-backend watchdog --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
    novaic-backend task-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
    novaic-backend saga-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997
    novaic-backend health --queue-service-url http://127.0.0.1:19997
    novaic-backend scheduler --gateway-url http://127.0.0.1:19999
    novaic-backend vmcontrol --port 8080
""")


def run_gateway():
    """Run the Gateway server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Gateway Server")
    parser.add_argument("--port", type=int, default=ServiceConfig.GATEWAY_PORT, help="Port to listen on")
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


def run_tools_server():
    """Run the Tools Server (HTTP API for tools, replaces MCP Gateway)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Tools Server")
    parser.add_argument("--port", type=int, default=ServiceConfig.TOOLS_SERVER_PORT, help=f"Port for Tools Server (default: {ServiceConfig.TOOLS_SERVER_PORT})")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    parser.add_argument("--gateway-url", help=f"Gateway URL (default: {ServiceConfig.GATEWAY_URL})")
    args = parser.parse_args()
    
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[Tools Server] ERROR: NOVAIC_DATA_DIR required (use --data-dir or set env)")
        sys.exit(1)
    
    os.environ["NOVAIC_TOOLS_PORT"] = str(args.port)
    if args.gateway_url:
        os.environ["GATEWAY_URL"] = args.gateway_url
    elif not os.environ.get("GATEWAY_URL"):
        os.environ["GATEWAY_URL"] = ServiceConfig.GATEWAY_URL
    
    from main_tools import app
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


def run_queue_service():
    """Run the Queue Service (Task/Saga queue management)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Queue Service")
    parser.add_argument("--port", type=int, default=ServiceConfig.QUEUE_SERVICE_PORT, help=f"Port for Queue Service (default: {ServiceConfig.QUEUE_SERVICE_PORT})")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    args = parser.parse_args()
    
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[Queue Service] ERROR: NOVAIC_DATA_DIR required (use --data-dir or set env)")
        sys.exit(1)
    os.environ["NOVAIC_QUEUE_PORT"] = str(args.port)
    
    from queue_service.main import app
    import uvicorn
    
    print(f"[Queue Service] Starting on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


def run_watchdog():
    """Run the Watchdog service (message monitor)."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Watchdog Service")
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--queue-service-url", default=ServiceConfig.QUEUE_SERVICE_URL, help="Queue Service URL")
    args = parser.parse_args()
    
    from task_queue.workers.watchdog import Watchdog
    
    worker = Watchdog(
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
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--queue-service-url", default=ServiceConfig.QUEUE_SERVICE_URL, help="Queue Service URL")
    parser.add_argument("--num-workers", type=int, default=ServiceConfig.NUM_WORKERS, help="Number of worker threads (reserved)")
    args = parser.parse_args()
    
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
    print(f"[task-worker] Num workers: {args.num_workers} (reserved)")
    
    worker.run()
    print("[task-worker] Shutdown complete")


def run_saga_worker():
    """Run the Saga Worker service."""
    # main_saga.py 已经使用 argparse 处理所有参数：
    # --gateway-url, --queue-service-url, --max-concurrent
    # 直接调用即可，argv 已在 main() 中处理好
    from main_saga import main as saga_run
    saga_run()


def run_health():
    """Run the Health Worker service."""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="NovAIC Health Worker Service")
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL (accepted but not used)")
    parser.add_argument("--queue-service-url", default=ServiceConfig.QUEUE_SERVICE_URL, help="Queue Service URL")
    parser.add_argument("--check-interval", type=float, default=30.0, help="Health check interval in seconds")
    parser.add_argument("--task-timeout", type=int, default=ServiceConfig.TASK_TIMEOUT, help="Task timeout in seconds")
    parser.add_argument("--saga-timeout", type=int, default=ServiceConfig.SAGA_TIMEOUT, help="Saga timeout in seconds")
    args = parser.parse_args()
    
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
    parser.add_argument("--gateway-url", default=ServiceConfig.GATEWAY_URL, help="Gateway URL")
    parser.add_argument("--check-interval", type=float, default=10.0, help="Check interval in seconds")
    args = parser.parse_args()
    
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
    parser.add_argument("--port", type=int, default=ServiceConfig.FILE_SERVICE_PORT, help=f"Port for File Service (default: {ServiceConfig.FILE_SERVICE_PORT})")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    args = parser.parse_args()
    
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[File Service] ERROR: NOVAIC_DATA_DIR required (use --data-dir or set env)")
        sys.exit(1)
    
    os.environ["FILE_SERVICE_PORT"] = str(args.port)
    
    from file_service.main import create_app
    import uvicorn
    
    base_dir = os.environ["NOVAIC_DATA_DIR"]
    app = create_app(base_dir=base_dir)
    
    print(f"[File Service] Starting on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


def run_tool_result_service():
    """Run the Tool Result Service (result normalization)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NovAIC Tool Result Service")
    parser.add_argument("--port", type=int, default=ServiceConfig.TOOL_RESULT_SERVICE_PORT, help=f"Port (default: {ServiceConfig.TOOL_RESULT_SERVICE_PORT})")
    parser.add_argument("--data-dir", help="Data directory (overrides NOVAIC_DATA_DIR)")
    args = parser.parse_args()
    
    if args.data_dir:
        os.environ["NOVAIC_DATA_DIR"] = args.data_dir
    if not os.environ.get("NOVAIC_DATA_DIR"):
        print("[Tool Result Service] ERROR: NOVAIC_DATA_DIR required (use --data-dir or set env)")
        sys.exit(1)
    
    os.environ["TOOL_RESULT_SERVICE_PORT"] = str(args.port)
    
    from tool_result_service.main import create_app
    import uvicorn
    
    app = create_app()
    print(f"[Tool Result Service] Starting on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


def run_vmcontrol():
    """Run the VMControl service (Rust binary)."""
    import argparse
    import subprocess
    import shutil
    from pathlib import Path
    import time
    import requests
    
    parser = argparse.ArgumentParser(description="NovAIC VMControl Service")
    parser.add_argument("--port", type=int, default=ServiceConfig.VMCONTROL_PORT, help=f"Port for VMControl (default: {ServiceConfig.VMCONTROL_PORT})")
    parser.add_argument("--host", default=ServiceConfig.VMCONTROL_HOST, help=f"Host to bind to (default: {ServiceConfig.VMCONTROL_HOST})")
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


def _setup_worker_logging(mode: str):
    """Setup file logging for worker processes.
    
    Worker processes in binary mode have stdout/stderr set to null by Tauri.
    This redirects output to a log file so we can debug startup failures.
    """
    data_dir = os.environ.get("NOVAIC_DATA_DIR")
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
    
    # Validate configuration
    try:
        ServiceConfig.validate()
        print(f"[Config] Gateway: {ServiceConfig.GATEWAY_URL}")
        print(f"[Config] Queue Service: {ServiceConfig.QUEUE_SERVICE_URL}")
        print(f"[Config] Tools Server: {ServiceConfig.TOOLS_SERVER_URL}")
        print(f"[Config] VMControl: {ServiceConfig.VMCONTROL_URL}")
        print(f"[Config] File Service: {ServiceConfig.FILE_SERVICE_URL}")
        print(f"[Config] Tool Result Service: {ServiceConfig.TOOL_RESULT_SERVICE_URL}")
    except ValueError as e:
        print(f"[Config] Configuration error: {e}")
        sys.exit(1)
    
    # Parse mode
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    # Remove mode from argv so argparse in sub-commands works correctly
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    # Setup file logging for worker processes (stdout is null in binary mode)
    # Gateway, Tools Server, Queue Service handle their own logging
    if mode in ("watchdog", "task-worker", "saga-worker", "health", "scheduler"):
        _setup_worker_logging(mode)
    
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
