#!/usr/bin/env python3
"""
单Runtime测试

测试场景：
以 0.05s (50ms) 的间隔持续给一个 Agent 发送消息，持续 1 分钟
验证是否只创建了 1 个 Runtime（批处理机制验证）

预期结果：
- 只创建 1 个 Runtime
- 所有消息都被同一个 Agent Loop 处理
- 消息不丢失，全部标记为 read=1
"""

import httpx
import time
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"

# 测试参数
SEND_INTERVAL = 0.05  # 50ms
TEST_DURATION = 60    # 60秒
MESSAGE_PREFIX = "[SingleRT]"


def cleanup():
    """清理测试环境"""
    print("🧹 清理测试环境...")
    conn = sqlite3.connect(str(DB_PATH))
    
    # 清理消息
    conn.execute("DELETE FROM chat_messages")
    
    # 清理 Task/Saga
    conn.execute("DELETE FROM tq_tasks")
    conn.execute("DELETE FROM tq_sagas")
    
    # 清理 Runtimes
    conn.execute("DELETE FROM agent_runtimes")
    
    # 重置 SubAgent 为 sleeping
    conn.execute("UPDATE subagents SET status = 'sleeping', updated_at = datetime('now')")
    
    conn.commit()
    conn.close()
    print("✅ 清理完成\n")


def create_test_agent():
    """创建或获取测试 Agent"""
    print("📝 准备测试 Agent...")
    
    with httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False) as client:
        # 尝试创建新 Agent
        try:
            r = client.post("/api/agents", json={
                "name": "SingleRuntimeTestAgent",
                "model": "kimi-k2.5"
            })
            
            if r.status_code == 200:
                agent_data = r.json()
                agent_id = agent_data['id']
                print(f"✅ 创建新 Agent: {agent_id[:12]}")
                return agent_id
            else:
                # 如果创建失败，尝试获取现有 Agent
                r = client.get("/api/agents")
                agents = r.json().get("agents", [])
                if agents:
                    agent_id = agents[0]["id"]
                    print(f"✅ 使用现有 Agent: {agent_id[:12]}")
                    return agent_id
                else:
                    raise Exception("无法创建或获取 Agent")
        except Exception as e:
            print(f"❌ 错误: {e}")
            raise


def set_current_agent(agent_id):
    """设置当前 Agent"""
    with httpx.Client(base_url=GATEWAY_URL, timeout=10.0, trust_env=False) as client:
        r = client.post("/api/agents/current", json={"agent_id": agent_id})
        if r.status_code != 200:
            raise Exception(f"设置当前 Agent 失败: {r.status_code}")


def send_messages(agent_id):
    """以固定间隔发送消息"""
    print(f"\n🚀 开始发送消息...")
    print(f"   - 间隔: {SEND_INTERVAL*1000:.0f}ms")
    print(f"   - 持续时间: {TEST_DURATION}s")
    print(f"   - 预计消息数: {int(TEST_DURATION / SEND_INTERVAL)} 条\n")
    
    start_time = time.time()
    message_count = 0
    failed_count = 0
    
    with httpx.Client(base_url=GATEWAY_URL, timeout=10.0, trust_env=False) as client:
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= TEST_DURATION:
                break
            
            try:
                message = f"{MESSAGE_PREFIX} 消息#{message_count + 1} (t={elapsed:.2f}s)"
                r = client.post("/api/chat/send", json={"message": message})
                
                if r.status_code == 200:
                    message_count += 1
                    if message_count % 100 == 0:
                        print(f"  ✓ 已发送 {message_count} 条消息 (用时 {elapsed:.1f}s)")
                else:
                    failed_count += 1
                    print(f"  ✗ 消息 #{message_count + 1} 发送失败: {r.status_code}")
            
            except Exception as e:
                failed_count += 1
                print(f"  ✗ 消息 #{message_count + 1} 发送异常: {e}")
            
            time.sleep(SEND_INTERVAL)
    
    actual_duration = time.time() - start_time
    
    print(f"\n✅ 消息发送完成")
    print(f"   - 成功发送: {message_count} 条")
    print(f"   - 发送失败: {failed_count} 条")
    print(f"   - 实际用时: {actual_duration:.2f}s")
    print(f"   - 平均速率: {message_count / actual_duration:.2f} msg/s\n")
    
    return message_count


def wait_for_processing(timeout=120):
    """等待消息处理完成"""
    print(f"⏳ 等待处理完成 (最多 {timeout}s)...\n")
    
    start_wait = time.time()
    last_report = start_wait
    
    while True:
        elapsed = time.time() - start_wait
        
        if elapsed > timeout:
            print(f"\n⚠️  超时！等待了 {timeout}s")
            break
        
        # 检查系统状态
        conn = sqlite3.connect(str(DB_PATH))
        
        # Pending/Running 的 Task 和 Saga
        cursor = conn.execute("SELECT COUNT(*) FROM tq_tasks WHERE status IN ('pending', 'claimed')")
        pending_tasks = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM tq_sagas WHERE status IN ('pending', 'running')")
        pending_sagas = cursor.fetchone()[0]
        
        # 未读消息
        cursor = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE type='USER_MESSAGE' AND read=0")
        unread_messages = cursor.fetchone()[0]
        
        conn.close()
        
        # 每 5 秒报告一次
        if time.time() - last_report > 5:
            print(f"[{elapsed:.0f}s] tasks={pending_tasks}, sagas={pending_sagas}, unread={unread_messages}")
            last_report = time.time()
        
        # 检查是否完成
        if pending_tasks == 0 and pending_sagas == 0 and unread_messages == 0:
            print(f"\n✅ 处理完成！耗时 {elapsed:.1f}s\n")
            break
        
        time.sleep(1)


