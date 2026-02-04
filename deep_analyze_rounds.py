#!/usr/bin/env python3
"""
深入分析每个 Agent Loop Round
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path.home() / ".novaic" / "novaic.db"


def analyze_rounds():
    """深入分析每个 Round"""
    conn = sqlite3.connect(str(DB_PATH))
    
    print("="*90)
    print("🔍 Agent Loop Round 深度分析")
    print("="*90)
    
    # 1. 获取所有 llm.call 任务
    cursor = conn.execute("""
        SELECT 
            id,
            status,
            created_at,
            started_at,
            finished_at,
            payload,
            result
        FROM tq_tasks
        WHERE topic = 'llm.call'
        ORDER BY created_at
    """)
    
    llm_tasks = cursor.fetchall()
    
    print(f"\n📊 总共 {len(llm_tasks)} 次 LLM 调用\n")
    
    for idx, task in enumerate(llm_tasks, 1):
        task_id, status, created_at, started_at, finished_at, payload_json, result_json = task
        
        print(f"\n{'='*90}")
        print(f"🤖 LLM 调用 #{idx} (Agent Loop Round #{idx})")
        print(f"{'='*90}")
        
        payload = json.loads(payload_json) if payload_json else {}
        result = json.loads(result_json) if result_json else {}
        
        # 任务信息
        print(f"\n任务信息:")
        print(f"  ID: {task_id}")
        print(f"  状态: {status}")
        print(f"  创建时间: {created_at}")
        print(f"  开始时间: {started_at}")
        print(f"  结束时间: {finished_at}")
        
        # 计算耗时
        if started_at and finished_at:
            from datetime import datetime
            start = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
            duration = (end - start).total_seconds()
            print(f"  耗时: {duration:.2f}秒")
        
        # Payload 信息
        runtime_id = payload.get('runtime_id', 'N/A')
        round_id = payload.get('round_id', 'N/A')
        messages = payload.get('messages', [])
        
        print(f"\n请求信息:")
        print(f"  Runtime ID: {runtime_id}")
        print(f"  Round ID: {round_id}")
        print(f"  上下文消息数: {len(messages)}")
        
        # 统计消息类型
        user_msgs = [m for m in messages if m.get('role') == 'user']
        assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
        tool_msgs = [m for m in messages if m.get('role') == 'tool']
        system_msgs = [m for m in messages if m.get('role') == 'system']
        
        print(f"    - system 消息: {len(system_msgs)}")
        print(f"    - user 消息: {len(user_msgs)}")
        print(f"    - assistant 消息: {len(assistant_msgs)}")
        print(f"    - tool 消息: {len(tool_msgs)}")
        
        # 查看最后几条 user 消息
        if user_msgs:
            print(f"\n  最近的用户消息:")
            for i, msg in enumerate(user_msgs[-5:], 1):
                content = msg.get('content', '')[:80]
                print(f"    {i}. {content}...")
        
        # Result 信息
        if result.get('success'):
            response = result.get('response', {})
            choices = response.get('choices', [])
            usage = response.get('usage', {})
            
            print(f"\n响应信息:")
            print(f"  模型: {response.get('model', 'N/A')}")
            print(f"  Token 使用:")
            print(f"    - Prompt tokens: {usage.get('prompt_tokens', 0):,}")
            print(f"    - Completion tokens: {usage.get('completion_tokens', 0):,}")
            print(f"    - Total tokens: {usage.get('total_tokens', 0):,}")
            
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')
                tool_calls = message.get('tool_calls', [])
                
                print(f"\n  AI 回复:")
                if reasoning:
                    print(f"    思考过程: {reasoning[:150]}...")
                if content:
                    print(f"    回复内容: {content[:150]}...")
                if tool_calls:
                    print(f"    Tool 调用: {len(tool_calls)} 个")
                    for tc in tool_calls:
                        func = tc.get('function', {})
                        print(f"      - {func.get('name', 'N/A')}")
        
        # 查询这个 Round 读取了多少新消息
        cursor_read = conn.execute("""
            SELECT result
            FROM tq_tasks
            WHERE topic = 'context.read'
              AND json_extract(payload, '$.runtime_id') = ?
              AND created_at < ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (runtime_id, created_at))
        
        read_result = cursor_read.fetchone()
        if read_result and read_result[0]:
            read_data = json.loads(read_result[0])
            new_messages = read_data.get('new_messages', [])
            print(f"\n  📖 context.read:")
            print(f"    本轮读取新消息: {len(new_messages)} 条")
    
    # 2. 查看 react_actions
    print(f"\n\n{'='*90}")
    print("⚡ react_actions 分析")
    print("="*90)
    
    cursor = conn.execute("""
        SELECT 
            id,
            status,
            created_at,
            step_results,
            context
        FROM tq_sagas
        WHERE saga_type = 'react_actions'
          AND json_extract(context, '$.agent_id') LIKE 'df579f32%'
        ORDER BY created_at
    """)
    
    actions_sagas = cursor.fetchall()
    
    print(f"\n总共 {len(actions_sagas)} 个 react_actions saga")
    
    for idx, saga in enumerate(actions_sagas, 1):
        saga_id, status, created_at, step_results_json, context_json = saga
        
        context = json.loads(context_json) if context_json else {}
        tool_calls = context.get('tool_calls', [])
        
        print(f"\n  react_actions #{idx}:")
        print(f"    Saga ID: {saga_id}")
        print(f"    状态: {status}")
        print(f"    Tool 调用数: {len(tool_calls)}")
        
        for tc in tool_calls[:5]:  # 只显示前5个
            func = tc.get('function', {})
            print(f"      - {func.get('name', 'N/A')}")
    
    # 3. 总结
    print(f"\n\n{'='*90}")
    print("📈 完整流程总结")
    print("="*90)
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM chat_messages
        WHERE type = 'USER_MESSAGE' AND agent_id LIKE 'df579f32%'
    """)
    user_msg_count = cursor.fetchone()[0]
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM chat_messages
        WHERE type = 'AGENT_REPLY' AND agent_id LIKE 'df579f32%'
    """)
    ai_reply_count = cursor.fetchone()[0]
    
    print(f"\n消息统计:")
    print(f"  用户消息: {user_msg_count} 条")
    print(f"  AI 回复: {ai_reply_count} 条")
    
    print(f"\n执行统计:")
    print(f"  Agent Loop Rounds: {len(llm_tasks)} 轮")
    print(f"  LLM 调用: {len(llm_tasks)} 次")
    print(f"  react_actions: {len(actions_sagas)} 次")
    
    print(f"\n效率分析:")
    if user_msg_count > 0 and len(llm_tasks) > 0:
        avg_msgs_per_round = user_msg_count / len(llm_tasks)
        print(f"  平均每轮处理消息数: {avg_msgs_per_round:.1f} 条")
        print(f"  批处理效率: {(1 - len(llm_tasks)/user_msg_count)*100:.1f}%")
    
    conn.close()
    
    print("="*90)


if __name__ == "__main__":
    analyze_rounds()
