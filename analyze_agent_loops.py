#!/usr/bin/env python3
"""
分析 Agent Loop 的详细执行情况
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".novaic" / "novaic.db"


def analyze_agent_loops():
    """分析 Agent Loop 的执行情况"""
    conn = sqlite3.connect(str(DB_PATH))
    
    print("="*80)
    print("🔍 Agent Loop 详细分析")
    print("="*80)
    
    # 1. 获取所有 react_think saga
    cursor = conn.execute("""
        SELECT 
            id,
            status,
            current_step,
            created_at,
            completed_at,
            step_results,
            context
        FROM tq_sagas
        WHERE saga_type = 'react_think'
          AND json_extract(context, '$.agent_id') LIKE 'df579f32%'
        ORDER BY created_at
    """)
    
    think_sagas = cursor.fetchall()
    
    print(f"\n📊 总共有 {len(think_sagas)} 个 react_think saga (Agent Loop Rounds)\n")
    
    for idx, saga in enumerate(think_sagas, 1):
        saga_id, status, current_step, created_at, completed_at, step_results_json, context_json = saga
        
        print(f"\n{'='*80}")
        print(f"🔄 Agent Loop Round #{idx}")
        print(f"{'='*80}")
        print(f"Saga ID: {saga_id}")
        print(f"状态: {status}")
        print(f"创建时间: {created_at}")
        print(f"完成时间: {completed_at}")
        
        # 解析 step_results
        step_results = json.loads(step_results_json) if step_results_json else {}
        
        # 解析 context
        context = json.loads(context_json) if context_json else {}
        runtime_id = context.get('runtime_id', 'N/A')
        
        print(f"Runtime ID: {runtime_id}")
        print(f"\n步骤执行情况:")
        
        # Step 1: context.read
        if '0' in step_results:
            step0 = step_results['0']
            if step0.get('success'):
                result = step0.get('result', {})
                new_messages = result.get('new_messages', [])
                context_length = result.get('length', 0)
                
                print(f"\n  📖 Step 1: context.read")
                print(f"     ✓ 读取新消息: {len(new_messages)} 条")
                print(f"     ✓ Context 总长度: {context_length}")
                
                if new_messages:
                    print(f"     ✓ 新消息 ID: {', '.join([m.get('message_id', '')[:12] for m in new_messages[:5]])}...")
        
        # Step 2: llm.call
        if '1' in step_results:
            step1 = step_results['1']
            if step1.get('success'):
                result = step1.get('result', {})
                response = result.get('response', {})
                usage = response.get('usage', {})
                
                print(f"\n  🤖 Step 2: llm.call")
                print(f"     ✓ 模型: {response.get('model', 'N/A')}")
                print(f"     ✓ Tokens: input={usage.get('prompt_tokens', 0)}, output={usage.get('completion_tokens', 0)}")
                
                # 查看回复内容
                choices = response.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content', '')
                    tool_calls = message.get('tool_calls', [])
                    
                    if content:
                        print(f"     ✓ 回复内容: {content[:100]}...")
                    
                    if tool_calls:
                        print(f"     ✓ Tool 调用: {len(tool_calls)} 个")
                        for tc in tool_calls:
                            func = tc.get('function', {})
                            print(f"       - {func.get('name', 'N/A')}")
        
        # Step 3: message.send (如果有 AI 回复)
        if '2' in step_results:
            step2 = step_results['2']
            if step2.get('success'):
                result = step2.get('result', {})
                print(f"\n  💬 Step 3: message.send")
                print(f"     ✓ 消息已发送: {result.get('message_id', 'N/A')[:12]}")
        
        # Step 4: tools.execute (如果有工具调用)
        if '3' in step_results:
            step3 = step_results['3']
            if step3.get('success'):
                result = step3.get('result', {})
                print(f"\n  🔧 Step 4: tools.execute")
                print(f"     ✓ 工具执行完成")
    
    # 2. 统计 AI 回复数
    print(f"\n\n{'='*80}")
    print("💬 AI 回复统计")
    print("="*80)
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM chat_messages
        WHERE type = 'AGENT_REPLY' AND agent_id LIKE 'df579f32%'
    """)
    ai_reply_count = cursor.fetchone()[0]
    
    print(f"AI 回复总数: {ai_reply_count} 条")
    
    # 3. 查看所有 AI 回复内容
    cursor = conn.execute("""
        SELECT content, created_at FROM chat_messages
        WHERE type = 'AGENT_REPLY' AND agent_id LIKE 'df579f32%'
        ORDER BY created_at
    """)
    
    ai_replies = cursor.fetchall()
    
    for idx, (content, created_at) in enumerate(ai_replies, 1):
        print(f"\n回复 #{idx} ({created_at}):")
        print(f"{content[:200]}...")
    
    # 4. 统计 LLM 调用次数
    print(f"\n\n{'='*80}")
    print("🤖 LLM 调用统计")
    print("="*80)
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM tq_tasks
        WHERE topic = 'llm.call'
          AND json_extract(payload, '$.runtime_id') IN (
              SELECT runtime_id FROM agent_runtimes WHERE agent_id LIKE 'df579f32%'
          )
          AND status = 'completed'
    """)
    llm_call_count = cursor.fetchone()[0]
    
    print(f"LLM 调用次数: {llm_call_count} 次")
    
    # 5. 统计 react_actions
    print(f"\n\n{'='*80}")
    print("⚡ react_actions 统计")
    print("="*80)
    
    cursor = conn.execute("""
        SELECT COUNT(*) FROM tq_sagas
        WHERE saga_type = 'react_actions'
          AND json_extract(context, '$.agent_id') LIKE 'df579f32%'
    """)
    actions_count = cursor.fetchone()[0]
    
    print(f"react_actions 执行次数: {actions_count} 次")
    
    conn.close()
    
    # 6. 总结
    print(f"\n\n{'='*80}")
    print("📈 总结")
    print("="*80)
    print(f"Agent Loop Rounds (react_think): {len(think_sagas)}")
    print(f"LLM 调用次数: {llm_call_count}")
    print(f"AI 回复数: {ai_reply_count}")
    print(f"react_actions 执行: {actions_count}")
    print("="*80)


if __name__ == "__main__":
    analyze_agent_loops()
