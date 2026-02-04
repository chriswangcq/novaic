#!/usr/bin/env python3
"""
快速 FIFO 锁压测

测试新的 FIFO 锁在高并发下的表现
"""

import httpx
import threading
import time
from collections import defaultdict
import sys

BASE_URL = "http://127.0.0.1:19999"


def create_agent(client, agent_id):
    """创建一个 Agent"""
    try:
        resp = client.post(
            f"{BASE_URL}/api/agents",
            json={
                "id": agent_id,
                "name": f"Test Agent {agent_id}",
                "avatar": "🤖",
            },
            timeout=5.0,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"Failed to create agent {agent_id}: {e}")
        return False


def send_messages(agent_id, num_messages, delay, results):
    """给一个 Agent 发送多条消息"""
    client = httpx.Client(trust_env=False, timeout=30.0)
    
    try:
        # 设置当前 Agent
        client.post(f"{BASE_URL}/api/agents/current", json={"agent_id": agent_id})
        
        success_count = 0
        fail_count = 0
        
        for i in range(num_messages):
            try:
                resp = client.post(
                    f"{BASE_URL}/api/chat/send",
                    json={"content": f"Agent {agent_id} message {i+1}"},
                    timeout=10.0,
                )
                
                if resp.status_code == 200:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"❌ Agent {agent_id} message {i+1} failed: {resp.status_code}")
                
            except Exception as e:
                fail_count += 1
                print(f"❌ Agent {agent_id} message {i+1} error: {e}")
            
            if delay > 0:
                time.sleep(delay)
        
        results[agent_id] = {"success": success_count, "fail": fail_count}
        
    except Exception as e:
        print(f"❌ Thread for agent {agent_id} failed: {e}")
        results[agent_id] = {"success": 0, "fail": num_messages, "error": str(e)}
    finally:
        client.close()


def check_system_status():
    """检查系统状态"""
    try:
        client = httpx.Client(trust_env=False, timeout=5.0)
        
        # 尝试访问 API
        resp = client.get(f"{BASE_URL}/api/agents")
        print(f"  Gateway response: {resp.status_code}")
        if resp.status_code in [200, 404, 500]:  # 500 也可能是正常（没初始化）
            print("✅ Gateway is running")
            return True
        else:
            print(f"⚠️  Gateway check: {resp.status_code}, content: {resp.text[:200]}")
            return False
        
    except Exception as e:
        print(f"❌ System check failed: {e}")
        return False
    finally:
        client.close()


def analyze_database_locks(db_path="/Users/wangchaoqun/.novaic/novaic.db"):
    """分析数据库锁的使用情况"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 检查消息数量
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM chat_messages")
        message_count = cursor.fetchone()['cnt']
        
        # 检查 Task/Saga 数量
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_tasks")
        task_count = cursor.fetchone()['cnt']
        
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_sagas")
        saga_count = cursor.fetchone()['cnt']
        
        # 检查卡住的 Task/Saga
        cursor = conn.execute("""
            SELECT COUNT(*) as cnt FROM tq_tasks 
            WHERE status IN ('claimed', 'running') 
            AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
        """)
        stuck_tasks = cursor.fetchone()['cnt']
        
        cursor = conn.execute("""
            SELECT COUNT(*) as cnt FROM tq_sagas 
            WHERE status IN ('claimed', 'running') 
            AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
        """)
        stuck_sagas = cursor.fetchone()['cnt']
        
        print(f"\n数据库状态:")
        print(f"  消息数: {message_count}")
        print(f"  Task 数: {task_count}")
        print(f"  Saga 数: {saga_count}")
        print(f"  卡住的 Task: {stuck_tasks}")
        print(f"  卡住的 Saga: {stuck_sagas}")
        
        conn.close()
        
        return stuck_tasks == 0 and stuck_sagas == 0
        
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")
        return False


def main():
    print("=" * 60)
    print("FIFO 锁快速压测")
    print("=" * 60)
    
    # 检查系统状态
    print("\n[1/5] 检查系统状态...")
    if not check_system_status():
        print("❌ 系统状态检查失败！")
        return 1
    
    # 创建测试 Agent
    print("\n[2/5] 创建测试 Agent...")
    num_agents = 5
    agents = [f"fifo-test-{i}" for i in range(num_agents)]
    
    client = httpx.Client(trust_env=False, timeout=10.0)
    for agent_id in agents:
        if create_agent(client, agent_id):
            print(f"  ✅ Agent {agent_id} created")
        else:
            print(f"  ⚠️  Agent {agent_id} may already exist")
    client.close()
    
    # 并发发送消息
    print(f"\n[3/5] 并发发送消息...")
    print(f"  {num_agents} 个 Agent，每个发送 20 条消息")
    
    results = {}
    threads = []
    start_time = time.time()
    
    for agent_id in agents:
        t = threading.Thread(
            target=send_messages,
            args=(agent_id, 20, 0.05, results)  # 每条消息间隔 50ms
        )
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    # 统计结果
    print(f"\n[4/5] 统计结果...")
    total_success = sum(r["success"] for r in results.values())
    total_fail = sum(r["fail"] for r in results.values())
    
    print(f"  总耗时: {elapsed:.2f}s")
    print(f"  成功: {total_success}")
    print(f"  失败: {total_fail}")
    print(f"  QPS: {total_success / elapsed:.2f}")
    
    for agent_id, result in sorted(results.items()):
        print(f"  {agent_id}: ✅ {result['success']}, ❌ {result['fail']}")
    
    # 等待一段时间让系统处理完成
    print(f"\n[5/5] 等待系统处理完成...")
    print("  等待 30 秒...")
    time.sleep(30)
    
    # 分析数据库状态
    print(f"\n检查数据库状态...")
    db_ok = analyze_database_locks()
    
    # 总结
    print("\n" + "=" * 60)
    if total_fail == 0 and db_ok:
        print("✅ 压测通过！")
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
