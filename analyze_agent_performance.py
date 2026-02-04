#!/usr/bin/env python3
"""
分析 Agent 性能和健康状况

查看 Agent Loop 的详细表现：
- React Think/Action 执行情况
- 每轮处理的消息数
- LLM 调用情况
- 异常和错误
"""

import sqlite3
import json
from collections import defaultdict
from datetime import datetime

DB_PATH = "/Users/wangchaoqun/.novaic/novaic.db"


def analyze_agent_loops():
    """分析 Agent Loop 的执行情况"""
    print("=" * 80)
    print("🔍 Agent Loop 健康分析")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. 获取最近的 Runtime
    print("\n[1] 最近的 Runtime 状态")
    print("-" * 80)
    
    cursor = conn.execute("""
        SELECT runtime_id, agent_id, subagent_id, status, phase,
               current_round_num, created_at, updated_at
        FROM agent_runtimes
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    runtimes = cursor.fetchall()
    print(f"\n找到 {len(runtimes)} 个最近的 Runtime:\n")
    
    for rt in runtimes:
        print(f"  Runtime: {rt['runtime_id']}")
        print(f"    Agent: {rt['agent_id']}")
        print(f"    SubAgent: {rt['subagent_id']}")
        print(f"    状态: {rt['status']}, Phase: {rt['phase']}")
        print(f"    当前轮数: {rt['current_round_num']}")
        print(f"    创建: {rt['created_at']}")
        print()
    
    # 2. 分析 React Think Saga
    print("\n[2] React Think Saga 分析")
    print("-" * 80)
    
    cursor = conn.execute("""
        SELECT id, status, step_results, error, 
               created_at, completed_at,
               julianday(completed_at) - julianday(created_at) as duration_days
        FROM tq_sagas
        WHERE saga_type = 'react_think'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    think_sagas = cursor.fetchall()
    print(f"\n找到 {len(think_sagas)} 个最近的 React Think Saga:\n")
    
    for i, saga in enumerate(think_sagas, 1):
        duration_sec = saga['duration_days'] * 86400 if saga['duration_days'] else 0
        
        print(f"  [{i}] Saga: {saga['id']}")
        print(f"      状态: {saga['status']}")
        print(f"      耗时: {duration_sec:.2f}s")
        
        if saga['step_results']:
            try:
                results = json.loads(saga['step_results'])
                print(f"      步骤数: {len(results)}")
                
                # 分析每个步骤
                for step_name, step_result in results.items():
                    if isinstance(step_result, dict):
                        if 'new_messages' in step_result:
                            print(f"        - {step_name}: 读取 {len(step_result.get('new_messages', []))} 条新消息")
                        elif 'prompt_tokens' in step_result:
                            print(f"        - {step_name}: LLM 调用 (prompt: {step_result.get('prompt_tokens', 0)}, completion: {step_result.get('completion_tokens', 0)})")
                        elif 'tool_calls' in step_result:
                            print(f"        - {step_name}: {len(step_result.get('tool_calls', []))} 个工具调用")
                        else:
                            print(f"        - {step_name}: {step_result.get('success', 'unknown')}")
            except:
                pass
        
        if saga['error']:
            print(f"      ❌ 错误: {saga['error'][:100]}")
        
        print()
    
    # 3. 分析 React Actions
    print("\n[3] React Actions 分析")
    print("-" * 80)
    
    cursor = conn.execute("""
        SELECT id, status, step_results, error,
               created_at, completed_at,
               julianday(completed_at) - julianday(created_at) as duration_days
        FROM tq_sagas
        WHERE saga_type = 'react_actions'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    action_sagas = cursor.fetchall()
    print(f"\n找到 {len(action_sagas)} 个最近的 React Actions:\n")
    
    for i, saga in enumerate(action_sagas, 1):
        duration_sec = saga['duration_days'] * 86400 if saga['duration_days'] else 0
        
        print(f"  [{i}] Saga: {saga['id']}")
        print(f"      状态: {saga['status']}")
        print(f"      耗时: {duration_sec:.2f}s")
        
        if saga['step_results']:
            try:
                results = json.loads(saga['step_results'])
                print(f"      步骤数: {len(results)}")
                
                # 统计工具调用
                tool_count = 0
                for step_name, step_result in results.items():
                    if isinstance(step_result, dict) and 'success' in step_result:
                        tool_count += 1
                
                if tool_count > 0:
                    print(f"      工具执行: {tool_count} 个")
            except:
                pass
        
        if saga['error']:
            print(f"      ❌ 错误: {saga['error'][:100]}")
        
        print()
    
    # 4. 统计 Saga 执行效率
    print("\n[4] Saga 执行效率统计")
    print("-" * 80)
    
    cursor = conn.execute("""
        SELECT saga_type, status, COUNT(*) as cnt,
               AVG(julianday(completed_at) - julianday(created_at)) * 86400 as avg_duration_sec
        FROM tq_sagas
        WHERE saga_type IN ('react_think', 'react_actions', 'message_process')
          AND created_at > datetime('now', '-1 hour')
        GROUP BY saga_type, status
        ORDER BY saga_type, status
    """)
    
    print("\n最近 1 小时的 Saga 统计:\n")
    
    for row in cursor.fetchall():
        print(f"  {row['saga_type']:20} | {row['status']:10} | 数量: {row['cnt']:4} | 平均耗时: {row['avg_duration_sec']:.2f}s")
    
    # 5. 查看具体的 Agent Loop Round
    print("\n\n[5] 详细的 Agent Loop Round 分析")
    print("-" * 80)
    
    # 选一个最近的 runtime 来详细分析
    if runtimes:
        runtime_id = runtimes[0]['runtime_id']
        print(f"\n分析 Runtime: {runtime_id}\n")
        
        # 获取这个 runtime 的所有 think saga
        cursor = conn.execute("""
            SELECT id, status, step_results, error,
                   created_at, completed_at,
                   julianday(completed_at) - julianday(created_at) as duration_days
            FROM tq_sagas
            WHERE saga_type = 'react_think'
              AND json_extract(context, '$.runtime_id') = ?
            ORDER BY created_at ASC
        """, (runtime_id,))
        
        rounds = cursor.fetchall()
        print(f"共 {len(rounds)} 轮 Agent Loop:\n")
        
        for i, round_saga in enumerate(rounds, 1):
            duration_sec = round_saga['duration_days'] * 86400 if round_saga['duration_days'] else 0
            
            print(f"  🔄 Round {i}")
            print(f"     Saga ID: {round_saga['id']}")
            print(f"     状态: {round_saga['status']}")
            print(f"     耗时: {duration_sec:.2f}s")
            
            if round_saga['step_results']:
                try:
                    results = json.loads(round_saga['step_results'])
                    
                    # context.read
                    if 'context.read' in results:
                        ctx_read = results['context.read']
                        if isinstance(ctx_read, dict):
                            new_msg_count = len(ctx_read.get('new_messages', []))
                            print(f"     📖 读取消息: {new_msg_count} 条新消息")
                    
                    # llm.call
                    if 'llm.call' in results:
                        llm_call = results['llm.call']
                        if isinstance(llm_call, dict):
                            print(f"     🤖 LLM 调用:")
                            print(f"        - Prompt tokens: {llm_call.get('prompt_tokens', 0)}")
                            print(f"        - Completion tokens: {llm_call.get('completion_tokens', 0)}")
                            
                            # 检查是否有工具调用
                            if 'tool_calls' in llm_call:
                                tool_calls = llm_call.get('tool_calls', [])
                                print(f"        - 工具调用数: {len(tool_calls)}")
                                for tc in tool_calls[:3]:  # 只显示前 3 个
                                    if isinstance(tc, dict):
                                        print(f"          • {tc.get('function', {}).get('name', 'unknown')}")
                    
                    # subagent.check_status
                    if 'subagent.check_status' in results:
                        status = results['subagent.check_status']
                        if isinstance(status, dict):
                            print(f"     📊 SubAgent 状态: {status.get('status', 'unknown')}")
                    
                except Exception as e:
                    print(f"     ⚠️  解析 step_results 失败: {e}")
            
            if round_saga['error']:
                print(f"     ❌ 错误: {round_saga['error'][:150]}")
            
            print()
    
    # 6. 检查异常情况
    print("\n[6] 异常情况检查")
    print("-" * 80)
    
    # 失败的 Saga
    cursor = conn.execute("""
        SELECT saga_type, COUNT(*) as cnt, GROUP_CONCAT(DISTINCT error) as errors
        FROM tq_sagas
        WHERE status = 'failed'
          AND created_at > datetime('now', '-1 hour')
        GROUP BY saga_type
    """)
    
    failed_sagas = cursor.fetchall()
    if failed_sagas:
        print("\n❌ 失败的 Saga (最近 1 小时):\n")
        for row in failed_sagas:
            print(f"  {row['saga_type']}: {row['cnt']} 次失败")
            if row['errors']:
                errors = row['errors'].split(',')
                for err in errors[:3]:
                    if err and err.strip():
                        print(f"    - {err[:100]}")
    else:
        print("\n✅ 最近 1 小时无失败的 Saga")
    
    # 长时间运行的 Saga
    cursor = conn.execute("""
        SELECT saga_type, id, 
               julianday(datetime('now')) - julianday(created_at) as running_days
        FROM tq_sagas
        WHERE status IN ('pending', 'running')
          AND julianday(datetime('now')) - julianday(created_at) > 0.00116  -- > 100 秒
        ORDER BY running_days DESC
    """)
    
    long_running = cursor.fetchall()
    if long_running:
        print("\n⚠️  长时间运行的 Saga (> 100s):\n")
        for row in long_running:
            running_sec = row['running_days'] * 86400
            print(f"  {row['saga_type']}: {row['id']} (运行了 {running_sec:.0f}s)")
    else:
        print("\n✅ 无长时间运行的 Saga")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)


if __name__ == "__main__":
    analyze_agent_loops()
