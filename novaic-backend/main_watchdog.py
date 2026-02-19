"""
Watchdog Worker 启动入口

监控 sending 消息，触发 RuntimeStart Saga。
"""

import argparse
import os
import signal

# 设置网络环境（绕过代理）
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


def main():
    parser = argparse.ArgumentParser(description="Watchdog Worker - 监控 sending 消息")
    parser.add_argument(
        "--gateway-url",
        default="http://127.0.0.1:19999",
        help="Gateway URL (default: http://127.0.0.1:19999)",
    )
    parser.add_argument(
        "--queue-service-url",
        default="http://127.0.0.1:19997",
        help="Queue Service URL (default: http://127.0.0.1:19997)",
    )
    args = parser.parse_args()
    
    from task_queue.workers.watchdog_sync import WatchdogSync

    worker = WatchdogSync(
        gateway_url=args.gateway_url,
        queue_service_url=args.queue_service_url,
        poll_interval=0.1,
    )
    
    # 信号处理
    def shutdown_handler(signum, frame):
        print("[main_watchdog] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[main_watchdog] Starting Watchdog...")
    print(f"[main_watchdog] Gateway URL: {args.gateway_url}")
    print(f"[main_watchdog] Queue Service URL: {args.queue_service_url}")
    
    worker.run()
    
    print("[main_watchdog] Shutdown complete")


if __name__ == "__main__":
    main()