def analyze_results(agent_id, expected_messages):
    """分析测试结果"""
    print("="*70)
    print("📊 测试结果分析")
    print("="*70)
    
    conn = sqlite3.connect(str(DB_PATH))
    
    # 1. 统计消息
    print("\n📨 消息统计:")
    
    cursor = conn.execute("""
        SELECT 
            status,
            read,
            COUNT(*) as count
        FROM chat_messages
        WHERE type = 'USER_MESSAGE' AND agent_id = ?
        GROUP BY status, read
    """, (agent_id,))
    
    total_messages = 0
    for row in cursor:
        status, read, count = row
        read_str = "已读" if read == 1 else "未读"
        print(f"   - status={status}, read={read_str}: {count} 条")
        total_messages += count
    
    print(f"   - 总计: {total_messages} 条")
    print(f"   - 预期: {expected_messages} 条")
    
    if total_messages == expected_messages:
        print(f"   ✅ 消息数量匹配")
    else:
        print(f"   ⚠️  消息数量不匹配 (差异: {abs(total_messages - expected_messages)} 条)")
    
    # 2. 统计 Runtime
    print("\n🏃 Runtime 统计:")
    
    cursor = conn.execute("""
        SELECT 
            runtime_id,
            status,
            json_array_length(context) as context_length,
            created_at,
            updated_at
        FROM agent_runtimes
        WHERE agent_id = ?
        ORDER BY created_at
    """, (agent_id,))
    
    runtimes = cursor.fetchall()
    print(f"   - 创建的 Runtime 数量: {len(runtimes)}")
    
    for i, row in enumerate(runtimes, 1):
        runtime_id, status, context_length, created_at, updated_at = row
        print(f"   - Runtime #{i}:")
        print(f"     ID: {runtime_id}")
        print(f"     状态: {status}")
        print(f"     Context 长度: {context_length}")
        print(f"     创建时间: {created_at}")
        print(f"     更新时间: {updated_at}")
    
    # 3. 验证核心假设
    print("\n✅ 核心验证:")
    
    if len(runtimes) == 1:
        print(f"   ✅ 只创建了 1 个 Runtime（符合预期）")
    else:
        print(f"   ❌ 创建了 {len(runtimes)} 个 Runtime（不符合预期！）")
    
    if len(runtimes) > 0:
        runtime_id = runtimes[0][0]
        context_length = runtimes[0][2]
        
        # 统计 context 中的 user 消息数
        cursor = conn.execute("""
            SELECT context FROM agent_runtimes WHERE runtime_id = ?
        """, (runtime_id,))
        row = cursor.fetchone()
        
        if row:
            import json
            context = json.loads(row[0])
            user_msgs = [m for m in context if m.get('role') == 'user']
            
            print(f"   - Runtime Context 中的用户消息数: {len(user_msgs)}")
            print(f"   - 数据库中的总消息数: {total_messages}")
            
            if len(user_msgs) == total_messages:
                print(f"   ✅ 所有消息都进入了 Context")
            else:
                print(f"   ⚠️  有 {total_messages - len(user_msgs)} 条消息未进入 Context")
    
    # 4. SubAgent 状态
    print("\n🤖 SubAgent 状态:")
    
    cursor = conn.execute("""
        SELECT subagent_id, status, updated_at
        FROM subagents
        WHERE agent_id = ?
        ORDER BY created_at
    """, (agent_id,))
    
    for row in cursor:
        subagent_id, status, updated_at = row
        print(f"   - SubAgent: {subagent_id}")
        print(f"     状态: {status}")
        print(f"     更新时间: {updated_at}")
    
    # 5. AI 回复
    print("\n💬 AI 回复:")
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM chat_messages
        WHERE type = 'AGENT_REPLY' AND agent_id = ?
    """, (agent_id,))
    ai_replies = cursor.fetchone()[0]
    
    print(f"   - AI 回复数: {ai_replies} 条")
    
    if ai_replies > 0:
        cursor = conn.execute("""
            SELECT content FROM chat_messages
            WHERE type = 'AGENT_REPLY' AND agent_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (agent_id,))
        latest_reply = cursor.fetchone()[0]
        
        print(f"   - 最新回复预览: {latest_reply[:100]}...")
    
    # 6. Saga 统计
    print("\n📊 Saga 统计:")
    
    cursor = conn.execute("""
        SELECT saga_type, status, COUNT(*) as count
        FROM tq_sagas
        GROUP BY saga_type, status
        ORDER BY saga_type, status
    """)
    
    for row in cursor:
        saga_type, status, count = row
        print(f"   - {saga_type} ({status}): {count}")
    
    conn.close()
    
    # 最终判断
    print("\n" + "="*70)
    if len(runtimes) == 1 and total_messages == expected_messages:
        print("🎉 测试通过！")
        print("   ✓ 只创建了 1 个 Runtime")
        print("   ✓ 所有消息都被处理")
        print("   ✓ 批处理机制正常工作")
    else:
        print("⚠️  测试存在问题，需要进一步检查")
    print("="*70)


def main():
    """主函数"""
    print("="*70)
    print("🔬 单 Runtime 测试 (批处理验证)")
    print("="*70)
    print(f"测试参数: 间隔={SEND_INTERVAL*1000:.0f}ms, 持续={TEST_DURATION}s")
    print("="*70 + "\n")
    
    # 1. 清理环境
    cleanup()
    
    # 2. 创建/获取 Agent
    agent_id = create_test_agent()
    
    # 3. 设置当前 Agent
    set_current_agent(agent_id)
    
    # 4. 发送消息
    message_count = send_messages(agent_id)
    
    # 5. 等待处理
    wait_for_processing(timeout=120)
    
    # 6. 分析结果
    analyze_results(agent_id, message_count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
