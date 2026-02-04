#!/usr/bin/env python3
"""
测试：先发送1条消息，等待处理完成，再发送2条消息
验证后续消息能否被正确处理
"""

import httpx
import time
import sqlite3
import json
from pathlib import Path

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"


def log(msg):
    print(f"{msg}")


def cleanup():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM chat_messages")
    conn.execute("DELETE FROM tq_tasks")
    conn.execute("DELETE FROM tq_sagas")
    conn.execute("DELETE FROM agent_runtimes")
    conn.execute("UPDATE subagents SET status = 'sleeping'")
    conn.commit()
    conn.close()


def get_stats():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    user = conn.execute("SELECT COUNT(*) as cnt FROM chat_messages WHERE type='USER_MESSAGE'").fetchone()['cnt']
    ai = conn.execute("SELECT COUNT(*) as cnt FROM chat_messages WHERE type='AGENT_REPLY'").fetchone()['cnt']
    
    context_sql = """
        SELECT context FROM agent_runtimes 
        ORDER BY created_at DESC LIMIT 1
    """
    runtime = conn.execute(context_sql).fetchone()
    ctx_user_count = 0
    if runtime:
        try:
            context = json.loads(runtime['context'])
            ctx_user_count = len([m for m in context if m.get('role') == 'user'])
        except:
            pass
    
    conn.close()
    return user, ai, ctx_user_count


def test():
    log("\n" + "="*70)
    log("测试：先发1条，等处理完，再发2条")
    log("="*70 + "\n")
    
    cleanup()
    time.sleep(1)
    
    client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False)
    
    # 创建 agent
    log("1. 创建 Agent...")
    r = client.post("/api/agents", json={"name": "DelayTest", "model": "kimi-k2.5"})
    agent_id = r.json()['id']
    log(f"   Agent ID: {agent_id[:12]}\n")
    
    # 第1条消息
    log("2. 发送第1条消息...")
    r = client.post("/api/chat/send", json={"message": "第1个问题：1+1=?"})
    log(f"   消息已发送: {r.json()['message_id'][:12]}")
    
    # 等待处理完成
    log("\n3. 等待第1条消息处理完成...")
    time.sleep(10)
    
    user, ai, ctx = get_stats()
    log(f"   用户消息: {user}, AI回复: {ai}, Context中用户消息: {ctx}")
    
    # 再发送2条消息
    log("\n4. 再发送2条消息...")
    r = client.post("/api/chat/send", json={"message": "第2个问题：2+2=?"})
    log(f"   消息2已发送: {r.json()['message_id'][:12]}")
    time.sleep(0.5)
    
    r = client.post("/api/chat/send", json={"message": "第3个问题：3+3=?"})
    log(f"   消息3已发送: {r.json()['message_id'][:12]}")
    
    # 等待处理
    log("\n5. 等待后续消息处理...")
    time.sleep(10)
    
    user, ai, ctx = get_stats()
    log(f"   用户消息: {user}, AI回复: {ai}, Context中用户消息: {ctx}")
    
    # 检查详细结果
    log("\n" + "="*70)
    log("详细结果")
    log("="*70 + "\n")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # 所有用户消息
    log("用户消息:")
    cursor = conn.execute("""
        SELECT id, content, status, read
        FROM chat_messages
        WHERE type = 'USER_MESSAGE'
        ORDER BY created_at
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        log(f"  {i}. [{row['status']:7}/r={row['read']}] {row['content']}")
    
    # 所有AI回复
    log("\nAI回复:")
    cursor = conn.execute("""
        SELECT id, content
        FROM chat_messages
        WHERE type = 'AGENT_REPLY'
        ORDER BY created_at
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        log(f"  {i}. {row['content'][:60]}")
    
    # Runtime Context
    cursor = conn.execute("""
        SELECT context FROM agent_runtimes
        ORDER BY created_at DESC LIMIT 1
    """)
    runtime = cursor.fetchone()
    if runtime:
        try:
            context = json.loads(runtime['context'])
            user_msgs = [m for m in context if m.get('role') == 'user']
            log(f"\nRuntime Context 中的用户消息: {len(user_msgs)} 条")
            for i, msg in enumerate(user_msgs, 1):
                log(f"  {i}. {msg.get('content', '')[:50]}")
        except Exception as e:
            log(f"\n解析 context 失败: {e}")
    
    # 结论
    log("\n" + "="*70)
    log("结论")
    log("="*70)
    
    user, ai, ctx = get_stats()
    if user == 3 and ctx == 3:
        log("✅ 所有3条用户消息都进入了 Context")
    elif user == 3 and ctx < 3:
        log(f"❌ 有消息丢失：发送了{user}条，但Context中只有{ctx}条")
    
    if ai >= user:
        log(f"✅ AI回复数({ai})足够")
    else:
        log(f"⚠️  AI回复数({ai})少于消息数({user})")
    
    conn.close()
    client.close()


if __name__ == "__main__":
    test()
