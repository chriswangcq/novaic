#!/usr/bin/env python3
"""
分析 Agent Loop 的详细耗时
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".novaic" / "novaic.db"


def parse_time(time_str):
    """解析时间字符串"""
    if not time_str:
        return None
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))


def calculate_duration(start_str, end_str):
    """计算时长（秒）"""
    if not start_str or not end_str:
        return None
    start = parse_time(start_str)
    end = parse_time(end_str)
    return (end - start).total_seconds()


def analyze_round_timing():
    """分析每个 Round 的详细耗时"""
    conn = sqlite3.connect(str(DB_PATH))
    
    print("="*100)
    print("⏱️  Agent Loop 耗时分析")
    print("="*100)
    
    # 获取所有 react_think saga
    cursor = conn.execute("""
        SELECT 
            id,
            created_at,
            completed_at,
            context
        FROM tq_sagas
        WHERE saga_type = 'react_think'
          AND json_extract(context, '$.agent_id') LIKE 'df579f32%'
        ORDER BY created_at
    """)
    
    think_sagas = cursor.fetchall()
    
    print(f"\n📊 总共 {len(think_sagas)} 个 Agent Loop Round\n")
    
    total_round_time = 0
    total_llm_time = 0
    total_tool_time = 0
    
    for idx, saga in enumerate(think_sagas, 1):
        saga_id, created_at, completed_at, context_json = saga
        
        context = json.loads(context_json) if context_json else {}
        runtime_id = context.get('runtime_id', 'N/A')
        
        round_duration = calculate_duration(created_at, completed_at)
        total_round_time += round_duration if round_duration else 0
        
        print(f"\n{'='*100}")
        print(f"🔄 Round #{idx}")
        print(f"{'='*100}")
        print(f"Saga ID: {saga_id}")
        print(f"开始时间: {created_at}")
        print(f"结束时间: {completed_at}")
        print(f"总耗时: {round_duration:.2f}秒" if round_duration else "N/A")
        
        # 获取这个 Round 相关的所有 tasks
        cursor_tasks = conn.execute("""
            SELECT 
                topic,
                created_at,
                started_at,
                finished_at,
                status
            FROM tq_tasks
            WHERE json_extract(payload, '$.runtime_id') = ?
              AND created_at >= ?
              AND created_at <= ?
            ORDER BY created_at
        """, (runtime_id, created_at, completed_at))
        
        tasks = cursor_tasks.fetchall()
        
        print(f"\n📋 任务执行时间线:")
        print(f"{'任务':<25} {'等待时间':<12} {'执行时间':<12} {'状态':<10}")
        print("-" * 65)
        
        round_start = parse_time(created_at)
        
        for task in tasks:
            topic, task_created, task_started, task_finished, status = task
            
            # 相对于 Round 开始的时间
            relative_created = (parse_time(task_created) - round_start).total_seconds() if task_created else None
            
            # 等待时间 (created -> started)
            wait_time = calculate_duration(task_created, task_started)
            
            # 执行时间 (started -> finished)
            exec_time = calculate_duration(task_started, task_finished)
            
            wait_str = f"{wait_time:.2f}s" if wait_time else "N/A"
            exec_str = f"{exec_time:.2f}s" if exec_time else "N/A"
            
            print(f"{topic:<25} {wait_str:<12} {exec_str:<12} {status:<10}")
            
            # 累计 LLM 时间
            if topic == 'llm.call' and exec_time:
                total_llm_time += exec_time
            
            # 累计工具执行时间
            if topic == 'tool.execute' and exec_time:
                total_tool_time += exec_time
        
        # 查找对应的 react_actions saga
        cursor_actions = conn.execute("""
            SELECT 
                id,
                created_at,
                completed_at,
                context
            FROM tq_sagas
            WHERE saga_type = 'react_actions'
              AND json_extract(context, '$.runtime_id') = ?
              AND created_at >= ?
              AND created_at <= ?
            ORDER BY created_at
            LIMIT 1
        """, (runtime_id, created_at, completed_at))
        
        actions_saga = cursor_actions.fetchone()
        
        if actions_saga:
            actions_id, actions_created, actions_completed, actions_context_json = actions_saga
            actions_duration = calculate_duration(actions_created, actions_completed)
            
            print(f"\n⚡ react_actions:")
            print(f"   Saga ID: {actions_id}")
            print(f"   耗时: {actions_duration:.2f}秒" if actions_duration else "N/A")
            
            # 解析 tool_calls
            actions_context = json.loads(actions_context_json) if actions_context_json else {}
            tool_calls = actions_context.get('tool_calls', [])
            
            if tool_calls:
                print(f"   工具调用: {len(tool_calls)} 个")
                for tc in tool_calls:
                    func = tc.get('function', {})
                    print(f"     - {func.get('name', 'N/A')}")
        
        # 分析时间分布
        if round_duration and round_duration > 0:
            print(f"\n📊 时间分布:")
            
            # 计算各个阶段的时间
            llm_time = 0
            tool_time = 0
            other_time = 0
            
            for task in tasks:
                topic, task_created, task_started, task_finished, status = task
                exec_time = calculate_duration(task_started, task_finished)
                
                if exec_time:
                    if topic == 'llm.call':
                        llm_time = exec_time
                    elif topic == 'tool.execute':
                        tool_time += exec_time
                    else:
                        other_time += exec_time
            
            overhead = round_duration - llm_time - tool_time - other_time
            
            print(f"   LLM 调用:    {llm_time:>6.2f}s  ({llm_time/round_duration*100:>5.1f}%)")
            print(f"   工具执行:    {tool_time:>6.2f}s  ({tool_time/round_duration*100:>5.1f}%)")
            print(f"   其他任务:    {other_time:>6.2f}s  ({other_time/round_duration*100:>5.1f}%)")
            print(f"   调度开销:    {overhead:>6.2f}s  ({overhead/round_duration*100:>5.1f}%)")
        
        # 分析 Round 之间的间隔
        if idx < len(think_sagas):
            next_saga = think_sagas[idx]
            next_created = next_saga[1]
            gap = calculate_duration(completed_at, next_created)
            
            print(f"\n⏸️  与下一轮的间隔: {gap:.2f}秒" if gap else "")
            
            # 查看间隔期间在做什么
            if gap and gap > 1:
                cursor_gap = conn.execute("""
                    SELECT COUNT(*)
                    FROM chat_messages
                    WHERE type = 'USER_MESSAGE'
                      AND agent_id LIKE 'df579f32%'
                      AND created_at > ?
                      AND created_at < ?
                """, (completed_at, next_created))
                
                gap_messages = cursor_gap.fetchone()[0]
                
                if gap_messages > 0:
                    print(f"   💬 期间收到了 {gap_messages} 条新消息")
                else:
                    print(f"   ⚠️  没有新消息，为什么要等这么久？")
    
    # 总体统计
    print(f"\n\n{'='*100}")
    print("📈 总体统计")
    print("="*100)
    
    print(f"\nRound 总耗时: {total_round_time:.2f}秒")
    print(f"LLM 总耗时:   {total_llm_time:.2f}秒  ({total_llm_time/total_round_time*100:.1f}%)")
    print(f"工具总耗时:   {total_tool_time:.2f}秒  ({total_tool_time/total_round_time*100:.1f}%)")
    print(f"其他+开销:    {total_round_time - total_llm_time - total_tool_time:.2f}秒  ({(total_round_time - total_llm_time - total_tool_time)/total_round_time*100:.1f}%)")
    
    # 分析整个测试的时间线
    print(f"\n\n{'='*100}")
    print("⏰ 完整时间线")
    print("="*100)
    
    # 第一条消息到最后一条消息
    cursor = conn.execute("""
        SELECT 
            MIN(created_at) as first_msg,
            MAX(created_at) as last_msg,
            COUNT(*) as total_msgs
        FROM chat_messages
        WHERE type = 'USER_MESSAGE' AND agent_id LIKE 'df579f32%'
    """)
    
    first_msg, last_msg, total_msgs = cursor.fetchone()
    msg_duration = calculate_duration(first_msg, last_msg)
    
    print(f"\n消息接收:")
    print(f"  第一条消息: {first_msg}")
    print(f"  最后一条消息: {last_msg}")
    print(f"  持续时间: {msg_duration:.2f}秒" if msg_duration else "N/A")
    print(f"  消息总数: {total_msgs}")
    
    # 第一个 Round 到最后一个 Round
    first_round = think_sagas[0]
    last_round = think_sagas[-1]
    
    processing_duration = calculate_duration(first_round[1], last_round[2])
    
    print(f"\n处理时间:")
    print(f"  第一轮开始: {first_round[1]}")
    print(f"  最后轮结束: {last_round[2]}")
    print(f"  处理持续: {processing_duration:.2f}秒" if processing_duration else "N/A")
    
    # 延迟分析
    first_msg_time = parse_time(first_msg)
    first_round_time = parse_time(first_round[1])
    initial_delay = (first_round_time - first_msg_time).total_seconds()
    
    print(f"\n延迟分析:")
    print(f"  首条消息到首次处理: {initial_delay:.2f}秒")
    
    last_msg_time = parse_time(last_msg)
    last_round_complete = parse_time(last_round[2])
    total_delay = (last_round_complete - last_msg_time).total_seconds()
    
    print(f"  末条消息到处理完成: {total_delay:.2f}秒")
    
    conn.close()
    
    print("="*100)


if __name__ == "__main__":
    analyze_round_timing()
