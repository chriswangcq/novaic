"""
Task Worker v2 启动入口

通用任务执行器，处理所有 task_queue 中的任务。
"""

import asyncio
import os
import sys
import signal

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


async def main():
    from task_queue.workers.task_worker_v2 import TaskWorkerV2
    
    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
    topics_str = os.environ.get("TASK_TOPICS", "")
    
    topics = topics_str.split(",") if topics_str else DEFAULT_TOPICS
    
    worker = TaskWorkerV2(
        topics=topics,
        gateway_url=gateway_url,
        poll_interval=0.1,
        heartbeat_interval=10.0,
    )
    
    # 信号处理
    loop = asyncio.get_running_loop()
    
    def shutdown_handler():
        print("[main_task] Received shutdown signal")
        asyncio.create_task(worker.shutdown())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler)
    
    print(f"[main_task] Starting TaskWorker v2...")
    print(f"[main_task] Gateway URL: {gateway_url}")
    print(f"[main_task] Topics: {topics}")
    
    await worker.run()
    
    print("[main_task] Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
