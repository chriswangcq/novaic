#!/usr/bin/env python3
"""
测试 claim-and-prepare API 是否正确不设置 read
"""

import httpx
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"

# 清理
conn = sqlite3.connect(str(DB_PATH))
conn.execute("DELETE FROM chat_messages")
conn.commit()
conn.close()

# 创建测试消息
print("1. 创建 Agent...")
client = httpx.Client(base_url=GATEWAY_URL, timeout=10.0, trust_env=False)
r = client.post("/api/agents", json={"name": "Test", "model": "kimi-k2.5"})
agent_id = r.json()['id']
print(f"   Agent ID: {agent_id[:12]}")

print("\n2. 发送消息（会创建 sending 状态）...")
r = client.post("/api/chat/send", json={"message": "测试消息"})
msg_id = r.json()['message_id']
print(f"   Message ID: {msg_id[:12]}")

# 检查初始状态
conn = sqlite3.connect(str(DB_PATH))
row = conn.execute("SELECT status, read FROM chat_messages WHERE id = ?", (msg_id,)).fetchone()
print(f"\n3. 发送后状态: status={row[0]}, read={row[1]}")

# 等待 Watchdog claim (或手动 claim)
print("\n4. 调用 claim-and-prepare API...")
r = client.post(f"{GATEWAY_URL}/internal/messages/claim-and-prepare")
if r.status_code == 200:
    data = r.json()
    message = data.get('message')
    if message:
        print(f"   Claimed message: {message['id'][:12]}")
    else:
        print("   No message to claim")

# 检查 claim 后状态
row = conn.execute("SELECT status, read FROM chat_messages WHERE id = ?", (msg_id,)).fetchone()
print(f"\n5. Claim 后状态: status={row[0]}, read={row[1]}")

if row[1] == 0:
    print("   ✅ read 保持为 0（正确）")
else:
    print("   ❌ read 被设置为 1（错误！）")

conn.close()
client.close()
