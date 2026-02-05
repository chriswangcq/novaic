"""
Task Worker 启动入口 (同步版本)

通用任务执行器，处理所有 task_queue 中的任务。
"""

import os
import sys
import signal
import argparse

# 设置环境
os.environ['no_proxy'] = 'localhost,127.0.0.1,::1'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,::1'


# 默认处理的 topics（所有 handler 需要在此注册）
DEFAULT_TOPICS = [
    # SubAgent lifecycle
    "subagent.wake",
    "subagent.set_awake",
    "subagent.set_sleeping",
    # Runtime lifecycle
    "runtime.create",
    "runtime.update_phase",
    "runtime.set_status",
    "runtime.increment_round",
    "runtime.set_summarized",
    "runtime.set_need_rest",
    "runtime.check_new_messages",
    # MCP lifecycle
    "mcp.create",
    "mcp.destroy",
    # LLM calls
    "llm.call",
    "llm.call_summary",
    # Tool execution
    "tool.execute",
    # Context operations
    "context.append",
    "context.get",
    "context.read",
    # Message processing
    "message.claim",
    "message.route",
    "message.process",
    # Saga triggers
    "saga.trigger",
]


def main():
    from task_queue.workers.task_worker_sync import TaskWorkerSync
    
    parser = argparse.ArgumentParser(description="Task Worker (sync)")
    parser.add_argument("--gateway-url", default="http://127.0.0.1:19999", help="Gateway URL")
    parser.add_argument("--queue-service-url", default="http://127.0.0.1:19997", help="Queue Service URL")
    parser.add_argument("--num-workers", type=int, default=5, help="Number of workers")
    args = parser.parse_args()
    
    gateway_url = args.gateway_url
    queue_service_url = args.queue_service_url
    topics = DEFAULT_TOPICS
    
    worker = TaskWorkerSync(
        topics=topics,
        queue_service_url=queue_service_url,
        gateway_url=gateway_url,
    )
    
    # 信号处理
    def shutdown_handler(signum, frame):
        print("[main_task] Received shutdown signal")
        worker.shutdown()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    print(f"[main_task] Starting TaskWorker (sync)...")
    print(f"[main_task] Gateway URL: {gateway_url}")
    print(f"[main_task] Queue Service URL: {queue_service_url}")
    print(f"[main_task] Topics: {topics}")
    
    worker.run()
    
    print("[main_task] Shutdown complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
