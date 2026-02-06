#!/usr/bin/env python3
"""
全面冒烟测试脚本
跟踪所有 saga 和 task，检测问题
"""

import httpx
import time
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

DB_PATH = Path.home() / ".novaic" / "novaic.db"
GATEWAY_URL = "http://127.0.0.1:19999"


class TestMonitor:
    """测试监控器 - 跟踪 saga 和 task"""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_data = {
            "agents": [],
            "messages": [],
            "sagas": [],
            "tasks": [],
            "errors": [],
        }
    
    def log(self, msg: str, level: str = "INFO"):
        """带时间戳的日志"""
        elapsed = time.time() - self.start_time
        timestamp = f"[{elapsed:6.2f}s]"
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARN": "⚠️ ",
            "DEBUG": "🔍",
        }.get(level, "  ")
        print(f"{timestamp} {prefix} {msg}")
    
    def get_db_stats(self) -> Dict[str, Any]:
        """获取数据库统计"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        stats = {}
        
        # Saga 统计
        cursor = conn.execute("""
            SELECT saga_type, status, COUNT(*) as count
            FROM tq_sagas
            GROUP BY saga_type, status
        """)
        stats['sagas'] = {}
        for row in cursor.fetchall():
            key = f"{row['saga_type']}:{row['status']}"
            stats['sagas'][key] = row['count']
        
        # Task 统计
        cursor = conn.execute("""
            SELECT topic, status, COUNT(*) as count
            FROM tq_tasks
            GROUP BY topic, status
        """)
        stats['tasks'] = {}
        for row in cursor.fetchall():
            key = f"{row['topic']}:{row['status']}"
            stats['tasks'][key] = row['count']
        
        # 消息统计
        cursor = conn.execute("""
            SELECT type, COUNT(*) as count
            FROM chat_messages
            GROUP BY type
        """)
        stats['messages'] = {}
        for row in cursor.fetchall():
            stats['messages'][row['type']] = row['count']
        
        # Runtime 统计
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM agent_runtimes
            GROUP BY status
        """)
        stats['runtimes'] = {}
        for row in cursor.fetchall():
            stats['runtimes'][row['status']] = row['count']
        
        conn.close()
        return stats
    
    def get_recent_sagas(self, limit: int = 20) -> List[Dict]:
        """获取最近的 saga"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT id, saga_type, status, current_step, 
                   created_at, updated_at, step_results
            FROM tq_sagas
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        sagas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sagas
    
    def get_recent_tasks(self, limit: int = 30) -> List[Dict]:
        """获取最近的 task"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT id, topic, status, payload, result,
                   created_at, claimed_at, completed_at
            FROM tq_tasks
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    
    def detect_stuck_sagas(self) -> List[Dict]:
        """检测卡住的 saga"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        # 查找 running 状态超过 60 秒的 saga
        cursor = conn.execute("""
            SELECT id, saga_type, status, current_step,
                   (strftime('%s', 'now') - strftime('%s', updated_at)) as age_seconds
            FROM tq_sagas
            WHERE status = 'running'
            AND (strftime('%s', 'now') - strftime('%s', updated_at)) > 60
        """)
        
        stuck = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return stuck
    
    def detect_stuck_tasks(self) -> List[Dict]:
        """检测卡住的 task"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        
        # 查找 claimed 状态超过 60 秒的 task
        cursor = conn.execute("""
            SELECT id, topic, status, claimed_by,
                   (strftime('%s', 'now') - strftime('%s', claimed_at)) as age_seconds
            FROM tq_tasks
            WHERE status = 'claimed'
            AND (strftime('%s', 'now') - strftime('%s', claimed_at)) > 60
        """)
        
        stuck = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return stuck
    
    def print_stats(self, title: str = "当前状态"):
        """打印统计信息"""
        stats = self.get_db_stats()
        self.log(f"\n{'='*70}", "DEBUG")
        self.log(f"{title}", "DEBUG")
        self.log(f"{'='*70}", "DEBUG")
        
        if stats.get('sagas'):
            self.log("Saga 状态:", "DEBUG")
            for key, count in sorted(stats['sagas'].items()):
                self.log(f"  {key}: {count}", "DEBUG")
        
        if stats.get('tasks'):
            self.log("Task 状态:", "DEBUG")
            for key, count in sorted(stats['tasks'].items()):
                self.log(f"  {key}: {count}", "DEBUG")
        
        if stats.get('messages'):
            self.log("消息统计:", "DEBUG")
            for msg_type, count in sorted(stats['messages'].items()):
                self.log(f"  {msg_type}: {count}", "DEBUG")
        
        self.log(f"{'='*70}\n", "DEBUG")
    
    def check_for_issues(self) -> bool:
        """检查是否有问题"""
        has_issues = False
        
        # 检查卡住的 saga
        stuck_sagas = self.detect_stuck_sagas()
        if stuck_sagas:
            has_issues = True
            self.log(f"发现 {len(stuck_sagas)} 个卡住的 Saga:", "ERROR")
            for saga in stuck_sagas:
                self.log(f"  - {saga['saga_type']} (id: {saga['id'][:12]}, age: {saga['age_seconds']}s)", "ERROR")
                self.test_data['errors'].append({
                    'type': 'stuck_saga',
                    'saga': saga
                })
        
        # 检查卡住的 task
        stuck_tasks = self.detect_stuck_tasks()
        if stuck_tasks:
            has_issues = True
            self.log(f"发现 {len(stuck_tasks)} 个卡住的 Task:", "ERROR")
            for task in stuck_tasks:
                self.log(f"  - {task['topic']} (id: {task['id'][:12]}, age: {task['age_seconds']}s)", "ERROR")
                self.test_data['errors'].append({
                    'type': 'stuck_task',
                    'task': task
                })
        
        return has_issues


