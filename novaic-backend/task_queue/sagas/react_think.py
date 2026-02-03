"""
ReactThink Saga - ReAct Think 阶段 (v2)

流程：
1. 从 DB 读取最新 context（过滤 sending 消息）
2. 调用 LLM
3. 保存 LLM 响应到 context
4. 触发 ReactActions（无论有没有 tool_calls）

v2 变更：
- 无 tool_calls 时，添加 chat_reply + runtime_rest action
- done/final 等工具名统一转换为 runtime_rest
"""

from ..saga import SagaDefinition


# 需要转换为 runtime_rest 的工具名
REST_TOOL_ALIASES = {"done", "final", "finish", "complete", "rest", "runtime_reset"}


def _build_read_context_payload(ctx):
    """Step 1: 从 DB 读取最新 context"""
    return {
        "runtime_id": ctx["runtime_id"],
        "filter_sending": True,
    }


def _build_llm_call_payload(ctx, prev_result):
    """Step 2: 调用 LLM（使用 Step 1 的结果）"""
    # prev_result 是 context.read 的结果
    context = prev_result.get("context", [])
    
    return {
        "runtime_id": ctx["runtime_id"],
        "round_id": f"round-{ctx.get('round_num', 1)}",
        "messages": context,  # 从 DB 读取的最新 context
        "model": ctx.get("model", "gpt-4o"),
        "tools": ctx.get("tools", []),
        "agent_id": ctx.get("agent_id"),
    }


def _build_save_response_payload(ctx, prev_result):
    """Step 3: 保存 LLM 响应"""
    response = prev_result.get("response", {})
    message = response.get("choices", [{}])[0].get("message", {})
    
    return {
        "runtime_id": ctx["runtime_id"],
        "message": message,
        "message_type": "llm_response",
        "round_id": f"round-{ctx.get('round_num', 1)}",
        "idempotency_key": f"{ctx['runtime_id']}-round{ctx.get('round_num', 1)}-response",
    }


def _normalize_tool_calls(tool_calls, runtime_id, round_num):
    """
    标准化 tool_calls：将 done/final 等转换为 runtime_rest
    
    这样 MCP 层只需要实现一个 runtime_rest 工具来设置 need_rest=1
    """
    normalized = []
    for tc in tool_calls:
        func = tc.get("function", {})
        tool_name = func.get("name", "")
        
        # 转换为 runtime_rest
        if tool_name in REST_TOOL_ALIASES:
            normalized.append({
                "id": tc.get("id", f"rest-{runtime_id}-round{round_num}"),
                "type": "function",
                "function": {
                    "name": "runtime_rest",
                    "arguments": func.get("arguments", '{"reason": "Task completed"}'),
                },
            })
        else:
            normalized.append(tc)
    
    return normalized


def _decide_and_build_actions(ctx, results):
    """决策并构建 ReactActions payload"""
    import json
    
    call_llm_result = results.get("call_llm", {})
    response = call_llm_result.get("response", {})
    message = response.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls", [])
    content = message.get("content", "")
    
    runtime_id = ctx["runtime_id"]
    agent_id = ctx.get("agent_id", "")
    round_num = ctx.get("round_num", 1)
    
    # 无 tool_calls 时，添加 chat_reply + runtime_rest
    if not tool_calls:
        tool_calls = []
        
        # 1. 如果有文本内容，添加 chat_reply action
        if content:
            tool_calls.append({
                "id": f"reply-{runtime_id}-round{round_num}",
                "type": "function",
                "function": {
                    "name": "chat_reply",
                    "arguments": json.dumps({
                        "message": content,  # chat_reply 的参数是 message 不是 content
                    }),
                },
            })
        
        # 2. 添加 runtime_rest action（设置 need_rest=1）
        tool_calls.append({
            "id": f"rest-{runtime_id}-round{round_num}",
            "type": "function",
            "function": {
                "name": "runtime_rest",
                "arguments": json.dumps({"reason": "Task completed"}),
            },
        })
    else:
        # 标准化 tool_calls（转换 done/final 等为 runtime_rest）
        tool_calls = _normalize_tool_calls(tool_calls, runtime_id, round_num)
    
    return {
        "tool_calls": tool_calls,
        "runtime_id": runtime_id,
    }


def _build_trigger_actions_from_decision(ctx, decision):
    """根据 decision 构建 ReactActions trigger"""
    return {
        "saga_type": "react_actions",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "round_num": ctx.get("round_num", 1),
            "tool_calls": decision.get("tool_calls", []),
            "model": ctx.get("model", "gpt-4o"),
            "tools": ctx.get("tools", []),
        },
        "idempotency_key": f"react-actions-{ctx['runtime_id']}-round{ctx.get('round_num', 1)}",
    }


# ReactThink Saga 定义 (v2)
REACT_THINK_SAGA = SagaDefinition("react_think")

# Step 1: 从 DB 读取最新 context
REACT_THINK_SAGA.add_task_step(
    name="read_context",
    topic="context.read",
    build_payload=_build_read_context_payload,
)

# Step 2: 调用 LLM（使用 read_context 的结果）
REACT_THINK_SAGA.add_task_step(
    name="call_llm",
    topic="llm.call",
    build_payload=_build_llm_call_payload,
)

# Step 3: 保存 LLM 响应
REACT_THINK_SAGA.add_task_step(
    name="save_response",
    topic="context.append",
    build_payload=_build_save_response_payload,
)

# Step 4: 决策（提取 tool_calls，无则添加 done）
REACT_THINK_SAGA.add_decision_step(
    name="decide_actions",
    decide=_decide_and_build_actions,
)

# Step 5: 触发 ReactActions（总是执行）
REACT_THINK_SAGA.add_task_step(
    name="trigger_actions",
    topic="saga.trigger",
    build_payload=_build_trigger_actions_from_decision,
)
