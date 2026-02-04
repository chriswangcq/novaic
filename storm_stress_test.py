#!/usr/bin/env python3
"""
🌪️ 暴风压测 - 极限负载测试

测试配置:
- 20 个 Agent
- 每个 Agent 100 条消息
- 总共 2000 条消息
- 爆发式发送
"""

import httpx
import threading
import time
import sys
import sqlite3
from collections import defaultdict
from datetime import datetime

BASE_URL = "http://127.0.0.1:19999"
DB_PATH = "/Users/wangchaoqun/.novaic/novaic.db"


class StormTester:
    def __init__(self, num_agents=20, messages_per_agent=100):
        self.num_agents = num_agents
        self.messages_per_agent = messages_per_agent
        self.total_messages = num_agents * messages_per_agent
        self.results = {}
        self.errors = defaultdict(list)
        self.start_time = None
        self.end_time = None
        
    def create_agents(self):
        """批量创建 Agent"""
        print(f"\n[1/4] 创建 {self.num_agents} 个测试 Agent...")
        
        agents = [f"storm-{i}" for i in range(self.num_agents)]
        
        # 并发创建
        def create_agent(agent_id):
            try:
                client = httpx.Client(trust_env=False, timeout=10.0)
                client.post(
                    f"{BASE_URL}/api/agents",
                    json={
                        "id": agent_id,
                        "name": f"Storm Agent {agent_id}",
                        "avatar": "🌪️",
                    }
                )
                client.close()
            except:
                pass  # 可能已存在
        
        threads = []
        for agent_id in agents:
            t = threading.Thread(target=create_agent, args=(agent_id,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f"  ✅ 完成")
        return agents
    
    def send_messages_burst(self, agent_id):
        """爆发式发送消息"""
        client = httpx.Client(trust_env=False, timeout=30.0)
        
        success = 0
        fail = 0
        latencies = []
        
        try:
            # 设置当前 Agent
            client.post(f"{BASE_URL}/api/agents/current", json={"agent_id": agent_id})
            
            for i in range(self.messages_per_agent):
                start = time.time()
                try:
                    resp = client.post(
                        f"{BASE_URL}/api/chat/send",
                        json={"content": f"Storm test message {i+1}"},
                        timeout=15.0,
                    )
                    
                    elapsed = time.time() - start
                    latencies.append(elapsed)
                    
                    if resp.status_code == 200:
                        success += 1
                    else:
                        fail += 1
                        if len(self.errors[agent_id]) < 3:
                            self.errors[agent_id].append(f"HTTP {resp.status_code}")
                
                except Exception as e:
                    fail += 1
                    if len(self.errors[agent_id]) < 3:
                        self.errors[agent_id].append(str(e)[:100])
            
            self.results[agent_id] = {
                "success": success,
                "fail": fail,
                "latencies": latencies,
                "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
                "max_latency": max(latencies) if latencies else 0,
            }
            
        finally:
            client.close()
    
    def run_storm(self, agents):
        """发起暴风攻击"""
        print(f"\n[2/4] 🌪️  发起暴风攻击...")
        print(f"  配置: {self.num_agents} Agent × {self.messages_per_agent} 消息 = {self.total_messages} 消息")
        print(f"  模式: 爆发式（无延迟，最大并发）")
        
        threads = []
        self.start_time = time.time()
        
        # 启动所有线程
        for agent_id in agents:
            t = threading.Thread(target=self.send_messages_burst, args=(agent_id,))
            threads.append(t)
            t.start()
        
        # 实时显示进度
        completed = 0
        while completed < len(threads):
            completed = sum(1 for t in threads if not t.is_alive())
            elapsed = time.time() - self.start_time
            print(f"  进度: {completed}/{len(threads)} Agent 完成, 耗时: {elapsed:.1f}s", end="\r")
            time.sleep(0.5)
        
        # 等待所有完成
        for t in threads:
            t.join()
        
        self.end_time = time.time()
        print()  # 换行
    
    def analyze_results(self):
        """分析压测结果"""
        print(f"\n[3/4] 📊 分析压测结果...")
        
        elapsed = self.end_time - self.start_time
        total_success = sum(r["success"] for r in self.results.values())
        total_fail = sum(r["fail"] for r in self.results.values())
        
        # 延迟统计
        all_latencies = []
        for r in self.results.values():
            all_latencies.extend(r["latencies"])
        
        all_latencies.sort()
        p50 = all_latencies[len(all_latencies)//2] if all_latencies else 0
        p95 = all_latencies[int(len(all_latencies)*0.95)] if all_latencies else 0
        p99 = all_latencies[int(len(all_latencies)*0.99)] if all_latencies else 0
        
        print(f"\n  发送阶段:")
        print(f"    总耗时: {elapsed:.2f}s")
        print(f"    成功: {total_success}/{self.total_messages}")
        print(f"    失败: {total_fail}/{self.total_messages}")
        print(f"    成功率: {total_success/self.total_messages*100:.1f}%")
        print(f"    QPS: {total_success/elapsed:.2f}")
        
        print(f"\n  延迟统计:")
        print(f"    平均: {sum(all_latencies)/len(all_latencies)*1000:.1f}ms")
        print(f"    P50: {p50*1000:.1f}ms")
        print(f"    P95: {p95*1000:.1f}ms")
        print(f"    P99: {p99*1000:.1f}ms")
        print(f"    最大: {max(all_latencies)*1000:.1f}ms")
        
        # 每个 Agent 的表现
        if total_fail > 0:
            print(f"\n  失败详情:")
            for agent_id, result in sorted(self.results.items()):
                if result["fail"] > 0:
                    print(f"    {agent_id}: {result['fail']} 次失败")
                    if agent_id in self.errors and self.errors[agent_id]:
                        for err in self.errors[agent_id][:3]:
                            print(f"      - {err}")
        
        return total_success, total_fail
    
    def check_system_health(self, wait_seconds=90):
        """检查系统健康状况"""
        print(f"\n[4/4] 🏥 系统健康检查...")
        print(f"  等待 {wait_seconds} 秒让系统完全处理...")
        
        # 分段等待，显示进度
        for i in range(wait_seconds):
            remaining = wait_seconds - i
            print(f"  剩余 {remaining}s...", end="\r")
            time.sleep(1)
        
        print(f"\n  检查数据库...")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            
            # 卡住的 Task
            cursor = conn.execute("""
                SELECT COUNT(*) as cnt FROM tq_tasks 
                WHERE status IN ('claimed', 'running') 
                AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
            """)
            stuck_tasks = cursor.fetchone()['cnt']
            
            # 卡住的 Saga
            cursor = conn.execute("""
                SELECT COUNT(*) as cnt FROM tq_sagas 
                WHERE status IN ('claimed', 'running') 
                AND datetime(heartbeat_at, '+60 seconds') < datetime('now')
            """)
            stuck_sagas = cursor.fetchone()['cnt']
            
            # Task/Saga 总数
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_tasks")
            total_tasks = cursor.fetchone()['cnt']
            
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM tq_sagas")
            total_sagas = cursor.fetchone()['cnt']
            
            # Task 状态分布
            cursor = conn.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM tq_tasks 
                GROUP BY status
            """)
            task_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
            
            # Saga 状态分布
            cursor = conn.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM tq_sagas 
                GROUP BY status
            """)
            saga_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
            
            # 消息状态
            cursor = conn.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM chat_messages 
                GROUP BY status
            """)
            message_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
            
            conn.close()
            
            print(f"\n  数据库状态:")
            print(f"    Task 总数: {total_tasks}")
            print(f"    Saga 总数: {total_sagas}")
            print(f"    卡住的 Task: {stuck_tasks}")
            print(f"    卡住的 Saga: {stuck_sagas}")
            
            print(f"\n    Task 状态分布:")
            for status, cnt in sorted(task_status.items()):
                print(f"      {status}: {cnt}")
            
            print(f"\n    Saga 状态分布:")
            for status, cnt in sorted(saga_status.items()):
                print(f"      {status}: {cnt}")
            
            print(f"\n    消息状态分布:")
            for status, cnt in sorted(message_status.items()):
                print(f"      {status}: {cnt}")
            
            return stuck_tasks == 0 and stuck_sagas == 0
            
        except Exception as e:
            print(f"  ❌ 数据库检查失败: {e}")
            return False
    
    def run(self):
        """执行完整的暴风压测"""
        print("=" * 70)
        print("🌪️  暴风压测 - 极限负载测试")
        print("=" * 70)
        
        agents = self.create_agents()
        self.run_storm(agents)
        total_success, total_fail = self.analyze_results()
        system_healthy = self.check_system_health(wait_seconds=90)
        
        # 总结
        print("\n" + "=" * 70)
        if total_fail == 0 and system_healthy:
            print("✅ 暴风压测通过！")
            print(f"   成功处理 {total_success} 条消息")
            print(f"   QPS: {total_success/(self.end_time - self.start_time):.2f}")
            print(f"   无 Task/Saga 卡住")
            print("=" * 70)
            return 0
        elif total_fail > 0:
            print(f"⚠️  有 {total_fail} 条消息发送失败")
            print(f"   成功率: {total_success/self.total_messages*100:.1f}%")
            print("=" * 70)
            return 1
        else:
            print("⚠️  有 Task/Saga 卡住")
            print("=" * 70)
            return 1


def main():
    # 暴风级别配置
    tester = StormTester(
        num_agents=20,
        messages_per_agent=100
    )
    
    return tester.run()


if __name__ == "__main__":
    sys.exit(main())
