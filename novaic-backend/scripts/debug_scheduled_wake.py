#!/usr/bin/env python3
"""
调试脚本：模拟 Scheduled Wake 时 LLM 收到的完整 context

用法：
    python scripts/debug_scheduled_wake.py <agent_id>
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_queue.client import GatewayInternalClient
from task_queue.utils.system_prompt import build_system_prompt
from task_queue.utils.context_builder import build_initial_context


def debug_scheduled_wake(agent_id: str, gateway_url: str = "http://127.0.0.1:19999"):
    """模拟 scheduled_wake 时 LLM 收到的 context"""
    
    client = GatewayInternalClient(gateway_url)
    
    print("=" * 80)
    print(f"调试 Scheduled Wake - Agent: {agent_id}")
    print("=" * 80)
    
    # 1. System Prompt (统一的)
    print("\n" + "=" * 40)
    print("1. SYSTEM PROMPT (统一)")
    print("=" * 40)
    try:
        sys_prompt = build_system_prompt(agent_id, client)
        print(sys_prompt[:2000] + "..." if len(sys_prompt) > 2000 else sys_prompt)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Initial Context (历史摘要)
    print("\n" + "=" * 40)
    print("2. INITIAL CONTEXT (历史摘要)")
    print("=" * 40)
    subagent_id = f"main-{agent_id[:8]}"
    try:
        initial_context = build_initial_context(agent_id, subagent_id, client)
        for i, ctx in enumerate(initial_context):
            role = ctx.get("role", "unknown")
            content = ctx.get("content", "")
            preview = content[:500] + "..." if len(content) > 500 else content
            print(f"\n[{i}] role={role}")
            print(preview)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 3. Wake Message (定时唤醒时写入 DB 的消息内容)
    print("\n" + "=" * 40)
    print("3. WAKE MESSAGE (定时唤醒时写入 DB 的消息内容)")
    print("=" * 40)
    try:
        from task_queue.utils.system_prompt import build_wake_message
        wake_msg = build_wake_message(agent_id, client)
        print(wake_msg)
        print("\n[说明] 这个消息会作为 SYSTEM_WAKE 类型写入 DB，")
        print("然后由 ReactThink 的 context.read 统一读取，和用户消息流程完全一致。")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. 最近的聊天消息
    print("\n" + "=" * 40)
    print("4. 最近的聊天消息 (会被读入 context)")
    print("=" * 40)
    try:
        # 获取最近消息
        history = client._request("GET", f"/api/agents/{agent_id}/chat/history", None, params={"limit": 10})
        messages = history.get("messages", [])
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            content = msg.get("content", "")[:100]
            timestamp = msg.get("timestamp", "")
            read = msg.get("read", False)
            print(f"  [{msg_type}] read={read} | {timestamp}")
            print(f"    {content}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 5. 问题分析
    print("\n" + "=" * 40)
    print("5. 问题分析")
    print("=" * 40)
    
    # 检查 SYSTEM_WAKE 消息
    try:
        history = client._request("GET", f"/api/agents/{agent_id}/chat/history", None, params={"limit": 20})
        messages = history.get("messages", [])
        system_wake_count = sum(1 for m in messages if m.get("type") == "SYSTEM_WAKE")
        if system_wake_count > 0:
            print(f"⚠️  发现 {system_wake_count} 条 SYSTEM_WAKE 消息在聊天历史中")
            print("   这些消息会被前端显示为 assistant 消息，造成 [Scheduled wake] 堆积")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/debug_scheduled_wake.py <agent_id>")
        print("\n可用的 agent_id:")
        # 尝试列出 agents
        try:
            client = GatewayInternalClient("http://127.0.0.1:19999")
            agents = client._request("GET", "/api/agents", None)
            for agent in agents.get("agents", []):
                print(f"  - {agent['id']}: {agent.get('name', 'unnamed')}")
        except Exception as e:
            print(f"  (无法获取 agent 列表: {e})")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    gateway_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:19999"
    
    debug_scheduled_wake(agent_id, gateway_url)
