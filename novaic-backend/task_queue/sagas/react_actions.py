"""
ReactActions Saga - ReAct Actions 阶段 (v3)

流程：
1. 并行执行所有 tool_calls（done/reset 会设置 need_rest=1）
2. 并行保存所有 tool results 到 context
3. 检查是否有新消息 + need_rest 状态
4. 决策：
   - 无新消息 且 need_rest=1 → RuntimeComplete
   - 其他情况 → ReactThink（继续循环）

v3 变更：
- 删除 set_phase_waiting_actions 步骤（Saga 步骤即进度，不需要额外 phase 状态）
"""

from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _build_tool_execute_tasks(ctx):
    """构建并行 tool.execute 任务"""
    tool_calls = ctx.get("tool_calls", [])
    runtime_id = ctx["runtime_id"]
    round_num = ctx.get("round_num", 1)
    agent_id = ctx.get("agent_id")
    subagent_id = ctx.get("subagent_id", "main")  # ✅ 新增：从 context 获取
    
    return [
        {
            "topic": TaskTopics.TOOL_EXECUTE,
            "payload": {
                "runtime_id": runtime_id,
                "agent_id": agent_id,
                "subagent_id": subagent_id,  # ✅ 新增：传递给 payload
                "round_id": f"round-{round_num}",
                "tool_call_id": tc.get("id"),
                "tool_name": tc.get("function", {}).get("name"),
                "arguments": tc.get("function", {}).get("arguments", "{}"),
            },
        }
        for tc in tool_calls
    ]


def _build_save_results_tasks(ctx, prev_results):
    """构建并行 context.append 任务
    
    注意：必须保存所有 tool results（包括失败的），因为 LLM API 要求
    每个 tool_call 都必须有对应的 tool result。
    
    prev_results 格式（并行步骤返回）：
    - {"success": bool, "results": [...], ...}
    """
    import json
    runtime_id = ctx["runtime_id"]
    round_num = ctx.get("round_num", 1)
    
    # 从并行步骤结果中提取 results 列表
    if isinstance(prev_results, dict):
        results_list = prev_results.get("results", [])
    else:
        # 兼容旧格式（直接是 list）
        results_list = prev_results if isinstance(prev_results, list) else []
    
    tasks = []
    for i, result in enumerate(results_list):
        tool_call_id = result.get("tool_call_id") or f"tool-{i}"
        
        # 构建 content（成功或失败都要保存）
        if result.get("success"):
            # 成功：保存 result 字段
            tool_result = result.get("result", "")
        else:
            # 失败：保存错误信息
            error_msg = result.get("error", "Tool execution failed")
            tool_result = {"error": error_msg, "success": False}
        
        # 正确序列化 result：使用 json.dumps 而不是 str()
        if isinstance(tool_result, (dict, list)):
            content = json.dumps(tool_result, ensure_ascii=False)
        else:
            content = str(tool_result)
        
        tasks.append({
            "topic": TaskTopics.CONTEXT_APPEND,
            "payload": {
                "runtime_id": runtime_id,
                "message": {
                    "role": "tool",
                    "tool_call_id": result.get("tool_call_id"),
                    "content": content,
                },
                "message_type": "tool_result",
                "round_id": f"round-{round_num}",
                "idempotency_key": f"{runtime_id}-round{round_num}-{tool_call_id}",
            },
        })
    
    return tasks


def _build_check_continue_payload(ctx):
    """检查是否继续"""
    return {
        "runtime_id": ctx["runtime_id"],
        "agent_id": ctx["agent_id"],
    }


def _decide_continue(ctx, results):
    """决策是否继续
    
    判断逻辑 (v2):
    - 检查 check_continue 结果：has_new_messages, need_rest
    - 无新消息 且 need_rest=1 → RuntimeComplete
    - 其他情况 → ReactThink（继续循环）
    """
    check_result = results.get("check_continue", {})
    has_new_messages = check_result.get("has_new_messages", False)
    need_rest = check_result.get("need_rest", False)
    
    # 无新消息 且 need_rest=1 → 完成
    should_complete = not has_new_messages and need_rest
    
    return {
        "should_complete": should_complete,
        "has_new_messages": has_new_messages,
        "need_rest": need_rest,
        "runtime_id": ctx["runtime_id"],
    }


def _build_trigger_next_think_payload(ctx, decision):
    """构建 saga.trigger payload - 触发下一轮 ReactThink"""
    next_round = ctx.get("round_num", 1) + 1
    return {
        "saga_type": "react_think",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "round_num": next_round,
            "model": ctx.get("model", "gpt-4o"),
            "tools": ctx.get("tools", []),
        },
        "idempotency_key": f"react-think-{ctx['runtime_id']}-round{next_round}",
    }


def _build_trigger_complete_payload(ctx, decision):
    """构建 saga.trigger payload - 触发 RuntimeComplete"""
    return {
        "saga_type": "runtime_complete",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
        },
        "idempotency_key": f"runtime-complete-{ctx['runtime_id']}",
    }


# ReactActions Saga 定义 (v3)
REACT_ACTIONS_SAGA = SagaDefinition("react_actions")

# Step 1: 并行执行 tool_calls
REACT_ACTIONS_SAGA.add_parallel_step(
    name="execute_tools",
    build_tasks=_build_tool_execute_tasks,
)

# Step 2: 并行保存结果
REACT_ACTIONS_SAGA.add_parallel_step(
    name="save_results",
    build_tasks=_build_save_results_tasks,
)

# Step 3: 检查是否继续（查询新消息 + runtime status）
REACT_ACTIONS_SAGA.add_task_step(
    name="check_continue",
    topic=TaskTopics.RUNTIME_CHECK_NEW_MESSAGES,
    build_payload=_build_check_continue_payload,
)

# Step 4: 决策
REACT_ACTIONS_SAGA.add_decision_step(
    name="decide_continue",
    decide=_decide_continue,
)

# Step 5a: 继续下一轮 Think
REACT_ACTIONS_SAGA.add_task_step(
    name="trigger_next_think",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_next_think_payload,
    condition=lambda d: not d.get("should_complete", False),
)

# Step 5b: 结束 Runtime
REACT_ACTIONS_SAGA.add_task_step(
    name="trigger_complete",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_complete_payload,
    condition=lambda d: d.get("should_complete", False),
)

# 自动注册
REACT_ACTIONS_SAGA = register_saga_definition(REACT_ACTIONS_SAGA)
