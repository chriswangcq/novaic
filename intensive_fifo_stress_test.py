#!/usr/bin/env python3
"""
高强度 FIFO 锁压测

测试 FIFO 锁在极限负载下的表现
"""

import httpx
import threading
import time
import sys
import sqlite3

BASE_URL = "http://127.0.0.1:19999"
DB_PATH = "/Users/wangchaoqun/.novaic/novaic.db"


def send_messages_burst(agent_id, num_messages, results):
    """爆发式发送消息（无延迟）"""
    client = httpx.Client(trust_env=False, timeout=30.0)
    
    try:
        # 设置当前 Agent
        client.post(f"{BASE_URL}/api/agents/current", json={"agent_id": agent_id})
        
        success = 0
        fail = 0
        errors = []
        
        for i in range(num_messages):
            try:
                resp = client.post(
                    f"{BASE_URL}/api/chat/send",
                    json={"content": f"Burst test {i+1}"},
                    timeout=10.0,
                )
                
                if resp.status_code == 200:
                    success += 1
                else:
                    fail += 1
                    if len(errors) < 5:
                        errors.append(f"{resp.status_code}: {resp.text[:100]}")
                
            except Exception as e:
                fail += 1
                if len(errors) < 5:
                    errors.append(str(e)[:100])
        
        results[agent_id] = {
            "success": success,
            "fail": fail,
            "errors": errors
        }
        
    finally:
        client.close()


def check_database_health(wait_seconds=60):
    """检查数据库健康状况"""
    print(f"\n等待 {wait_seconds} 秒让系统处理...")
    time.sleep(wait_seconds)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # 检查卡住的 Task
        cursor = conn.execute("""
            SELECT COUNT(*) as cnt FROM tq_tasks 
            WHERE status IN ('claimed', 'running') 
            AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
        """)
        stuck_tasks = cursor.fetchone()['cnt']
        
        # 检查卡住的 Saga
        cursor = conn.execute("""
            SELECT COUNT(*) as cnt FROM tq_sagas 
            WHERE status IN ('claimed', 'running') 
            AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
        """)
        stuck_sagas = cursor.fetchone()['cnt']
        
        # 检查总的 Task/Saga 数量
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_tasks")
        total_tasks = cursor.fetchone()['cnt']
        
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_sagas")
        total_sagas = cursor.fetchone()['cnt']
        
        # 检查消息状态分布
        cursor = conn.execute("""
            SELECT status, COUNT(*) as cnt 
            FROM chat_messages 
            GROUP BY status
        """)
        message_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
        
        conn.close()
        
        print(f"\n数据库健康检查:")
        print(f"  Task 总数: {total_tasks}")
        print(f"  Saga 总数: {total_sagas}")
        print(f"  卡住的 Task: {stuck_tasks}")
        print(f"  卡住的 Saga: {stuck_sagas}")
        print(f"  消息状态分布: {message_status}")
        
        return stuck_tasks == 0 and stuck_sagas == 0
        
    except Exception as e:
        print(f"❌ 数据库健康检查失败: {e}")
        return False


def main():
    print("=" * 60)
    print("高强度 FIFO 锁压测")
    print("=" * 60)
    
    # 测试配置
    num_agents = 10
    messages_per_agent = 50
    total_messages = num_agents * messages_per_agent
    
    print(f"\n测试配置:")
    print(f"  Agent 数量: {num_agents}")
    print(f"  每个 Agent 消息数: {messages_per_agent}")
    print(f"  总消息数: {total_messages}")
    print(f"  发送模式: 爆发式（无延迟）")
    
    # 创建测试 Agent
    print(f"\n[1/3] 创建测试 Agent...")
    agents = [f"intensive-{i}" for i in range(num_agents)]
    
    client = httpx.Client(trust_env=False, timeout=10.0)
    for agent_id in agents:
        try:
            client.post(
                f"{BASE_URL}/api/agents",
                json={
                    "id": agent_id,
                    "name": f"Intensive Test {agent_id}",
                    "avatar": "🔥",
                }
            )
        except:
            pass  # 可能已存在
    client.close()
    
    # 爆发式发送消息
    print(f"\n[2/3] 爆发式发送消息...")
    results = {}
    threads = []
    start_time = time.time()
    
    for agent_id in agents:
        t = threading.Thread(
            target=send_messages_burst,
            args=(agent_id, messages_per_agent, results)
        )
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    # 统计结果
    total_success = sum(r["success"] for r in results.values())
    total_fail = sum(r["fail"] for r in results.values())
    
    print(f"\n发送结果:")
    print(f"  总耗时: {elapsed:.2f}s")
    print(f"  成功: {total_success}/{total_messages}")
    print(f"  失败: {total_fail}/{total_messages}")
    print(f"  成功率: {total_success/total_messages*100:.1f}%")
    print(f"  QPS: {total_success/elapsed:.2f}")
    
    # 显示失败详情
    if total_fail > 0:
        print(f"\n失败详情:")
        for agent_id, result in sorted(results.items()):
            if result["fail"] > 0:
                print(f"  {agent_id}: {result['fail']} failures")
                for error in result["errors"]:
                    print(f"    - {error}")
    
    # 检查数据库健康
    print(f"\n[3/3] 检查数据库健康...")
    db_healthy = check_database_health(wait_seconds=60)
    
    # 总结
    print("\n" + "=" * 60)
    if total_fail == 0 and db_healthy:
        print("✅ 高强度压测通过！")
        print(f"   成功处理 {total_success} 条消息")
        print(f"   无 Task/Saga 卡住")
        print(f"   QPS: {total_success/elapsed:.2f}")
        print("=" * 60)
        return 0
    elif total_fail > 0:
        print(f"⚠️  有 {total_fail} 条消息发送失败")
        print("=" * 60)
        return 1
    else:
        print("⚠️  有 Task/Saga 卡住")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
