#!/usr/bin/env python3
"""
验证批处理逻辑 - AI 是否正确处理了多条消息
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


def test_batch_processing():
    """验证：快速发送3条消息，AI应该在1次回复中处理所有3条"""
    log("\n" + "="*70)
    log("验证批处理逻辑")
    log("="*70)
    
    cleanup()
    time.sleep(2)
    
    client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False)
    
    # 创建 agent
    log("\n1. 创建 Agent...")
    r = client.post("/api/agents", json={"name": "BatchTest", "model": "kimi-k2.5"})
    agent = r.json()
    agent_id = agent['id']
    log(f"   Agent ID: {agent_id[:12]}")
    
    # 快速发送3条不同的消息
    log("\n2. 快速发送3条消息...")
    messages = [
        "第一条：请告诉我1+1等于几",
        "第二条：请告诉我2+2等于几", 
        "第三条：请告诉我3+3等于几"
    ]
    
    msg_ids = []
    for i, content in enumerate(messages):
        r = client.post("/api/chat/send", json={"message": content})
        data = r.json()
        msg_id = data['message_id']
        msg_ids.append(msg_id)
        log(f"   消息#{i+1}: {msg_id[:12]} - {content}")
        time.sleep(0.5)  # 快速发送，间隔0.5秒
    
    # 等待处理
    log("\n3. 等待处理...")
    time.sleep(20)
    
    # 分析结果
    log("\n" + "="*70)
    log("分析结果")
    log("="*70)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    # 查看所有消息
    log("\n=== 所有消息 ===")
    cursor = conn.execute("""
        SELECT id, type, status, read, content, created_at
        FROM chat_messages
        ORDER BY created_at
    """)
    user_messages = []
    ai_messages = []
    for row in cursor.fetchall():
        msg_type = row['type']
        content = row['content'][:60]
        if msg_type == 'USER_MESSAGE':
            user_messages.append(row)
            log(f"  [USER] read={row['read']} {content}")
        else:
            ai_messages.append(row)
            log(f"  [AI]   {content}")
    
    # 查看 react_think saga
    log("\n=== React Think Saga ===")
    cursor = conn.execute("""
        SELECT id, status, step_results, created_at
        FROM tq_sagas
        WHERE saga_type = 'react_think'
        ORDER BY created_at
    """)
    sagas = cursor.fetchall()
    log(f"  总数: {len(sagas)}")
    
    for i, saga in enumerate(sagas, 1):
        log(f"\n  Saga #{i}: {saga['id'][:12]} - {saga['status']}")
        if saga['step_results']:
            try:
                results = json.loads(saga['step_results'])
                
                # 查看 read_context 步骤
                if 'read_context' in results:
                    context = results['read_context'].get('context', [])
                    log(f"    read_context: {len(context)} 条消息")
                    
                    # 统计 user 消息
                    user_msgs_in_context = [msg for msg in context if msg.get('role') == 'user']
                    log(f"    其中 user 消息: {len(user_msgs_in_context)} 条")
                    for j, msg in enumerate(user_msgs_in_context[-3:], 1):  # 显示最后3条
                        log(f"      {j}. {msg.get('content', '')[:50]}")
                
                # 查看 call_llm 步骤
                if 'call_llm' in results:
                    llm_result = results['call_llm']
                    if llm_result.get('success'):
                        response = llm_result.get('response', {})
                        ai_content = response.get('content', '')
                        log(f"    LLM 回复: {ai_content[:100]}...")
                    else:
                        log(f"    LLM 失败: {llm_result.get('error')}")
                        
            except Exception as e:
                log(f"    解析失败: {e}")
    
    # 验证结果
    log("\n" + "="*70)
    log("验证结果")
    log("="*70)
    
    log(f"\n发送的消息数: {len(user_messages)}")
    log(f"AI 回复数: {len(ai_messages)}")
    log(f"React Think Saga 数: {len(sagas)}")
    
    # 检查 AI 回复是否涵盖了所有问题
    if ai_messages:
        log("\n检查 AI 回复内容:")
        for i, ai_msg in enumerate(ai_messages, 1):
            content = ai_msg['content']
            log(f"\n  AI 回复 #{i}:")
            log(f"    {content}")
            
            # 检查是否提到了 1+1, 2+2, 3+3
            mentions = []
            if '1+1' in content or '等于2' in content or '1加1' in content:
                mentions.append("1+1")
            if '2+2' in content or '等于4' in content or '2加2' in content:
                mentions.append("2+2")
            if '3+3' in content or '等于6' in content or '3加3' in content:
                mentions.append("3+3")
            
            if mentions:
                log(f"    涵盖的问题: {', '.join(mentions)}")
            else:
                log(f"    未明确回答问题")
    
    # 总结
    log("\n" + "="*70)
    log("结论")
    log("="*70)
    
    if len(sagas) == 1:
        log("✅ 所有3条消息被1个 react_think saga 处理（批处理成功）")
        if len(ai_messages) == 1:
            log("✅ AI 在1次回复中处理了所有消息")
        else:
            log(f"⚠️  AI 生成了 {len(ai_messages)} 条回复（可能是多轮）")
    elif len(sagas) > 1:
        log(f"⚠️  消息被分成了 {len(sagas)} 个批次处理")
        log("    这可能是因为消息到达时间差导致的")
    
    # 检查是否有未读消息
    unread = [m for m in user_messages if m['read'] == 0]
    if unread:
        log(f"⚠️  有 {len(unread)} 条消息未被处理")
    else:
        log("✅ 所有消息都已被读取")
    
    conn.close()
    client.close()


if __name__ == "__main__":
    test_batch_processing()
