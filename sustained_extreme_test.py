#!/usr/bin/env python3
"""
🔥 持续极限压测

配置:
- 5 个 Agent
- 持续 1 分钟
- 每秒 5 条消息
- 总计: 5 × 60 × 5 = 1500 条消息
"""

import httpx
import threading
import time
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict

BASE_URL = "http://127.0.0.1:19999"
DB_PATH = "/Users/wangchaoqun/.novaic/novaic.db"


class SustainedTester:
    def __init__(self):
        self.num_agents = 5
        self.duration_seconds = 60
        self.messages_per_second = 5
        self.total_per_agent = self.duration_seconds * self.messages_per_second  # 300
        self.total_messages = self.num_agents * self.total_per_agent  # 1500
        
        self.results = {}
        self.stats = {
            'sent': 0,
            'success': 0,
            'fail': 0,
            'latencies': [],
        }
        self.stats_lock = threading.Lock()
        
        self.start_time = None
        self.end_time = None
        
    def create_agents(self):
        """创建测试 Agent"""
        print(f"\n[1/4] 创建 {self.num_agents} 个测试 Agent...")
        
        agents = [f"sustained-{i}" for i in range(self.num_agents)]
        
        client = httpx.Client(trust_env=False, timeout=10.0)
        for agent_id in agents:
            try:
                client.post(
                    f"{BASE_URL}/api/agents",
                    json={
                        "id": agent_id,
                        "name": f"Sustained Test {agent_id}",
                        "avatar": "🔥",
                    }
                )
            except:
                pass  # 可能已存在
        client.close()
        
        print(f"  ✅ 完成")
        return agents
    
    def send_messages_sustained(self, agent_id):
        """持续发送消息（每秒 5 条，持续 60 秒）"""
        client = httpx.Client(trust_env=False, timeout=30.0)
        
        try:
            # 设置当前 Agent
            client.post(f"{BASE_URL}/api/agents/current", json={"agent_id": agent_id})
            
            start_time = time.time()
            message_count = 0
            
            for i in range(self.total_per_agent):
                # 计算目标时间（应该在哪个时刻发送）
                target_time = start_time + (i / self.messages_per_second)
                
                # 等待到目标时间
                now = time.time()
                sleep_time = target_time - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # 发送消息
                send_start = time.time()
                try:
                    resp = client.post(
                        f"{BASE_URL}/api/chat/send",
                        json={"content": f"Sustained test {i+1}"},
                        timeout=15.0,
                    )
                    
                    latency = time.time() - send_start
                    
                    with self.stats_lock:
                        self.stats['sent'] += 1
                        if resp.status_code == 200:
                            self.stats['success'] += 1
                        else:
                            self.stats['fail'] += 1
                        self.stats['latencies'].append(latency)
                    
                    message_count += 1
                    
                except Exception as e:
                    with self.stats_lock:
                        self.stats['sent'] += 1
                        self.stats['fail'] += 1
            
            actual_duration = time.time() - start_time
            self.results[agent_id] = {
                "sent": message_count,
                "duration": actual_duration,
                "qps": message_count / actual_duration if actual_duration > 0 else 0,
            }
            
        finally:
            client.close()
    
    def monitor_progress(self, threads):
        """实时监控进度"""
        start = time.time()
        
        while any(t.is_alive() for t in threads):
            elapsed = time.time() - start
            
            with self.stats_lock:
                sent = self.stats['sent']
                success = self.stats['success']
                fail = self.stats['fail']
                current_qps = sent / elapsed if elapsed > 0 else 0
            
            print(f"  进度: {elapsed:.0f}s | 已发送: {sent}/{self.total_messages} | "
                  f"成功: {success} | 失败: {fail} | QPS: {current_qps:.1f}", 
                  end="\r")
            
            time.sleep(0.5)
        
        print()  # 换行
    
    def run_sustained_test(self, agents):
        """执行持续压测"""
        print(f"\n[2/4] 🔥 开始持续极限压测...")
        print(f"  配置:")
        print(f"    - Agent 数: {self.num_agents}")
        print(f"    - 持续时间: {self.duration_seconds}s")
        print(f"    - 每秒消息数: {self.messages_per_second} 条/Agent")
        print(f"    - 总消息数: {self.total_messages} 条")
        print(f"    - 目标 QPS: {self.num_agents * self.messages_per_second} (持续)")
        print()
        
        threads = []
        self.start_time = time.time()
        
        # 启动所有发送线程
        for agent_id in agents:
            t = threading.Thread(target=self.send_messages_sustained, args=(agent_id,))
            threads.append(t)
            t.start()
        
        # 监控进度
        self.monitor_progress(threads)
        
        # 等待所有完成
        for t in threads:
            t.join()
        
        self.end_time = time.time()
    
    def analyze_results(self):
        """分析结果"""
        print(f"\n[3/4] 📊 分析结果...")
        
        elapsed = self.end_time - self.start_time
        
        with self.stats_lock:
            total_sent = self.stats['sent']
            total_success = self.stats['success']
            total_fail = self.stats['fail']
            latencies = sorted(self.stats['latencies'])
        
        # 延迟统计
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            p50 = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)]
            p99 = latencies[int(len(latencies)*0.99)]
            max_latency = max(latencies)
        else:
            avg_latency = p50 = p95 = p99 = max_latency = 0
        
        print(f"\n  发送统计:")
        print(f"    总耗时: {elapsed:.2f}s")
        print(f"    已发送: {total_sent}/{self.total_messages}")
        print(f"    成功: {total_success}")
        print(f"    失败: {total_fail}")
        print(f"    成功率: {total_success/total_sent*100:.2f}%")
        print(f"    实际 QPS: {total_sent/elapsed:.2f}")
        print(f"    目标 QPS: {self.num_agents * self.messages_per_second}")
        
        print(f"\n  延迟统计:")
        print(f"    平均: {avg_latency*1000:.1f}ms")
        print(f"    P50: {p50*1000:.1f}ms")
        print(f"    P95: {p95*1000:.1f}ms")
        print(f"    P99: {p99*1000:.1f}ms")
        print(f"    最大: {max_latency*1000:.1f}ms")
        
        print(f"\n  每个 Agent 的表现:")
        for agent_id, result in sorted(self.results.items()):
            print(f"    {agent_id}: {result['sent']} 条, "
                  f"耗时 {result['duration']:.1f}s, "
                  f"QPS {result['qps']:.1f}")
        
        return total_success, total_fail
    
    def check_system_health(self, wait_seconds=90):
        """检查系统健康"""
        print(f"\n[4/4] 🏥 系统健康检查...")
        print(f"  等待 {wait_seconds} 秒让系统处理...")
        
        for i in range(wait_seconds):
            remaining = wait_seconds - i
            print(f"  剩余 {remaining}s...", end="\r")
            time.sleep(1)
        
        print(f"\n  检查数据库...")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            
            # 卡住的 Task/Saga
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
            
            # 最近创建的 Saga 统计
            cursor = conn.execute("""
                SELECT COUNT(*) as cnt FROM tq_sagas
                WHERE created_at > datetime('now', '-2 minute')
            """)
            recent_sagas = cursor.fetchone()['cnt']
            
            # Task/Saga 状态分布
            cursor = conn.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM tq_tasks
                WHERE created_at > datetime('now', '-2 minute')
                GROUP BY status
            """)
            task_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
            
            cursor = conn.execute("""
                SELECT status, COUNT(*) as cnt 
                FROM tq_sagas
                WHERE created_at > datetime('now', '-2 minute')
                GROUP BY status
            """)
            saga_status = {row['status']: row['cnt'] for row in cursor.fetchall()}
            
            conn.close()
            
            print(f"\n  数据库状态:")
            print(f"    卡住的 Task: {stuck_tasks}")
            print(f"    卡住的 Saga: {stuck_sagas}")
            print(f"    最近 2 分钟的 Saga: {recent_sagas}")
            
            if task_status:
                print(f"\n    Task 状态分布（最近 2 分钟）:")
                for status, cnt in sorted(task_status.items()):
                    print(f"      {status}: {cnt}")
            
            if saga_status:
                print(f"\n    Saga 状态分布（最近 2 分钟）:")
                for status, cnt in sorted(saga_status.items()):
                    print(f"      {status}: {cnt}")
            
            return stuck_tasks == 0 and stuck_sagas == 0
            
        except Exception as e:
            print(f"  ❌ 数据库检查失败: {e}")
            return False
    
    def run(self):
        """执行完整测试"""
        print("=" * 80)
        print("🔥 持续极限压测")
        print("=" * 80)
        
        agents = self.create_agents()
        self.run_sustained_test(agents)
        total_success, total_fail = self.analyze_results()
        system_healthy = self.check_system_health(wait_seconds=90)
        
        # 总结
        print("\n" + "=" * 80)
        if total_fail == 0 and system_healthy:
            print("✅ 持续极限压测通过！")
            print(f"   成功处理 {total_success} 条消息")
            print(f"   持续 QPS: {total_success/(self.end_time - self.start_time):.2f}")
            print(f"   无 Task/Saga 卡住")
            print("=" * 80)
            return 0
        elif total_fail > 0:
            print(f"⚠️  有 {total_fail} 条消息发送失败")
            print(f"   成功率: {total_success/(total_success + total_fail)*100:.1f}%")
            print("=" * 80)
            return 1
        else:
            print("⚠️  有 Task/Saga 卡住")
            print("=" * 80)
            return 1


def main():
    tester = SustainedTester()
    return tester.run()


if __name__ == "__main__":
    sys.exit(main())
