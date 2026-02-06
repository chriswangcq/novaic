#!/usr/bin/env python3
"""
实时监控 Worker 状态

持续监控 Task 和 Saga Worker，检测异常
"""

import sqlite3
import time
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path.home() / ".novaic" / "novaic.db"

# 监控间隔
MONITOR_INTERVAL = 5  # 秒

# 阈值
MAX_PENDING_TASKS = 100
MAX_PENDING_SAGAS = 50
MAX_STUCK_TASKS = 5
MAX_STUCK_SAGAS = 5


class WorkerMonitor:
    def __init__(self):
        self.last_task_count = 0
        self.last_saga_count = 0
        self.stuck_history = defaultdict(list)
    
    def get_stats(self):
        """获取当前统计"""
        conn = sqlite3.connect(str(DB_PATH))
        
        stats = {}
        
        # Task 统计
        cursor = conn.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM tq_tasks
            WHERE created_at > datetime('now', '-10 minutes')
            GROUP BY status
        """)
        stats['tasks'] = {row[0]: row[1] for row in cursor}
        
        # Saga 统计
        cursor = conn.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM tq_sagas
            WHERE created_at > datetime('now', '-10 minutes')
            GROUP BY status
        """)
        stats['sagas'] = {row[0]: row[1] for row in cursor}
        
        # 卡住的 task
        cursor = conn.execute("""
            SELECT COUNT(*) FROM tq_tasks
            WHERE status = 'claimed'
              AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60
        """)
        stats['stuck_tasks'] = cursor.fetchone()[0]
        
        # 卡住的 saga
        cursor = conn.execute("""
            SELECT COUNT(*) FROM tq_sagas
            WHERE status = 'running'
              AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60
        """)
        stats['stuck_sagas'] = cursor.fetchone()[0]
        
        # 最近完成的任务
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as count,
                MAX(finished_at) as last_time
            FROM tq_tasks
            WHERE status = 'done'
              AND finished_at > datetime('now', '-1 minute')
        """)
        row = cursor.fetchone()
        stats['recent_task_done'] = row[0]
        stats['last_task_time'] = row[1]
        
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as count,
                MAX(completed_at) as last_time
            FROM tq_sagas
            WHERE status = 'completed'
              AND completed_at > datetime('now', '-1 minute')
        """)
        row = cursor.fetchone()
        stats['recent_saga_done'] = row[0]
        stats['last_saga_time'] = row[1]
        
        conn.close()
        return stats
    
    def check_alerts(self, stats):
        """检查告警"""
        alerts = []
        
        # 检查卡住的任务
        if stats['stuck_tasks'] >= MAX_STUCK_TASKS:
            alerts.append(('ERROR', f"有 {stats['stuck_tasks']} 个 task 卡住！"))
        
        if stats['stuck_sagas'] >= MAX_STUCK_SAGAS:
            alerts.append(('ERROR', f"有 {stats['stuck_sagas']} 个 saga 卡住！"))
        
        # 检查堆积
        pending_tasks = stats['tasks'].get('pending', 0) + stats['tasks'].get('claimed', 0)
        if pending_tasks > MAX_PENDING_TASKS:
            alerts.append(('WARN', f"Task 队列堆积: {pending_tasks} 个待处理"))
        
        pending_sagas = stats['sagas'].get('pending', 0) + stats['sagas'].get('running', 0)
        if pending_sagas > MAX_PENDING_SAGAS:
            alerts.append(('WARN', f"Saga 队列堆积: {pending_sagas} 个待处理"))
        
        # 检查是否有活动
        if stats['recent_task_done'] == 0:
            alerts.append(('WARN', "最近 1 分钟没有 task 完成"))
        
        if stats['recent_saga_done'] == 0:
            alerts.append(('WARN', "最近 1 分钟没有 saga 完成"))
        
        return alerts
    
    def display_stats(self, stats, alerts):
        """显示统计信息"""
        # 清屏
        os.system('clear' if os.name != 'nt' else 'cls')
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("="*80)
        print(f"⏱️  Worker 实时监控 - {now}")
        print("="*80)
        
        # Task 统计
        print("\n📋 Task 队列 (最近 10 分钟):")
        tasks = stats['tasks']
        print(f"  Pending: {tasks.get('pending', 0):>4}  "
              f"Claimed: {tasks.get('claimed', 0):>4}  "
              f"Done: {tasks.get('done', 0):>4}  "
              f"Failed: {tasks.get('failed', 0):>4}")
        
        # Saga 统计
        print("\n📊 Saga 队列 (最近 10 分钟):")
        sagas = stats['sagas']
        print(f"  Pending: {sagas.get('pending', 0):>4}  "
              f"Running: {sagas.get('running', 0):>4}  "
              f"Completed: {sagas.get('completed', 0):>4}  "
              f"Failed: {sagas.get('failed', 0):>4}")
        
        # 最近活动
        print("\n⏱️  最近活动 (1 分钟内):")
        print(f"  Task 完成: {stats['recent_task_done']} 个")
        print(f"  Saga 完成: {stats['recent_saga_done']} 个")
        
        # 卡住的任务
        print(f"\n⚠️  卡住的任务 (心跳 > 60s):")
        print(f"  Task: {stats['stuck_tasks']}")
        print(f"  Saga: {stats['stuck_sagas']}")
        
        # 告警
        if alerts:
            print("\n🚨 告警:")
            for level, message in alerts:
                icon = "🔴" if level == 'ERROR' else "🟡"
                print(f"  {icon} [{level}] {message}")
        else:
            print("\n✅ 系统运行正常")
        
        print("\n" + "="*80)
        print("按 Ctrl+C 停止监控")
    
    def run(self):
        """运行监控"""
        print("🚀 启动 Worker 监控...")
        print(f"监控间隔: {MONITOR_INTERVAL} 秒\n")
        
        try:
            while True:
                stats = self.get_stats()
                alerts = self.check_alerts(stats)
                self.display_stats(stats, alerts)
                
                time.sleep(MONITOR_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n👋 停止监控")
        except Exception as e:
            print(f"\n\n❌ 监控失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    monitor = WorkerMonitor()
    monitor.run()
