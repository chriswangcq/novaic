#!/usr/bin/env python3
"""
测试1的内容验证：检查AI是否在回复中处理了所有3条消息
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
print("测试1: 多条消息连续发送 - 内容验证")
print("="*70)

print("\n1. 创建 Agent...")
r = client.post("/api/agents", json={"name": "MultiMsgAgent", "model": "kimi-k2.5"})
agent_id = r.json()['id']
print(f"   Agent ID: {agent_id[:12]}")

print("\n2. 连续发送3条消息...")
messages = [
    "消息#1: 请简短回复收到",
    "消息#2: 请简短回复收到", 
    "消息#3: 请简短回复收到"
]

for i, msg in enumerate(messages, 1):
    print(f"   发送: {msg}")
    r = client.post("/api/chat/send", json={"message": msg})
    time.sleep(1)

print("\n3. 等待处理...")
time.sleep(15)

print("\n4. 检查结果")
print("="*70)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# 用户消息
cursor = conn.execute("""
    SELECT content FROM chat_messages 
    WHERE type='USER_MESSAGE' AND agent_id=?
    ORDER BY created_at
""", (agent_id,))
user_msgs = cursor.fetchall()
print(f"\n用户消息 ({len(user_msgs)} 条):")
for msg in user_msgs:
    print(f"  - {msg['content']}")

# AI回复
cursor = conn.execute("""
    SELECT content FROM chat_messages 
    WHERE type='AGENT_REPLY' AND agent_id=?
    ORDER BY created_at
""", (agent_id,))
ai_msgs = cursor.fetchall()
print(f"\nAI回复 ({len(ai_msgs)} 条):")
for i, msg in enumerate(ai_msgs, 1):
    print(f"\n--- 回复 {i} ---")
    print(msg['content'])
    print("-" * 40)

# 内容分析
print("\n" + "="*70)
print("内容分析:")
print("="*70)

if len(ai_msgs) == 0:
    print("❌ 没有收到AI回复")
else:
    # 检查所有回复内容，看是否提到了所有3条消息
    all_replies = "\n".join([msg['content'] for msg in ai_msgs])
    
    found_count = 0
    for i in range(1, 4):
        if f"消息#{i}" in all_replies or f"第{i}条" in all_replies or f"#{i}" in all_replies:
            found_count += 1
            print(f"✅ 回复中提到了消息#{i}")
        else:
            print(f"⚠️  回复中未明确提到消息#{i}")
    
    print(f"\n总结:")
    print(f"  - 发送了 {len(user_msgs)} 条用户消息")
    print(f"  - 收到了 {len(ai_msgs)} 条AI回复")
    print(f"  - 回复内容中明确提到了 {found_count} 条消息")
    
    if found_count == 3:
        print("\n✅ AI正确处理了所有3条消息（批处理正常）")
    elif len(ai_msgs) == 3:
        print("\n✅ AI为每条消息分别回复（独立处理）")
    else:
        print(f"\n⚠️  需要人工检查回复内容")

# 检查runtime context
cursor = conn.execute("""
    SELECT context FROM agent_runtimes 
    WHERE agent_id=?
    ORDER BY created_at DESC LIMIT 1
""", (agent_id,))
row = cursor.fetchone()
if row:
    import json
    context = json.loads(row['context'])
    user_messages_in_context = [m for m in context if m.get('role') == 'user']
    print(f"\nRuntime Context 中的用户消息: {len(user_messages_in_context)} 条")
    if len(user_messages_in_context) == 3:
        print("✅ 所有3条消息都已进入context（没有消息丢失）")

conn.close()
client.close()
