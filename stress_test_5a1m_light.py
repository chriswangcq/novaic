#!/usr/bin/env python3
"""
🧪 5 Agent × 1 分钟轻量压测
- 5 个 Agent
- 每秒 1 条消息/Agent
- 持续 60 秒
- 总计: 300 条消息
- 目标 QPS: 5
"""

import httpx
import threading
import time
import sys
import sqlite3
from datetime import datetime

BASE_URL = "http://127.0.0.1:19999"


def get_db_path():
    """从 Gateway 获取数据库路径"""
    try:
        resp = httpx.get(f"{BASE_URL}/internal/data-dir", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()["db_path"]
    except:
        pass
    return "/Users/wangchaoqun/.novaic/novaic.db"


class LightStressTester:
    def __init__(self):
        self.num_agents = 5
        self.duration_seconds = 60
        self.messages_per_second = 1  # 降低到每秒 1 条
        self.total_per_agent = self.duration_seconds * self.messages_per_second
        self.total_messages = self.num_agents * self.total_per_agent
        
        self.agent_ids = []
        self.stats = {
            'sent': 0,
            'success': 0,
            'fail': 0,
            'latencies': [],
        }
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None
    
    def setup_agents(self):
        """创建并配置测试 agents"""
        print(f"\n[1/4] 创建 {self.num_agents} 个测试 Agent...")
        
        client = httpx.Client(timeout=10.0, trust_env=False)
        
        for i in range(self.num_agents):
            try:
                resp = client.post(
                    f"{BASE_URL}/api/agents",
                    json={
                        "name": f"LightTest-{i}",
                        "model": "kimi-k2.5"
                    }
                )
                if resp.status_code == 200:
                    agent_id = resp.json()["id"]
                    self.agent_ids.append(agent_id)
                    print(f"  ✅ Agent {i}: {agent_id}")
                else:
                    print(f"  ❌ Agent {i} 创建失败: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  ❌ Agent {i} 创建失败: {e}")
        
        client.close()
        
        if len(self.agent_ids) != self.num_agents:
            print(f"  ⚠️  只创建了 {len(self.agent_ids)}/{self.num_agents} 个 Agent")
            return False
        
        print(f"  ✅ 完成")
        return True
    
    def send_messages_for_agent(self, agent_id, agent_idx):
        """为一个 agent 持续发送消息"""
        client = httpx.Client(timeout=30.0, trust_env=False)
        
        try:
            # 选择 agent
            client.post(f"{BASE_URL}/api/agents/current", json={"agent_id": agent_id})
            
            start = time.time()
            
            for i in range(self.total_per_agent):
                # 计算目标发送时间（每秒 1 条）
                target_time = start + i  # 简单：每条消息间隔 1 秒
                
                # 等待到目标时间
                sleep_time = target_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # 发送消息
                send_start = time.time()
                try:
                    resp = client.post(
                        f"{BASE_URL}/api/chat/send",
                        json={"message": f"轻量测试 Agent{agent_idx}-{i+1}"},
                        timeout=15.0
                    )
                    latency = time.time() - send_start
                    
                    with self.lock:
                        self.stats['sent'] += 1
                        if resp.status_code == 200:
                            self.stats['success'] += 1
                        else:
                            self.stats['fail'] += 1
                        self.stats['latencies'].append(latency)
                
                except Exception as e:
                    with self.lock:
                        self.stats['sent'] += 1
                        self.stats['fail'] += 1
        
        finally:
            client.close()
    
    def monitor_progress(self, threads):
        """监控进度"""
        start = time.time()
        
        while any(t.is_alive() for t in threads):
            elapsed = time.time() - start
            
            with self.lock:
                sent = self.stats['sent']
                success = self.stats['success']
                fail = self.stats['fail']
                qps = sent / elapsed if elapsed > 0 else 0
            
            progress = (sent / self.total_messages * 100) if self.total_messages > 0 else 0
            
            print(f"  [{elapsed:.0f}s] 进度: {progress:.1f}% | "
                  f"发送: {sent}/{self.total_messages} | "
                  f"成功: {success} | 失败: {fail} | "
                  f"QPS: {qps:.1f}  ",
                  end="\r")
            
            time.sleep(1)
        
        print()
    
    def run_test(self):
        """执行压测"""
        print(f"\n[2/4] 🧪 开始轻量压测...")
        print(f"  配置:")
        print(f"    - Agent 数: {self.num_agents}")
        print(f"    - 持续时间: {self.duration_seconds}s")
        print(f"    - 消息数/Agent: {self.messages_per_second}/s")
        print(f"    - 总消息数: {self.total_messages}")
        print(f"    - 目标 QPS: {self.num_agents * self.messages_per_second}")
        print()
        
        threads = []
        self.start_time = time.time()
        
        for idx, agent_id in enumerate(self.agent_ids):
            t = threading.Thread(
                target=self.send_messages_for_agent,
                args=(agent_id, idx)
            )
            threads.append(t)
            t.start()
        
        # 监控
        self.monitor_progress(threads)
        
        # 等待完成
        for t in threads:
            t.join()
        
        self.end_time = time.time()
    
    def analyze_results(self):
        """分析结果"""
        print(f"\n[3/4] 📊 分析结果...")
        
        elapsed = self.end_time - self.start_time
        
        with self.lock:
            sent = self.stats['sent']
            success = self.stats['success']
            fail = self.stats['fail']
            latencies = sorted(self.stats['latencies'])
        
        # 延迟统计
        if latencies:
            avg = sum(latencies) / len(latencies)
            p50 = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)]
            p99 = latencies[int(len(latencies)*0.99)]
            pmax = max(latencies)
        else:
            avg = p50 = p95 = p99 = pmax = 0
        
        print(f"\n  发送统计:")
        print(f"    总耗时: {elapsed:.2f}s")
        print(f"    已发送: {sent}/{self.total_messages}")
        print(f"    成功: {success} ({success/sent*100:.1f}%)")
        print(f"    失败: {fail}")
        print(f"    实际 QPS: {sent/elapsed:.2f}")
        
        print(f"\n  延迟统计:")
        print(f"    平均: {avg*1000:.1f}ms")
        print(f"    P50: {p50*1000:.1f}ms")
        print(f"    P95: {p95*1000:.1f}ms")
        print(f"    P99: {p99*1000:.1f}ms")
        print(f"    最大: {pmax*1000:.1f}ms")
        
        return success, fail
    
    def check_health(self, wait_seconds=120):
        """检查系统健康"""
        print(f"\n[4/4] 🏥 等待 {wait_seconds}s 后检查系统健康...")
        
        for i in range(wait_seconds):
            print(f"  剩余: {wait_seconds - i}s  ", end="\r")
            time.sleep(1)
        print()
        
        db_path = get_db_path()
        print(f"  数据库: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            
            # 消息统计
            cur = conn.execute(
                "SELECT type, status, COUNT(*) as cnt FROM chat_messages "
                "WHERE timestamp > datetime('now', '-10 minute') "
                "GROUP BY type, status"
            )
            print(f"\n  消息统计（最近 10 分钟）:")
            msg_stats = {}
            for row in cur.fetchall():
                print(f"    {row[0]}/{row[1]}: {row[2]}")
                msg_stats[f"{row[0]}/{row[1]}"] = row[2]
            
            # Saga 统计
            cur = conn.execute(
                "SELECT saga_type, status, COUNT(*) as cnt FROM tq_sagas "
                "WHERE created_at > datetime('now', '-10 minute') "
                "GROUP BY saga_type, status"
            )
            print(f"\n  Saga 统计（最近 10 分钟）:")
            saga_stats = {}
            for row in cur.fetchall():
                print(f"    {row[0]}/{row[1]}: {row[2]}")
                saga_stats[f"{row[0]}/{row[1]}"] = row[2]
            
            # Runtime 统计
            cur = conn.execute(
                "SELECT status, phase, COUNT(*) as cnt FROM agent_runtimes "
                "WHERE created_at > datetime('now', '-10 minute') "
                "GROUP BY status, phase"
            )
            print(f"\n  Runtime 统计（最近 10 分钟）:")
            for row in cur.fetchall():
                print(f"    {row[0]}/{row[1]}: {row[2]}")
            
            # AI 回复数量
            cur = conn.execute(
                "SELECT COUNT(*) FROM chat_messages "
                "WHERE type = 'AGENT_REPLY' "
                "AND timestamp > datetime('now', '-10 minute')"
            )
            ai_replies = cur.fetchone()[0]
            print(f"\n  AI 回复数: {ai_replies}")
            
            # 卡住的 task/saga
            cur = conn.execute(
                "SELECT COUNT(*) FROM tq_tasks "
                "WHERE status IN ('claimed', 'running') "
                "AND datetime(heartbeat_at, '+60 seconds') < datetime('now')"
            )
            stuck_tasks = cur.fetchone()[0]
            
            cur = conn.execute(
                "SELECT COUNT(*) FROM tq_sagas "
                "WHERE status IN ('claimed', 'running') "
                "AND datetime(heartbeat_at, '+60 seconds') < datetime('now')"
            )
            stuck_sagas = cur.fetchone()[0]
            
            # 失败的 saga
            cur = conn.execute(
                "SELECT COUNT(*) FROM tq_sagas WHERE status = 'failed'"
            )
            failed_sagas = cur.fetchone()[0]
            
            print(f"\n  健康检查:")
            print(f"    卡住的 Task: {stuck_tasks}")
            print(f"    卡住的 Saga: {stuck_sagas}")
            print(f"    失败的 Saga: {failed_sagas}")
            
            conn.close()
            
            # 评估：至少要有一些 AI 回复
            has_ai_replies = ai_replies > 0
            no_stuck = stuck_tasks == 0 and stuck_sagas == 0
            few_failures = failed_sagas < 5
            
            return has_ai_replies and no_stuck and few_failures
        
        except Exception as e:
            print(f"  ❌ 数据库检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """运行完整测试"""
        print("=" * 80)
        print("🧪 5 Agent × 1 分钟轻量压测")
        print("=" * 80)
        
        if not self.setup_agents():
            print("\n❌ Agent 创建失败")
            return 1
        
        self.run_test()
        success, fail = self.analyze_results()
        healthy = self.check_health(wait_seconds=120)
        
        # 总结
        print("\n" + "=" * 80)
        if fail == 0 and healthy:
            print("✅ 轻量压测通过！")
            print(f"   成功: {success} 条消息")
            print(f"   QPS: {success/(self.end_time - self.start_time):.2f}")
            print(f"   系统健康")
        elif fail > 0:
            print(f"⚠️  有 {fail} 条消息失败")
            print(f"   成功率: {success/(success + fail)*100:.1f}%")
        else:
            print("⚠️  系统不健康（有卡住或失败的 Task/Saga）")
        print("=" * 80)
        
        return 0 if (fail == 0 and healthy) else 1


def main():
    tester = LightStressTester()
    return tester.run()


if __name__ == "__main__":
    sys.exit(main())
