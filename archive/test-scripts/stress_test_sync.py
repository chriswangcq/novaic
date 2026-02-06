#!/usr/bin/env python3
"""
同步架构大规模压力测试
- 多Agent并发
- 持续消息发送
- 系统性能监控
"""
import time
import threading
import httpx
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

GATEWAY = "http://127.0.0.1:19999"
DB_PATH = Path.home() / ".novaic" / "novaic.db"

class StressTestStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.messages_sent = 0
        self.messages_failed = 0
        self.agents_created = 0
        self.start_time = None
        self.errors = defaultdict(int)
    
    def record_message(self, success=True, error=None):
        with self.lock:
            if success:
                self.messages_sent += 1
            else:
                self.messages_failed += 1
                if error:
                    self.errors[str(error)[:50]] += 1
    
    def record_agent(self):
        with self.lock:
            self.agents_created += 1
    
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            return {
                "elapsed": elapsed,
                "messages_sent": self.messages_sent,
                "messages_failed": self.messages_failed,
                "agents_created": self.agents_created,
                "msg_per_sec": self.messages_sent / elapsed if elapsed > 0 else 0,
                "errors": dict(self.errors)
            }

stats = StressTestStats()

def create_agent(name: str) -> str:
    """创建单个agent"""
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        try:
            resp = client.post(f"{GATEWAY}/api/agents", json={
                "name": name,
                "model": "kimi-k2.5"
            })
            if resp.status_code == 200:
                agent_id = resp.json()["id"]
                stats.record_agent()
                return agent_id
            else:
                print(f"✗ Create agent failed: {resp.status_code}")
                return None
        except Exception as e:
            print(f"✗ Create agent error: {e}")
            return None

def send_message_worker(agent_id: str, worker_id: int, num_messages: int, interval: float):
    """消息发送工作线程"""
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        # 选择agent
        try:
            client.post(f"{GATEWAY}/api/agents/current", json={"agent_id": agent_id})
        except Exception as e:
            print(f"✗ Worker {worker_id}: Select agent failed: {e}")
            return
        
        for i in range(num_messages):
            try:
                resp = client.post(f"{GATEWAY}/api/chat/send", json={
                    "message": f"W{worker_id} M{i+1}: Test message"
                })
                
                if resp.status_code == 200 and resp.json().get("success"):
                    stats.record_message(success=True)
                else:
                    error = resp.json().get("error", f"HTTP {resp.status_code}")
                    stats.record_message(success=False, error=error)
                    if i % 10 == 0:  # 只打印部分错误
                        print(f"✗ W{worker_id}: {error}")
            except Exception as e:
                stats.record_message(success=False, error=str(e))
                if i % 10 == 0:
                    print(f"✗ W{worker_id}: {e}")
            
            if interval > 0:
                time.sleep(interval)

