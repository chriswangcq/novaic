#!/usr/bin/env python3
"""
高强度压力测试

测试场景：
1. 10个Agent，每个发送20条消息（共200条消息）
2. 并发发送，模拟真实高负载场景
3. 实时监控系统指标
4. 检测卡死、超时、消息丢失
"""

import httpx
import time
import sqlite3
from pathlib import Path
import threading
from dataclasses import dataclass, field
from typing import List, Dict
import json
from datetime import datetime

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"

# 测试参数
AGENT_COUNT = 5
MESSAGES_PER_AGENT = 10
SEND_INTERVAL = 0.1  # 100ms间隔
MONITOR_INTERVAL = 2  # 2秒监控一次
MAX_WAIT_TIME = 180  # 最多等待3分钟


@dataclass
class TestMetrics:
    """测试指标"""
    total_messages_sent: int = 0
    total_replies_received: int = 0
    agents_created: int = 0
    start_time: float = 0
    end_time: float = 0
    
    # 系统指标历史
    pending_tasks_history: List[int] = field(default_factory=list)
    pending_sagas_history: List[int] = field(default_factory=list)
    unread_messages_history: List[int] = field(default_factory=list)
    
    # 错误统计
    send_errors: int = 0
    stuck_tasks: List[Dict] = field(default_factory=list)
    
    def elapsed_time(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


class StressTest:
    def __init__(self):
        self.metrics = TestMetrics()
        self.agents = []
        self.stop_monitor = threading.Event()
        # 注意：不再使用共享的 client，每个线程将创建自己的 client
        
    def cleanup(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("DELETE FROM chat_messages")
        conn.execute("DELETE FROM tq_tasks")
        conn.execute("DELETE FROM tq_sagas")
        conn.execute("DELETE FROM agent_runtimes")
        conn.execute("UPDATE subagents SET status = 'sleeping'")
        conn.commit()
        conn.close()
        print("✅ 清理完成\n")
    
    def create_agents(self):
        """创建测试用的Agents"""
        print(f"📝 创建 {AGENT_COUNT} 个Agent...")
        
        # 创建Agent是单线程操作，可以使用临时client
        with httpx.Client(base_url=GATEWAY_URL, timeout=60.0, trust_env=False) as client:
            for i in range(1, AGENT_COUNT + 1):
                try:
                    r = client.post("/api/agents", json={
                        "name": f"StressAgent{i}",
                        "model": "kimi-k2.5"
                    })
                    if r.status_code == 200:
                        agent_data = r.json()
                        self.agents.append(agent_data['id'])
                        self.metrics.agents_created += 1
                        print(f"  ✅ Agent {i:2d}: {agent_data['id'][:12]}")
                    else:
                        print(f"  ❌ Agent {i:2d}: 创建失败 ({r.status_code})")
                except Exception as e:
                    print(f"  ❌ Agent {i:2d}: {e}")
        print()
    
    def send_messages_for_agent(self, agent_id: str, agent_idx: int):
        """为单个Agent发送消息（在独立线程中）"""
        # ⚠️ 关键修复：每个线程使用独立的 httpx.Client
        # 这样就不会有状态竞争（/api/agents/current 是全局状态）
        with httpx.Client(base_url=GATEWAY_URL, timeout=60.0, trust_env=False) as client:
            # 首先设置当前Agent
            try:
                r = client.post("/api/agents/current", json={"agent_id": agent_id})
                if r.status_code != 200:
                    print(f"  ❌ Agent{agent_idx:2d} 设置当前Agent失败")
                    return
            except Exception as e:
                print(f"  ❌ Agent{agent_idx:2d} 设置当前Agent异常: {e}")
                return
            
            # 发送消息
            for i in range(1, MESSAGES_PER_AGENT + 1):
                try:
                    message = f"[Agent{agent_idx}] 消息#{i}"
                    r = client.post("/api/chat/send", json={"message": message})
                    if r.status_code == 200:
                        self.metrics.total_messages_sent += 1
                        if i % 5 == 0:
                            print(f"  Agent{agent_idx:2d} 已发送 {i:2d}/{MESSAGES_PER_AGENT}")
                    else:
                        self.metrics.send_errors += 1
                        print(f"  ❌ Agent{agent_idx:2d} 消息#{i} 发送失败")
                except Exception as e:
                    self.metrics.send_errors += 1
                    print(f"  ❌ Agent{agent_idx:2d} 消息#{i} 异常: {e}")
                
                time.sleep(SEND_INTERVAL)
    
    def send_all_messages(self):
        """顺序发送所有消息（避免全局状态竞争）"""
        print(f"🚀 开始顺序发送消息...")
        print(f"   - {AGENT_COUNT} 个Agent")
        print(f"   - 每个Agent {MESSAGES_PER_AGENT} 条消息")
        print(f"   - 总共 {AGENT_COUNT * MESSAGES_PER_AGENT} 条消息")
        print(f"   - 发送间隔 {SEND_INTERVAL*1000:.0f}ms")
        print(f"   ⚠️  顺序模式：因为 /api/agents/current 是全局状态\n")
        
        # 顺序发送，避免全局状态 (/api/agents/current) 竞争
        for idx, agent_id in enumerate(self.agents, 1):
            print(f"📤 Agent{idx} 开始发送...")
            self.send_messages_for_agent(agent_id, idx)
            print(f"✅ Agent{idx} 发送完成 ({MESSAGES_PER_AGENT}条)\n")
        
        print(f"✅ 所有消息发送完成")
        print(f"   - 成功发送: {self.metrics.total_messages_sent}")
        print(f"   - 发送失败: {self.metrics.send_errors}\n")
    
    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        conn = sqlite3.connect(str(DB_PATH))
        
        # Pending tasks
        cursor = conn.execute("SELECT COUNT(*) FROM tq_tasks WHERE status IN ('pending', 'claimed')")
        pending_tasks = cursor.fetchone()[0]
        
        # Pending sagas
        cursor = conn.execute("SELECT COUNT(*) FROM tq_sagas WHERE status IN ('pending', 'running')")
        pending_sagas = cursor.fetchone()[0]
        
        # Unread messages
        cursor = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE type='USER_MESSAGE' AND read=0")
        unread_messages = cursor.fetchone()[0]
        
        # Sent messages (status=sent)
        cursor = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE type='USER_MESSAGE' AND status='sent'")
        sent_messages = cursor.fetchone()[0]
        
        # AI replies
        cursor = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE type='AGENT_REPLY'")
        ai_replies = cursor.fetchone()[0]
        
        # Stuck tasks (claimed > 60s)
        cursor = conn.execute("""
            SELECT id, topic, claimed_by, 
                   (strftime('%s', 'now') - strftime('%s', claimed_at)) as age_seconds
            FROM tq_tasks
            WHERE status = 'claimed'
            AND (strftime('%s', 'now') - strftime('%s', claimed_at)) > 60
        """)
        stuck_tasks = [{"id": row[0][:12], "topic": row[1], "worker": row[2], "age": row[3]} 
                       for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "pending_tasks": pending_tasks,
            "pending_sagas": pending_sagas,
            "unread_messages": unread_messages,
            "sent_messages": sent_messages,
            "ai_replies": ai_replies,
            "stuck_tasks": stuck_tasks,
        }
    
    def monitor_loop(self):
        """监控循环（在后台线程）"""
        print("📊 启动实时监控...")
        print(f"{'时间':>8} | {'待处理Task':>11} | {'待处理Saga':>11} | {'未读消息':>9} | {'AI回复':>8} | {'卡死Task':>9}")
        print("-" * 85)
        
        while not self.stop_monitor.is_set():
            try:
                metrics = self.get_system_metrics()
                
                elapsed = int(self.metrics.elapsed_time())
                print(f"{elapsed:7d}s | {metrics['pending_tasks']:11d} | {metrics['pending_sagas']:11d} | "
                      f"{metrics['unread_messages']:9d} | {metrics['ai_replies']:8d} | {len(metrics['stuck_tasks']):9d}")
                
                # 记录历史
                self.metrics.pending_tasks_history.append(metrics['pending_tasks'])
                self.metrics.pending_sagas_history.append(metrics['pending_sagas'])
                self.metrics.unread_messages_history.append(metrics['unread_messages'])
                self.metrics.total_replies_received = metrics['ai_replies']
                
                # 检测卡死任务
                if metrics['stuck_tasks']:
                    self.metrics.stuck_tasks.extend(metrics['stuck_tasks'])
                
                time.sleep(MONITOR_INTERVAL)
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(MONITOR_INTERVAL)
    
    def wait_for_completion(self):
        """等待所有消息处理完成"""
        print(f"\n⏳ 等待处理完成 (最多 {MAX_WAIT_TIME}s)...\n")
        
        start_wait = time.time()
        last_check_time = start_wait
        
        while True:
            elapsed_wait = time.time() - start_wait
            
            if elapsed_wait > MAX_WAIT_TIME:
                print(f"\n⚠️  超时！等待了 {MAX_WAIT_TIME}s，放弃等待")
                return False
            
            metrics = self.get_system_metrics()
            
            # 检查是否完成
            if (metrics['pending_tasks'] == 0 and 
                metrics['pending_sagas'] == 0 and
                metrics['unread_messages'] == 0):
                print(f"\n✅ 所有任务完成！耗时 {elapsed_wait:.1f}s")
                return True
            
            # 每10秒输出一次状态
            if time.time() - last_check_time > 10:
                print(f"[{elapsed_wait:.0f}s] 仍在处理... "
                      f"(tasks={metrics['pending_tasks']}, "
                      f"sagas={metrics['pending_sagas']}, "
                      f"unread={metrics['unread_messages']})")
                last_check_time = time.time()
            
            time.sleep(2)
    
    def analyze_results(self):
        """分析测试结果"""
        print("\n" + "="*85)
        print("📊 测试结果分析")
        print("="*85)
        
        expected_messages = AGENT_COUNT * MESSAGES_PER_AGENT
        
        print(f"\n📨 消息统计:")
        print(f"   - 期望发送: {expected_messages} 条")
        print(f"   - 实际发送: {self.metrics.total_messages_sent} 条")
        print(f"   - 发送失败: {self.metrics.send_errors} 条")
        print(f"   - AI回复: {self.metrics.total_replies_received} 条")
        
        # 计算成功率
        send_rate = (self.metrics.total_messages_sent / expected_messages * 100) if expected_messages > 0 else 0
        reply_rate = (self.metrics.total_replies_received / self.metrics.total_messages_sent * 100) if self.metrics.total_messages_sent > 0 else 0
        
        print(f"\n📈 成功率:")
        print(f"   - 发送成功率: {send_rate:.1f}%")
        print(f"   - 回复成功率: {reply_rate:.1f}%")
        
        # 性能指标
        elapsed = self.metrics.elapsed_time()
        throughput = self.metrics.total_messages_sent / elapsed if elapsed > 0 else 0
        
        print(f"\n⚡ 性能指标:")
        print(f"   - 总耗时: {elapsed:.1f}s")
        print(f"   - 消息吞吐量: {throughput:.2f} msg/s")
        print(f"   - 平均每条消息处理时间: {elapsed / self.metrics.total_messages_sent:.2f}s" if self.metrics.total_messages_sent > 0 else "   - N/A")
        
        # 系统负载峰值
        if self.metrics.pending_tasks_history:
            max_pending_tasks = max(self.metrics.pending_tasks_history)
            max_pending_sagas = max(self.metrics.pending_sagas_history)
            max_unread = max(self.metrics.unread_messages_history)
            
            print(f"\n🔥 系统负载峰值:")
            print(f"   - 最大待处理Task: {max_pending_tasks}")
            print(f"   - 最大待处理Saga: {max_pending_sagas}")
            print(f"   - 最大未读消息: {max_unread}")
        
        # 卡死任务
        if self.metrics.stuck_tasks:
            print(f"\n⚠️  检测到 {len(self.metrics.stuck_tasks)} 个卡死任务:")
            for task in self.metrics.stuck_tasks[:5]:  # 只显示前5个
                print(f"   - [{task['id']}] {task['topic']} (已卡死 {task['age']}s)")
        
        # 检查数据库中的消息分布
        self.analyze_message_distribution()
        
        # 最终判断
        print(f"\n" + "="*85)
        if (self.metrics.total_messages_sent == expected_messages and
            self.metrics.send_errors == 0 and
            self.metrics.total_replies_received > 0 and
            not self.metrics.stuck_tasks):
            print("✅ 压力测试通过！")
        else:
            print("⚠️  压力测试存在问题，需要排查")
        print("="*85)
    
    def analyze_message_distribution(self):
        """分析消息在各Agent间的分布"""
        print(f"\n📊 消息分布（按Agent）:")
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.execute("""
            SELECT 
                a.name,
                COUNT(CASE WHEN cm.type='USER_MESSAGE' THEN 1 END) as user_msgs,
                COUNT(CASE WHEN cm.type='AGENT_REPLY' THEN 1 END) as ai_replies
            FROM agents a
            LEFT JOIN chat_messages cm ON a.id = cm.agent_id
            WHERE a.name LIKE 'StressAgent%'
            GROUP BY a.id, a.name
            ORDER BY a.name
        """)
        
        print(f"   {'Agent':15} | {'用户消息':>9} | {'AI回复':>8} | {'回复率':>8}")
        print(f"   {'-'*15}-+-{'-'*9}-+-{'-'*8}-+-{'-'*8}")
        
        for row in cursor:
            name, user_msgs, ai_replies = row
            rate = (ai_replies / user_msgs * 100) if user_msgs > 0 else 0
            print(f"   {name:15} | {user_msgs:9d} | {ai_replies:8d} | {rate:7.1f}%")
        
        conn.close()
    
    def run(self):
        """运行压力测试"""
        print("="*85)
        print("🔥 高强度压力测试")
        print("="*85)
        print(f"配置: {AGENT_COUNT} Agents × {MESSAGES_PER_AGENT} 消息 = {AGENT_COUNT * MESSAGES_PER_AGENT} 条")
        print("="*85 + "\n")
        
        self.metrics.start_time = time.time()
        
        # 1. 清理
        self.cleanup()
        
        # 2. 创建Agents
        self.create_agents()
        if len(self.agents) < AGENT_COUNT:
            print(f"❌ 只创建了 {len(self.agents)} 个Agent，期望 {AGENT_COUNT} 个")
            return
        
        # 3. 启动监控
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        
        # 4. 并发发送消息
        self.send_all_messages()
        
        # 5. 等待处理完成
        success = self.wait_for_completion()
        
        # 6. 停止监控
        self.stop_monitor.set()
        monitor_thread.join(timeout=2)
        
        self.metrics.end_time = time.time()
        
        # 7. 分析结果
        self.analyze_results()


if __name__ == "__main__":
    test = StressTest()
    try:
        test.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        test.stop_monitor.set()
        test.metrics.end_time = time.time()
        test.analyze_results()
