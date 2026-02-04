#!/usr/bin/env python3
"""
清理卡住的 Task 和 Saga

自动检测并清理心跳超时的任务
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".novaic" / "novaic.db"

TASK_TIMEOUT = 60  # 任务心跳超时阈值（秒）
SAGA_TIMEOUT = 60  # Saga 心跳超时阈值（秒）


def cleanup_stuck_tasks(dry_run=False):
    """清理卡住的 task"""
    conn = sqlite3.connect(str(DB_PATH))
    
    # 查找超时的 task
    cursor = conn.execute("""
        SELECT 
            id,
            topic,
            claimed_by,
            round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as age
        FROM tq_tasks
        WHERE status = 'claimed'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > ?
    """, (TASK_TIMEOUT,))
    
    stuck_tasks = cursor.fetchall()
    
    if not stuck_tasks:
        print("✅ 没有发现卡住的 task")
        conn.close()
        return 0
    
    print(f"🔍 发现 {len(stuck_tasks)} 个卡住的 task:")
    for task_id, topic, claimed_by, age in stuck_tasks:
        print(f"  • {task_id[:20]} ({topic}) - 心跳超时 {age:.0f}s - Worker: {claimed_by}")
    
    if dry_run:
        print("\n⚠️  试运行模式，不执行清理")
        conn.close()
        return len(stuck_tasks)
    
    # 标记为 failed
    conn.execute("""
        UPDATE tq_tasks 
        SET status = 'failed',
            error = 'Cleanup: heartbeat timeout > ' || ? || 's',
            finished_at = datetime('now')
        WHERE status = 'claimed'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > ?
    """, (TASK_TIMEOUT, TASK_TIMEOUT))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 已清理 {len(stuck_tasks)} 个 task")
    return len(stuck_tasks)


def cleanup_stuck_sagas(dry_run=False):
    """清理卡住的 saga"""
    conn = sqlite3.connect(str(DB_PATH))
    
    # 查找超时的 saga
    cursor = conn.execute("""
        SELECT 
            id,
            saga_type,
            claimed_by,
            current_step,
            round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as age
        FROM tq_sagas
        WHERE status = 'running'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > ?
    """, (SAGA_TIMEOUT,))
    
    stuck_sagas = cursor.fetchall()
    
    if not stuck_sagas:
        print("\n✅ 没有发现卡住的 saga")
        conn.close()
        return 0
    
    print(f"\n🔍 发现 {len(stuck_sagas)} 个卡住的 saga:")
    for saga_id, saga_type, claimed_by, step, age in stuck_sagas:
        print(f"  • {saga_id[:20]} ({saga_type}) - 步骤 {step} - 心跳超时 {age:.0f}s - Worker: {claimed_by}")
    
    if dry_run:
        print("\n⚠️  试运行模式，不执行清理")
        conn.close()
        return len(stuck_sagas)
    
    # 标记为 failed
    conn.execute("""
        UPDATE tq_sagas 
        SET status = 'failed',
            error = 'Cleanup: heartbeat timeout > ' || ? || 's',
            completed_at = datetime('now')
        WHERE status = 'running'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > ?
    """, (SAGA_TIMEOUT, SAGA_TIMEOUT))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 已清理 {len(stuck_sagas)} 个 saga")
    return len(stuck_sagas)


def main():
    print("="*80)
    print("🧹 清理卡住的 Task 和 Saga")
    print("="*80)
    print(f"时间: {datetime.now().isoformat()}")
    print(f"超时阈值: Task {TASK_TIMEOUT}s, Saga {SAGA_TIMEOUT}s\n")
    
    # 先试运行看看有多少
    import sys
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if dry_run:
        print("⚠️  试运行模式 (使用 --execute 执行实际清理)\n")
    
    task_count = cleanup_stuck_tasks(dry_run=dry_run)
    saga_count = cleanup_stuck_sagas(dry_run=dry_run)
    
    total = task_count + saga_count
    
    print("\n" + "="*80)
    if dry_run and total > 0:
        print(f"💡 发现 {total} 个卡住的任务")
        print("   使用 'python cleanup_stuck.py --execute' 执行清理")
    elif total > 0:
        print(f"✅ 清理完成！共处理 {total} 个任务")
        print("   建议重启相关的 Worker 进程")
    else:
        print("✅ 系统正常，无需清理")
    print("="*80)


if __name__ == "__main__":
    import sys
    
    if '--execute' in sys.argv:
        # 移除 --dry-run 标志
        sys.argv = [arg for arg in sys.argv if arg not in ['--dry-run', '-n']]
    
    main()
