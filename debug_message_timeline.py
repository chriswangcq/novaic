#!/usr/bin/env python3
"""
调试消息时间线 - 跟踪每条消息的状态变化
"""

import httpx
import time
import sqlite3
import json
from pathlib import Path

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"


def log(msg):
    print(f"[{time.time():.2f}] {msg}")


def get_message_status():
    """获取所有消息的当前状态"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.execute("""
        SELECT id, type, status, read, content, created_at
        FROM chat_messages
        ORDER BY created_at
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def cleanup():
    """清理数据"""
    log("清理测试数据...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM chat_messages")
    conn.execute("DELETE FROM tq_tasks")
    conn.execute("DELETE FROM tq_sagas")
    conn.execute("DELETE FROM agent_runtimes")
    conn.execute("UPDATE subagents SET status = 'sleeping'")
    conn.commit()
    conn.close()
    log("清理完成\n")


def test():
    cleanup()
    time.sleep(1)
    
    client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False)
    
    # 创建 agent
    log("1. 创建 Agent...")
    r = client.post("/api/agents", json={"name": "Debug", "model": "kimi-k2.5"})
    agent = r.json()
    agent_id = agent['id']
    log(f"   Agent ID: {agent_id[:12]}\n")
    
    # 发送3条消息
    log("2. 发送3条消息...")
    for i in range(3):
        r = client.post("/api/chat/send", json={
            "message": f"消息{i+1}: 1+{i+1}等于几？"
        })
        msg_id = r.json()['message_id']
        log(f"   消息{i+1} 已发送: {msg_id[:12]}")
        time.sleep(0.5)
    
    log("\n3. 观察消息状态变化...")
    
    # 跟踪10秒钟，每0.5秒检查一次
    for t in range(20):
        time.sleep(0.5)
        
        messages = get_message_status()
        
        # 只显示变化
        status_str = " | ".join([
            f"{msg[1][:4]}:{msg[2][:4]}/r={msg[3]}"
            for msg in messages if msg[1] != 'AGENT_REPLY'
        ])
        
        if status_str:
            log(f"   [{t*0.5:4.1f}s] {status_str}")
        
        # 检查是否都已读
        all_read = all(msg[3] == 1 for msg in messages if msg[1] == 'USER_MESSAGE')
        if all_read and len([m for m in messages if m[1] == 'USER_MESSAGE']) == 3:
            log(f"\n   ✓ 所有用户消息都已被读取")
            break
    
    # 等待处理完成
    log("\n4. 等待处理完成...")
    time.sleep(5)
    
    # 检查最终结果
    log("\n" + "="*70)
    log("最终结果")
    log("="*70)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # 所有消息
    cursor = conn.execute("""
        SELECT id, type, status, read, content
        FROM chat_messages
        ORDER BY created_at
    """)
    messages = cursor.fetchall()
    
    user_msgs = [m for m in messages if m['type'] == 'USER_MESSAGE']
    ai_msgs = [m for m in messages if m['type'] == 'AGENT_REPLY']
    
    log(f"\n用户消息: {len(user_msgs)} 条")
    for i, m in enumerate(user_msgs, 1):
        log(f"  {i}. status={m['status']:7} read={m['read']}  {m['content']}")
    
    log(f"\nAI回复: {len(ai_msgs)} 条")
    for i, m in enumerate(ai_msgs, 1):
        log(f"  {i}. {m['content'][:60]}")
    
    # 检查 runtime context
    cursor = conn.execute("""
        SELECT runtime_id, context
        FROM agent_runtimes
        ORDER BY created_at DESC
        LIMIT 1
    """)
    runtime = cursor.fetchone()
    
    if runtime:
        context = json.loads(runtime['context'])
        user_in_context = [msg for msg in context if msg.get('role') == 'user']
        log(f"\nRuntime Context 中的用户消息: {len(user_in_context)} 条")
        for i, msg in enumerate(user_in_context, 1):
            log(f"  {i}. {msg.get('content', '')[:50]}")
    
    conn.close()
    client.close()


if __name__ == "__main__":
    test()
