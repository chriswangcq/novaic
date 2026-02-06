#!/usr/bin/env python3
"""
Worker 健康诊断工具

用于排查 Task Worker 和 Saga Worker 是否卡住
"""

import sqlite3
import time
import psutil
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path.home() / ".novaic" / "novaic.db"


def get_worker_processes():
    """获取所有 Worker 进程信息"""
    workers = {
        'task_workers': [],
        'saga_workers': []
    }
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            
            if 'main_task.py' in cmdline:
                workers['task_workers'].append({
                    'pid': proc.info['pid'],
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                    'uptime_seconds': time.time() - proc.info['create_time'],
                    'cmdline': cmdline
                })
            elif 'main_saga.py' in cmdline:
                workers['saga_workers'].append({
                    'pid': proc.info['pid'],
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                    'uptime_seconds': time.time() - proc.info['create_time'],
                    'cmdline': cmdline
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return workers


def check_stuck_tasks():
    """检查卡住的 task"""
    conn = sqlite3.connect(str(DB_PATH))
    
    # 查找心跳超过 60 秒的 claimed task
    cursor = conn.execute("""
        SELECT 
            id,
            topic,
            claimed_by,
            claimed_at,
            heartbeat_at,
            round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as heartbeat_age_sec,
            round((julianday('now') - julianday(started_at)) * 86400, 2) as execution_time_sec,
            payload
        FROM tq_tasks
        WHERE status = 'claimed'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60
        ORDER BY heartbeat_at
    """)
    
    stuck_tasks = []
    for row in cursor:
        task_id, topic, claimed_by, claimed_at, heartbeat_at, heartbeat_age, exec_time, payload_json = row
        
        payload = json.loads(payload_json) if payload_json else {}
        
        stuck_tasks.append({
            'task_id': task_id,
            'topic': topic,
            'claimed_by': claimed_by,
            'claimed_at': claimed_at,
            'heartbeat_at': heartbeat_at,
            'heartbeat_age_sec': heartbeat_age,
            'execution_time_sec': exec_time,
            'payload': payload
        })
    
    conn.close()
    return stuck_tasks


def check_stuck_sagas():
    """检查卡住的 saga"""
    conn = sqlite3.connect(str(DB_PATH))
    
    # 查找心跳超过 60 秒的 running saga
    cursor = conn.execute("""
        SELECT 
            id,
            saga_type,
            claimed_by,
            current_step,
            claimed_at,
            heartbeat_at,
            round((julianday('now') - julianday(heartbeat_at)) * 86400, 2) as heartbeat_age_sec,
            context
        FROM tq_sagas
        WHERE status = 'running'
          AND (julianday('now') - julianday(heartbeat_at)) * 86400 > 60
        ORDER BY heartbeat_at
    """)
    
    stuck_sagas = []
    for row in cursor:
        saga_id, saga_type, claimed_by, current_step, claimed_at, heartbeat_at, heartbeat_age, context_json = row
        
        context = json.loads(context_json) if context_json else {}
        
        stuck_sagas.append({
            'saga_id': saga_id,
            'saga_type': saga_type,
            'claimed_by': claimed_by,
            'current_step': current_step,
            'claimed_at': claimed_at,
            'heartbeat_at': heartbeat_at,
            'heartbeat_age_sec': heartbeat_age,
            'context': context
        })
    
    conn.close()
    return stuck_sagas


def group_by_worker(stuck_items, key='claimed_by'):
    """按 Worker 分组"""
    groups = {}
    for item in stuck_items:
        worker = item.get(key)
        if worker not in groups:
            groups[worker] = []
        groups[worker].append(item)
    return groups


def check_recent_activity():
    """检查最近的活动"""
    conn = sqlite3.connect(str(DB_PATH))
    
    # 最近完成的 task
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as count,
            MAX(finished_at) as last_finished
        FROM tq_tasks
        WHERE status = 'done'
          AND finished_at > datetime('now', '-5 minutes')
    """)
    recent_tasks = cursor.fetchone()
    
    # 最近完成的 saga
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as count,
            MAX(completed_at) as last_completed
        FROM tq_sagas
        WHERE status = 'completed'
          AND completed_at > datetime('now', '-5 minutes')
    """)
    recent_sagas = cursor.fetchone()
    
    conn.close()
    
    return {
        'recent_tasks_count': recent_tasks[0],
        'last_task_finished': recent_tasks[1],
        'recent_sagas_count': recent_sagas[0],
        'last_saga_completed': recent_sagas[1]
    }


def diagnose():
    """执行诊断"""
    print("="*80)
    print("🔍 Worker 健康诊断")
    print("="*80)
    print(f"时间: {datetime.now().isoformat()}\n")
    
    # 1. 检查进程
    print("📊 进程状态")
    print("-"*80)
    workers = get_worker_processes()
    
    if not workers['task_workers']:
        print("❌ 没有找到 Task Worker 进程！")
    else:
        print(f"✅ Task Worker: {len(workers['task_workers'])} 个进程")
        for w in workers['task_workers']:
            uptime_min = w['uptime_seconds'] / 60
            print(f"   PID {w['pid']}: CPU {w['cpu_percent']:.1f}%, "
                  f"Memory {w['memory_mb']:.1f}MB, "
                  f"Uptime {uptime_min:.1f}min")
            
            # 检查异常
            if w['cpu_percent'] > 90:
                print(f"   ⚠️  CPU 使用率过高！")
            if w['memory_mb'] > 500:
                print(f"   ⚠️  内存使用过高！")
    
    if not workers['saga_workers']:
        print("❌ 没有找到 Saga Worker 进程！")
    else:
        print(f"\n✅ Saga Worker: {len(workers['saga_workers'])} 个进程")
        for w in workers['saga_workers']:
            uptime_min = w['uptime_seconds'] / 60
            print(f"   PID {w['pid']}: CPU {w['cpu_percent']:.1f}%, "
                  f"Memory {w['memory_mb']:.1f}MB, "
                  f"Uptime {uptime_min:.1f}min")
            
            # 检查异常
            if w['cpu_percent'] > 90:
                print(f"   ⚠️  CPU 使用率过高！")
            if w['memory_mb'] > 500:
                print(f"   ⚠️  内存使用过高！")
    
    # 2. 检查卡住的 task
    print("\n\n📋 卡住的 Task (心跳 > 60s)")
    print("-"*80)
    stuck_tasks = check_stuck_tasks()
    
    if not stuck_tasks:
        print("✅ 没有卡住的 task")
    else:
        print(f"❌ 发现 {len(stuck_tasks)} 个卡住的 task\n")
        
        # 按 Worker 分组
        task_groups = group_by_worker(stuck_tasks)
        
        for worker_id, tasks in task_groups.items():
            print(f"Worker: {worker_id} ({len(tasks)} 个 task 卡住)")
            for task in tasks[:5]:  # 只显示前 5 个
                print(f"  • {task['task_id'][:20]} ({task['topic']})")
                print(f"    心跳超时: {task['heartbeat_age_sec']:.0f}s")
                print(f"    执行时间: {task['execution_time_sec']:.0f}s")
                print(f"    认领时间: {task['claimed_at']}")
            if len(tasks) > 5:
                print(f"  ... 还有 {len(tasks) - 5} 个")
            print()
    
    # 3. 检查卡住的 saga
    print("\n📋 卡住的 Saga (心跳 > 60s)")
    print("-"*80)
    stuck_sagas = check_stuck_sagas()
    
    if not stuck_sagas:
        print("✅ 没有卡住的 saga")
    else:
        print(f"❌ 发现 {len(stuck_sagas)} 个卡住的 saga\n")
        
        # 按 Worker 分组
        saga_groups = group_by_worker(stuck_sagas)
        
        for worker_id, sagas in saga_groups.items():
            print(f"Worker: {worker_id} ({len(sagas)} 个 saga 卡住)")
            for saga in sagas[:5]:  # 只显示前 5 个
                print(f"  • {saga['saga_id'][:20]} ({saga['saga_type']})")
                print(f"    当前步骤: {saga['current_step']}")
                print(f"    心跳超时: {saga['heartbeat_age_sec']:.0f}s")
                print(f"    认领时间: {saga['claimed_at']}")
            if len(sagas) > 5:
                print(f"  ... 还有 {len(sagas) - 5} 个")
            print()
    
    # 4. 检查最近活动
    print("\n📈 最近活动 (5分钟内)")
    print("-"*80)
    activity = check_recent_activity()
    
    print(f"Task 完成数: {activity['recent_tasks_count']}")
    print(f"最后完成时间: {activity['last_task_finished'] or 'N/A'}")
    print(f"\nSaga 完成数: {activity['recent_sagas_count']}")
    print(f"最后完成时间: {activity['last_saga_completed'] or 'N/A'}")
    
    # 5. 综合判断
    print("\n\n🎯 诊断结论")
    print("="*80)
    
    issues = []
    
    if not workers['task_workers']:
        issues.append("❌ Task Worker 未运行")
    elif stuck_tasks:
        worker_ids = set(t['claimed_by'] for t in stuck_tasks)
        issues.append(f"❌ {len(worker_ids)} 个 Task Worker 有卡住的任务")
    
    if not workers['saga_workers']:
        issues.append("❌ Saga Worker 未运行")
    elif stuck_sagas:
        worker_ids = set(s['claimed_by'] for s in stuck_sagas)
        issues.append(f"❌ {len(worker_ids)} 个 Saga Worker 有卡住的任务")
    
    # 检查是否有集中在某个 Worker
    if stuck_tasks:
        task_groups = group_by_worker(stuck_tasks)
        for worker_id, tasks in task_groups.items():
            if len(tasks) >= 5:
                issues.append(f"⚠️  Worker {worker_id} 有 {len(tasks)} 个 task 卡住（可能进程有问题）")
    
    if stuck_sagas:
        saga_groups = group_by_worker(stuck_sagas)
        for worker_id, sagas in saga_groups.items():
            if len(sagas) >= 5:
                issues.append(f"⚠️  Worker {worker_id} 有 {len(sagas)} 个 saga 卡住（可能进程有问题）")
    
    # 检查最近是否有活动
    if activity['recent_tasks_count'] == 0:
        issues.append("⚠️  最近 5 分钟没有 task 完成（系统可能停滞）")
    
    if activity['recent_sagas_count'] == 0:
        issues.append("⚠️  最近 5 分钟没有 saga 完成（系统可能停滞）")
    
    if not issues:
        print("✅ 系统运行正常！")
    else:
        print("发现以下问题：\n")
        for issue in issues:
            print(issue)
        
        print("\n\n💡 建议操作：")
        if stuck_tasks or stuck_sagas:
            print("1. 清理卡住的 task 和 saga：")
            print("   python cleanup_stuck.py")
            print("\n2. 重启有问题的 Worker：")
            print("   pkill -f main_task && python main_task.py &")
            print("   pkill -f main_saga && python main_saga.py &")
    
    print("="*80)


if __name__ == "__main__":
    try:
        diagnose()
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
