#!/usr/bin/env python3
"""
深度追踪 context.read 的行为
"""

import httpx
import time
import sqlite3
from pathlib import Path
import json

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
print("Context.Read 深度追踪")
print("="*70)

# 创建 Agent
print("\n1. 创建 Agent...")
r = client.post("/api/agents", json={"name": "TraceAgent", "model": "kimi-k2.5"})
agent_data = r.json()
agent_id = agent_data['id']
print(f"   Agent ID: {agent_id[:12]}")

# 发送3条消息
print("\n2. 发送3条消息...")
for i in range(1, 4):
    msg = f"消息#{i}"
    print(f"   发送: {msg}")
    r = client.post("/api/chat/send", json={"message": msg})
    time.sleep(0.5)

print("\n3. 等待处理...")
time.sleep(15)

print("\n4. 分析每个 context.read 任务")
print("="*70)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# 查询所有 context.read 任务
cursor = conn.execute("""
    SELECT 
        id,
        payload,
        result,
        created_at
    FROM tq_tasks 
    WHERE topic = 'context.read'
    AND created_at > datetime('now', '-2 minutes')
    ORDER BY created_at
""")

read_tasks = cursor.fetchall()
print(f"\n找到 {len(read_tasks)} 个 context.read 任务\n")

for i, task in enumerate(read_tasks, 1):
    print(f"{'='*70}")
    print(f"context.read 任务 #{i}")
    print(f"{'='*70}")
    print(f"Task ID: {task['id'][:12]}")
    print(f"时间: {task['created_at']}")
    
    try:
        payload = json.loads(task['payload'])
        result = json.loads(task['result']) if task['result'] else {}
        
        runtime_id = payload.get('runtime_id', 'N/A')
        print(f"Runtime ID: {runtime_id[:12]}")
        
        # 分析结果
        if result.get('success'):
            context = result.get('context', [])
            new_messages = result.get('new_messages', [])
            
            print(f"\n📊 结果:")
            print(f"   - Context 总长度: {len(context)}")
            print(f"   - 新消息数: {len(new_messages)}")
            
            # 统计 context 中的角色
            user_msgs = [m for m in context if m.get('role') == 'user']
            asst_msgs = [m for m in context if m.get('role') == 'assistant']
            tool_msgs = [m for m in context if m.get('role') == 'tool']
            
            print(f"\n   Context 组成:")
            print(f"     - user: {len(user_msgs)} 条")
            print(f"     - assistant: {len(asst_msgs)} 条")
            print(f"     - tool: {len(tool_msgs)} 条")
            
            if new_messages:
                print(f"\n   📨 新消息:")
                for j, msg in enumerate(new_messages, 1):
                    content = msg.get('content', '')
                    msg_id = msg.get('id', 'N/A')[:12]
                    print(f"      {j}. [{msg_id}] {content}")
            else:
                print(f"\n   ⚠️  new_messages 为空，但 context 长度={len(context)}")
            
            # 检查对应时刻的数据库状态
            print(f"\n   📋 此时数据库状态:")
            cursor2 = conn.execute("""
                SELECT id, content, status, read
                FROM chat_messages
                WHERE agent_id = ? AND type = 'USER_MESSAGE'
                ORDER BY created_at
            """, (agent_id,))
            
            db_messages = cursor2.fetchall()
            print(f"      总共 {len(db_messages)} 条用户消息:")
            for msg_row in db_messages:
                mid = msg_row['id'][:12]
                content = msg_row['content']
                status = msg_row['status']
                read = msg_row['read']
                print(f"         [{mid}] {content:20} | status={status:7} | read={read}")
        else:
            print(f"   ❌ 失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ⚠️  解析错误: {e}")
    
    print()

# 查看最终的 runtime context
print(f"\n{'='*70}")
print("最终 Runtime Context")
print(f"{'='*70}")

cursor = conn.execute("""
    SELECT context
    FROM agent_runtimes
    WHERE agent_id = ?
    ORDER BY created_at DESC
    LIMIT 1
""", (agent_id,))

row = cursor.fetchone()
if row:
    final_context = json.loads(row['context'])
    print(f"总长度: {len(final_context)}\n")
    
    for i, msg in enumerate(final_context, 1):
        role = msg.get('role', '?')
        content = str(msg.get('content', ''))
        if len(content) > 60:
            content = content[:60] + '...'
        print(f"{i:2}. [{role:10}] {content}")

conn.close()
client.close()

print(f"\n{'='*70}")
print("追踪完成")
print(f"{'='*70}")