class SmokeTest:
    """冒烟测试执行器"""
    
    def __init__(self):
        self.monitor = TestMonitor()
        self.client = httpx.Client(base_url=GATEWAY_URL, timeout=30.0, trust_env=False)
    
    def cleanup(self):
        """清理测试数据"""
        self.monitor.log("清理测试数据...", "INFO")
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("DELETE FROM chat_messages")
        conn.execute("DELETE FROM tq_tasks")
        conn.execute("DELETE FROM tq_sagas")
        conn.execute("DELETE FROM agent_runtimes")
        conn.execute("UPDATE subagents SET status = 'sleeping'")
        conn.commit()
        conn.close()
        self.monitor.log("清理完成", "SUCCESS")
    
    def create_agent(self, name: str, model: str = "kimi-k2.5") -> str:
        """创建 agent"""
        self.monitor.log(f"创建 Agent: {name} (model={model})", "INFO")
        try:
            r = self.client.post("/api/agents", json={
                "name": name,
                "model": model
            })
            r.raise_for_status()
            agent = r.json()
            agent_id = agent['id']
            self.monitor.log(f"  ✓ Agent ID: {agent_id[:12]}", "SUCCESS")
            self.monitor.test_data['agents'].append({
                'id': agent_id,
                'name': name,
                'model': model
            })
            return agent_id
        except Exception as e:
            self.monitor.log(f"创建 Agent 失败: {e}", "ERROR")
            raise
    
    def set_current_agent(self, agent_id: str):
        """设置当前 agent"""
        try:
            self.client.post("/api/agents/current", json={"agent_id": agent_id})
        except Exception as e:
            self.monitor.log(f"设置当前 Agent 失败: {e}", "ERROR")
            raise
    
    def send_message(self, content: str, agent_id: Optional[str] = None) -> str:
        """发送消息"""
        if agent_id:
            self.set_current_agent(agent_id)
        
        self.monitor.log(f"发送消息: {content[:50]}...", "INFO")
        try:
            r = self.client.post("/api/chat/send", json={"message": content})
            r.raise_for_status()
            data = r.json()
            msg_id = data['message_id']
            self.monitor.log(f"  ✓ Message ID: {msg_id[:12]}", "SUCCESS")
            self.monitor.test_data['messages'].append({
                'id': msg_id,
                'content': content,
                'agent_id': agent_id,
                'timestamp': time.time()
            })
            return msg_id
        except Exception as e:
            self.monitor.log(f"发送消息失败: {e}", "ERROR")
            raise
    
    def wait_for_completion(self, max_wait: int = 45, check_interval: int = 2):
        """等待所有 saga/task 完成"""
        self.monitor.log(f"等待处理完成 (最多 {max_wait}s)...", "INFO")
        
        for i in range(0, max_wait, check_interval):
            time.sleep(check_interval)
            
            stats = self.monitor.get_db_stats()
            
            # 检查是否有 pending/claimed/running 的任务
            has_pending = any(
                'pending' in k or 'claimed' in k 
                for k in stats.get('tasks', {}).keys()
            )
            has_running_sagas = any(
                'running' in k 
                for k in stats.get('sagas', {}).keys()
            )
            
            if not has_pending and not has_running_sagas:
                self.monitor.log(f"所有任务完成 ({i+check_interval}s)", "SUCCESS")
                return True
            
            # 每 10 秒打印一次状态
            if (i + check_interval) % 10 == 0:
                self.monitor.log(f"[{i+check_interval}s] 仍在处理中...", "DEBUG")
        
        self.monitor.log(f"等待超时 ({max_wait}s)", "WARN")
        return False
    
    def verify_agent_replies(self, expected_count: int) -> bool:
        """验证 AI 回复数量"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE type='AGENT_REPLY'"
        )
        count = cursor.fetchone()[0]
        conn.close()
        
        if count >= expected_count:
            self.monitor.log(f"✓ 收到 {count} 条 AI 回复 (期望 >= {expected_count})", "SUCCESS")
            return True
        else:
            self.monitor.log(f"✗ 只收到 {count} 条 AI 回复 (期望 >= {expected_count})", "ERROR")
            return False
    
    def test_multiple_messages(self, count: int = 3):
        """测试1: 多条消息发送"""
        self.monitor.log("\n" + "="*70, "INFO")
        self.monitor.log("测试1: 多条消息连续发送", "INFO")
        self.monitor.log("="*70, "INFO")
        
        # 创建一个 agent
        agent_id = self.create_agent("MultiMsgAgent")
        
        # 连续发送多条消息
        self.monitor.log(f"连续发送 {count} 条消息...", "INFO")
        for i in range(count):
            self.send_message(f"消息#{i+1}: 请简短回复收到", agent_id)
            time.sleep(1)  # 间隔1秒
        
        # 等待处理
        self.wait_for_completion(max_wait=60)
        
        # 打印状态
        self.monitor.print_stats("测试1完成后状态")
        
        # 验证回复
        success = self.verify_agent_replies(count)
        
        # 检查问题
        has_issues = self.monitor.check_for_issues()
        
        return success and not has_issues
    
    def test_single_agent_multi_turn(self, turns: int = 3):
        """测试2: 单agent多轮连续对话"""
        self.monitor.log("\n" + "="*70, "INFO")
        self.monitor.log("测试2: 单Agent多轮连续对话", "INFO")
        self.monitor.log("="*70, "INFO")
        
        # 创建一个 agent
        agent_id = self.create_agent("SingleAgentMultiTurn")
        
        # 多轮对话
        self.monitor.log(f"进行 {turns} 轮对话...", "INFO")
        for i in range(turns):
            self.send_message(f"第{i+1}轮: 你好，请回复轮次{i+1}", agent_id)
            
            # 等待本轮完成
            self.monitor.log(f"等待第{i+1}轮完成...", "DEBUG")
            self.wait_for_completion(max_wait=30)
            time.sleep(2)  # 轮次间隔
        
        # 打印状态
        self.monitor.print_stats("测试2完成后状态")
        
        # 验证回复
        success = self.verify_agent_replies(turns)
        
        # 检查问题
        has_issues = self.monitor.check_for_issues()
        
        return success and not has_issues
    
    def test_multi_agent_multi_turn(self, agent_count: int = 2, turns: int = 2):
        """测试3: 多agent多轮连续对话"""
        self.monitor.log("\n" + "="*70, "INFO")
        self.monitor.log("测试3: 多Agent多轮连续对话", "INFO")
        self.monitor.log("="*70, "INFO")
        
        # 创建多个 agent
        agents = []
        for i in range(agent_count):
            agent_id = self.create_agent(f"MultiAgent{i+1}")
            agents.append(agent_id)
        
        # 轮流与每个 agent 对话
        total_messages = 0
        for turn in range(turns):
            self.monitor.log(f"第{turn+1}轮对话...", "INFO")
            for i, agent_id in enumerate(agents):
                self.send_message(
                    f"这是第{turn+1}条消息。请回复：'我是[你的名字]，收到第{turn+1}条消息'",
                    agent_id
                )
                total_messages += 1
                time.sleep(1)
        
        # 等待全部完成
        self.wait_for_completion(max_wait=90)
        
        # 打印状态
        self.monitor.print_stats("测试3完成后状态")
        
        # 验证回复
        success = self.verify_agent_replies(total_messages)
        
        # 检查问题
        has_issues = self.monitor.check_for_issues()
        
        return success and not has_issues
    
    def run_all_tests(self):
        """运行所有测试"""
        self.monitor.log("\n" + "🎯"*35, "INFO")
        self.monitor.log("开始全面冒烟测试", "INFO")
        self.monitor.log("🎯"*35 + "\n", "INFO")
        
        results = {}
        
        try:
            # 清理
            self.cleanup()
            time.sleep(2)
            
            # 测试1: 多条消息
            try:
                results['test1'] = self.test_multiple_messages(count=3)
                time.sleep(5)
            except Exception as e:
                self.monitor.log(f"测试1异常: {e}", "ERROR")
                results['test1'] = False
            
            # 清理
            self.cleanup()
            time.sleep(2)
            
            # 测试2: 单agent多轮
            try:
                results['test2'] = self.test_single_agent_multi_turn(turns=3)
                time.sleep(5)
            except Exception as e:
                self.monitor.log(f"测试2异常: {e}", "ERROR")
                results['test2'] = False
            
            # 清理
            self.cleanup()
            time.sleep(2)
            
            # 测试3: 多agent多轮
            try:
                results['test3'] = self.test_multi_agent_multi_turn(agent_count=2, turns=2)
            except Exception as e:
                self.monitor.log(f"测试3异常: {e}", "ERROR")
                results['test3'] = False
            
        finally:
            self.client.close()
        
        # 总结
        self.print_summary(results)
        
        return all(results.values())
    
    def print_summary(self, results: Dict[str, bool]):
        """打印测试总结"""
        self.monitor.log("\n" + "="*70, "INFO")
        self.monitor.log("测试总结", "INFO")
        self.monitor.log("="*70, "INFO")
        
        test_names = {
            'test1': '测试1: 多条消息连续发送',
            'test2': '测试2: 单Agent多轮连续对话',
            'test3': '测试3: 多Agent多轮连续对话',
        }
        
        for test_key, test_name in test_names.items():
            result = results.get(test_key)
            if result is True:
                self.monitor.log(f"✅ {test_name}: 通过", "SUCCESS")
            elif result is False:
                self.monitor.log(f"❌ {test_name}: 失败", "ERROR")
            else:
                self.monitor.log(f"⚠️  {test_name}: 未运行", "WARN")
        
        # 总体结果
        total = len(results)
        passed = sum(1 for v in results.values() if v is True)
        
        self.monitor.log("\n" + "="*70, "INFO")
        if passed == total:
            self.monitor.log(f"🎉 所有测试通过! ({passed}/{total})", "SUCCESS")
        else:
            self.monitor.log(f"⚠️  部分测试失败: {passed}/{total} 通过", "WARN")
        
        # 错误汇总
        if self.monitor.test_data['errors']:
            self.monitor.log("\n发现的问题:", "ERROR")
            for i, error in enumerate(self.monitor.test_data['errors'], 1):
                self.monitor.log(f"{i}. {error['type']}: {error}", "ERROR")
        
        self.monitor.log("="*70, "INFO")
        
        total_time = time.time() - self.monitor.start_time
        self.monitor.log(f"总耗时: {total_time:.2f}秒", "INFO")


def main():
    """主函数"""
    # 检查数据库是否存在
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("请先启动 Gateway")
        sys.exit(1)
    
    # 检查 Gateway 是否运行
    try:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            r = client.get(f"{GATEWAY_URL}/api/health")
            if r.status_code not in [200, 503]:  # 503 可能是部分不健康但仍可用
                print(f"❌ Gateway 未运行或不健康: status={r.status_code}")
                sys.exit(1)
            print(f"✓ Gateway 状态: {r.text}")
    except Exception as e:
        print(f"❌ 无法连接到 Gateway: {e}")
        sys.exit(1)
    
    # 运行测试
    tester = SmokeTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
