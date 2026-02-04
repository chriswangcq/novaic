#!/usr/bin/env python3
"""
单个测试场景 - 用于详细分析
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
    log("清理完成")


def print_stats():
    """打印统计"""
    conn = sqlite3.connect(str(DB_PATH))
    
    log("\n=== 消息统计 ===")
    cursor = conn.execute("""
        SELECT type, status, COUNT(*) as count
        FROM chat_messages
        GROUP BY type, status
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}/{row[1]}: {row[2]}")
    
    log("\n=== Saga 统计 ===")
    cursor = conn.execute("""
        SELECT saga_type, status, COUNT(*) as count
        FROM tq_sagas
        GROUP BY saga_type, status
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}/{row[1]}: {row[2]}")
    
    log("\n=== Task 统计 ===")
    cursor = conn.execute("""
        SELECT topic, status, COUNT(*) as count
        FROM tq_tasks
        GROUP BY topic, status
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}/{row[1]}: {row[2]}")
    
    conn.close()


def test_multiple_messages():
    """测试：多条消息快速发送"""
    log("\n" + "="*70)
    log("测试：快速发送3条消息")
    log("="*70)
    
    cleanup()
    time.sleep(2)
    
    client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0)
    
    # 创建 agent
    log("创建 Agent...")
    r = client.post("/api/agents", json={"name": "TestAgent", "model": "kimi-k2.5"})
    log(f"Response status: {r.status_code}")
    log(f"Response text: {r.text[:200]}")
    agent = r.json()
    agent_id = agent['id']
    log(f"Agent ID: {agent_id}")
    
    # 发送3条消息
    log("\n发送消息...")
    msg_ids = []
    for i in range(3):
        r = client.post("/api/chat/send", json={
            "message": f"消息#{i+1}: 请简短回复'收到{i+1}'"
        })
        data = r.json()
        msg_id = data['message_id']
        msg_ids.append(msg_id)
        log(f"  发送消息#{i+1}: {msg_id[:12]}")
        time.sleep(1)  # 间隔1秒
    
    # 等待
    log("\n等待处理...")
    time.sleep(15)
    
    # 查看详细信息
    log("\n" + "="*70)
    log("详细信息")
    log("="*70)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # 所有消息
    log("\n=== 所有消息 ===")
    cursor = conn.execute("""
        SELECT id, type, status, content, timestamp
        FROM chat_messages
        ORDER BY timestamp
    """)
    for row in cursor.fetchall():
        log(f"  [{row['type']:15}] {row['status']:10} {row['content'][:40]}")
    
    # 所有 saga
    log("\n=== 所有 Saga ===")
    cursor = conn.execute("""
        SELECT id, saga_type, status, current_step, created_at
        FROM tq_sagas
        ORDER BY created_at
    """)
    for row in cursor.fetchall():
        log(f"  [{row['saga_type']:20}] {row['status']:10} step={row['current_step']}")
    
    # React think saga 的详细信息
    log("\n=== React Think Saga 详情 ===")
    cursor = conn.execute("""
        SELECT id, saga_type, status, step_results
        FROM tq_sagas
        WHERE saga_type = 'react_think'
    """)
    for row in cursor.fetchall():
        log(f"  Saga ID: {row['id'][:12]}")
        log(f"  Status: {row['status']}")
        if row['step_results']:
            try:
                results = json.loads(row['step_results'])
                log(f"  Step Results: {json.dumps(results, indent=4, ensure_ascii=False)}")
            except:
                log(f"  Step Results (raw): {row['step_results'][:200]}")
    
    # 统计
    print_stats()
    
    # AI 回复数
    cursor = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE type='AGENT_REPLY'")
    reply_count = cursor.fetchone()[0]
    log(f"\n{'='*70}")
    log(f"AI 回复数: {reply_count} / 3 (期望)")
    log(f"{'='*70}")
    
    conn.close()
    client.close()


if __name__ == "__main__":
    test_multiple_messages()
