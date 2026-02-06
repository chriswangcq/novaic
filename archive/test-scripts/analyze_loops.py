#!/usr/bin/env python3
"""
分析测试1中有几个agent loop，每个loop处理了什么
"""

import httpx
import time
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"

# 清理
conn = sqlite3.connect(str(DB_PATH))
conn.execute("DELETE FROM chat_messages")
conn.execute("DELETE FROM tq_tasks")
conn.execute("DELETE FROM tq_sagas")
conn.execute("DELETE FROM agent_runtimes")
conn.execute("UPDATE subagents SET status = 'sleeping'")
conn.commit()
conn.close()

client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False)

print("="*70)
print("Agent Loop 分析测试")
print("="*70)

print("\n1. 创建 Agent...")
r = client.post("/api/agents", json={"name": "TestAgent", "model": "kimi-k2.5"})
agent_id = r.json()['id']
print(f"   Agent ID: {agent_id[:12]}")

print("\n2. 连续发送3条消息...")
for i in range(1, 4):
    msg = f"消息#{i}: 请简短回复收到"
    print(f"   发送: {msg}")
    r = client.post("/api/chat/send", json={"message": msg})
    time.sleep(1)

print("\n3. 等待处理...")
time.sleep(15)

print("\n4. 分析 Agent Loop")
print("="*70)

conn = sqlite3.connect(str(DB_PATH))

# 查看所有react_think sagas
cursor = conn.execute("""
    SELECT 
        id,
        saga_type,
        context,
        step_results,
        created_at
    FROM tq_sagas 
    WHERE saga_type IN ('react_think', 'react_actions')
    AND created_at > datetime('now', '-2 minutes')
    ORDER BY created_at
""")

import json

loop_num = 0
for row in cursor:
    saga_id, saga_type, context_str, step_results_str, created_at = row
    
    if saga_type == 'react_think':
        loop_num += 1
        print(f"\n{'='*70}")
        print(f"🔵 Agent Loop #{loop_num}")
        print(f"{'='*70}")
        print(f"Saga ID: {saga_id[:12]}")
        print(f"时间: {created_at}")
        
        # 解析step_results获取context.read的结果
        try:
            step_results = json.loads(step_results_str) if step_results_str else {}
            
            # Step 1 通常是 context.read
            if 'read_context' in step_results:
                read_result = step_results['read_context']
                if isinstance(read_result, dict):
                    new_messages = read_result.get('new_messages', [])
                    context_data = read_result.get('context', [])
                    
                    print(f"\n📚 Context.Read 结果:")
                    print(f"   - 新消息数: {len(new_messages)}")
                    print(f"   - Context总长度: {len(context_data)}")
                    
                    if new_messages:
                        print(f"\n   📨 新消息内容:")
                        for i, msg in enumerate(new_messages, 1):
                            content = msg.get('content', '')
                            msg_id = msg.get('id', 'N/A')[:12]
                            print(f"      {i}. [{msg_id}] {content}")
                    
                    # 统计context中的user消息
                    user_msgs = [m for m in context_data if m.get('role') == 'user']
                    print(f"\n   👤 Context中用户消息总数: {len(user_msgs)}")
            
            # Step 2 是 llm.call
            if 'call_llm' in step_results:
                llm_result = step_results['call_llm']
                if isinstance(llm_result, dict) and llm_result.get('success'):
                    response = llm_result.get('response', {})
                    choices = response.get('choices', [])
                    if choices:
                        message = choices[0].get('message', {})
                        reply_content = message.get('content', '')
                        print(f"\n💬 AI回复:")
                        print(f"   {reply_content[:100]}")
                        
        except Exception as e:
            print(f"   ⚠️  解析错误: {e}")

# 查看最终的chat_messages
print(f"\n{'='*70}")
print("📊 最终结果统计")
print(f"{'='*70}")

cursor = conn.execute("""
    SELECT type, COUNT(*) as count
    FROM chat_messages
    GROUP BY type
""")
for row in cursor:
    msg_type, count = row
    print(f"{msg_type}: {count} 条")

print(f"\n💬 AI回复内容:")
cursor = conn.execute("""
    SELECT content
    FROM chat_messages
    WHERE type = 'AGENT_REPLY'
    ORDER BY created_at
""")
for i, row in enumerate(cursor, 1):
    print(f"{i}. {row[0]}")

conn.close()
client.close()

print(f"\n{'='*70}")
print(f"✅ 总计: {loop_num} 个 Agent Loop")
print(f"{'='*70}")
