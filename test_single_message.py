#!/usr/bin/env python3
"""
简单测试：发送一条明确的消息，检查AI回复
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

print("1. 创建 Agent...")
r = client.post("/api/agents", json={"name": "TestAgent", "model": "kimi-k2.5"})
agent_id = r.json()['id']
print(f"   Agent ID: {agent_id[:12]}\n")

print("2. 发送明确的消息...")
message = "你好！我是用户小明。请你回复：'你好小明，我是AI助手。'"
r = client.post("/api/chat/send", json={"message": message})
msg_id = r.json()['message_id']
print(f"   发送: {message}")
print(f"   Message ID: {msg_id[:12]}\n")

print("3. 等待处理...")
time.sleep(15)

print("4. 检查结果\n")
print("="*70)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# 用户消息
cursor = conn.execute("SELECT content FROM chat_messages WHERE type='USER_MESSAGE' ORDER BY created_at")
user_msgs = cursor.fetchall()
print(f"用户消息 ({len(user_msgs)} 条):")
for msg in user_msgs:
    print(f"  - {msg['content']}")

# AI回复
cursor = conn.execute("SELECT content FROM chat_messages WHERE type='AGENT_REPLY' ORDER BY created_at")
ai_msgs = cursor.fetchall()
print(f"\nAI回复 ({len(ai_msgs)} 条):")
for msg in ai_msgs:
    print(f"  - {msg['content']}")

# 检查回复是否符合预期
print("\n" + "="*70)
if len(ai_msgs) == 0:
    print("❌ 没有收到AI回复")
elif len(ai_msgs) == 1:
    reply = ai_msgs[0]['content']
    if '小明' in reply and ('AI助手' in reply or '助手' in reply):
        print("✅ AI回复符合预期")
    else:
        print("⚠️  AI回复内容不完全符合预期")
        print(f"   期望包含：'小明' 和 'AI助手'")
        print(f"   实际回复：{reply}")
else:
    print(f"⚠️  收到 {len(ai_msgs)} 条AI回复（期望1条）")

conn.close()
client.close()