def check_db_stats():
    """检查数据库状态"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Messages
        sending = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE status='sending'").fetchone()[0]
        sent = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE status='sent'").fetchone()[0]
        
        # Tasks
        tasks_total = conn.execute("SELECT COUNT(*) FROM tq_tasks").fetchone()[0]
        tasks_done = conn.execute("SELECT COUNT(*) FROM tq_tasks WHERE status='done'").fetchone()[0]
        tasks_failed = conn.execute("SELECT COUNT(*) FROM tq_tasks WHERE status='failed'").fetchone()[0]
        
        # Sagas
        sagas_total = conn.execute("SELECT COUNT(*) FROM tq_sagas").fetchone()[0]
        sagas_completed = conn.execute("SELECT COUNT(*) FROM tq_sagas WHERE status='completed'").fetchone()[0]
        sagas_failed = conn.execute("SELECT COUNT(*) FROM tq_sagas WHERE status='failed'").fetchone()[0]
        sagas_running = conn.execute("SELECT COUNT(*) FROM tq_sagas WHERE status='running'").fetchone()[0]
        
        # Runtimes
        runtimes = conn.execute("SELECT COUNT(*) FROM agent_runtimes").fetchone()[0]
        
        conn.close()
        
        return {
            "messages": {"sending": sending, "sent": sent},
            "tasks": {"total": tasks_total, "done": tasks_done, "failed": tasks_failed},
            "sagas": {"total": sagas_total, "completed": sagas_completed, "failed": sagas_failed, "running": sagas_running},
            "runtimes": runtimes
        }
    except Exception as e:
        return {"error": str(e)}

def print_stats():
    """打印统计信息"""
    s = stats.get_stats()
    db = check_db_stats()
    
    print("\n" + "=" * 80)
    print(f"⏱️  运行时间: {s['elapsed']:.1f}s")
    print(f"📨 消息: {s['messages_sent']} 成功, {s['messages_failed']} 失败 ({s['msg_per_sec']:.1f} msg/s)")
    print(f"👥 Agents: {s['agents_created']}")
    
    if "error" not in db:
        print(f"\n📊 数据库:")
        print(f"  Messages: {db['messages']['sent']} sent, {db['messages']['sending']} sending")
        print(f"  Tasks: {db['tasks']['done']}/{db['tasks']['total']} done, {db['tasks']['failed']} failed")
        print(f"  Sagas: {db['sagas']['completed']}/{db['sagas']['total']} completed, {db['sagas']['running']} running, {db['sagas']['failed']} failed")
        print(f"  Runtimes: {db['runtimes']}")
    
    if s['errors']:
        print(f"\n❌ 错误 (top 5):")
        sorted_errors = sorted(s['errors'].items(), key=lambda x: x[1], reverse=True)[:5]
        for err, count in sorted_errors:
            print(f"  [{count}x] {err}")
    
    print("=" * 80)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="同步架构压力测试")
    parser.add_argument("--agents", type=int, default=3, help="Agent数量")
    parser.add_argument("--workers", type=int, default=5, help="每个Agent的并发worker数")
    parser.add_argument("--messages", type=int, default=50, help="每个worker发送的消息数")
    parser.add_argument("--interval", type=float, default=0.1, help="消息间隔(秒)")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 全同步架构大规模压力测试")
    print("=" * 80)
    print(f"配置:")
    print(f"  Agents: {args.agents}")
    print(f"  Workers per agent: {args.workers}")
    print(f"  Messages per worker: {args.messages}")
    print(f"  Message interval: {args.interval}s")
    print(f"  Total messages: {args.agents * args.workers * args.messages}")
    print("=" * 80)
    
    stats.start_time = time.time()
    
    # 1. 创建agents
    print("\n1️⃣  创建Agents...")
    agent_ids = []
    for i in range(args.agents):
        aid = create_agent(f"Stress-{i+1}")
        if aid:
            agent_ids.append(aid)
            print(f"   ✓ Agent {i+1}: {aid[:12]}")
        else:
            print(f"   ✗ Agent {i+1} failed")
    
    if not agent_ids:
        print("❌ 没有可用的agents，退出")
        return
    
    print(f"\n✓ 成功创建 {len(agent_ids)} 个agents")
    
    # 2. 启动并发消息发送
    print(f"\n2️⃣  启动 {len(agent_ids) * args.workers} 个并发workers...")
    threads = []
    
    for i, agent_id in enumerate(agent_ids):
        for w in range(args.workers):
            worker_id = i * args.workers + w + 1
            t = threading.Thread(
                target=send_message_worker,
                args=(agent_id, worker_id, args.messages, args.interval),
                daemon=True
            )
            t.start()
            threads.append(t)
    
    print(f"✓ {len(threads)} workers已启动")
    
    # 3. 监控进度
    print(f"\n3️⃣  监控中...")
    last_print = time.time()
    
    while any(t.is_alive() for t in threads):
        time.sleep(2)
        if time.time() - last_print >= 10:
            print_stats()
            last_print = time.time()
    
    # 4. 等待所有线程完成
    print("\n4️⃣  等待workers完成...")
    for t in threads:
        t.join()
    
    # 5. 额外等待让系统处理完消息
    print("\n5️⃣  等待系统处理 (20秒)...")
    for i in range(20):
        time.sleep(1)
        if (i + 1) % 5 == 0:
            s = stats.get_stats()
            db = check_db_stats()
            print(f"   [{i+1}s] DB: {db['messages']['sent']} sent, {db['tasks']['done']}/{db['tasks']['total']} tasks")
    
    # 6. 最终统计
    print("\n" + "=" * 80)
    print("📊 最终结果")
    print_stats()
    
    # 7. 成功率分析
    s = stats.get_stats()
    db = check_db_stats()
    
    if "error" not in db:
        success_rate = (s['messages_sent'] / (s['messages_sent'] + s['messages_failed'])) * 100 if (s['messages_sent'] + s['messages_failed']) > 0 else 0
        task_success_rate = (db['tasks']['done'] / db['tasks']['total']) * 100 if db['tasks']['total'] > 0 else 0
        
        print(f"\n🎯 性能指标:")
        print(f"  消息成功率: {success_rate:.1f}%")
        print(f"  Task成功率: {task_success_rate:.1f}%")
        print(f"  平均吞吐: {s['msg_per_sec']:.2f} msg/s")
        
        if success_rate >= 95 and task_success_rate >= 90:
            print(f"\n🎉 压测成功！系统表现优秀！")
        elif success_rate >= 80:
            print(f"\n✅ 压测通过，系统稳定")
        else:
            print(f"\n⚠️  压测发现问题，需要优化")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
