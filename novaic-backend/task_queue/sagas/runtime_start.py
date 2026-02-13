"""
RuntimeStart Saga - Runtime 启动流程 (v3)

流程：
1. 初始化 Runtime（构建初始 context、system prompt）
2. 创建 MCP Server
3. 设置 SubAgent 为 awake
4. 触发 ReactThink Saga

v3 变更：
- Runtime 已在 message_process 的 route_message 中原子创建
- runtime.create 变为 runtime.init（初始化已有 runtime）
- 直接使用 ctx["runtime_id"]
"""

from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _build_runtime_init_payload(ctx):
    """构建 runtime.create payload（实际是初始化已有 runtime）
    
    runtime_id 已在 message_process 中创建，这里负责：
    1. 构建初始 context（历史摘要）
    2. 注入 system prompt
    3. 自动匹配技能
    """
    payload = {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "runtime_id": ctx["runtime_id"],  # 已创建的 runtime_id
        "trigger_type": ctx.get("trigger_type", "user_message"),
    }
    
    # Sub-subagent 需要 initial_context（包含任务描述）
    if "initial_context" in ctx and ctx["initial_context"]:
        payload["initial_context"] = ctx["initial_context"]
    
    return payload


def _build_mcp_create_payload(ctx):
    """构建 mcp.create payload
    
    runtime_id 从 ctx 获取（由 message_process 传入）
    """
    return {
        "runtime_id": ctx["runtime_id"],
        "agent_id": ctx["agent_id"],
    }


def _build_set_awake_payload(ctx):
    """构建 subagent.set_awake payload"""
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "runtime_id": ctx["runtime_id"],
    }


def _build_trigger_think_payload(ctx):
    """构建 saga.trigger payload - 触发 ReactThink"""
    runtime_id = ctx["runtime_id"]
    
    return {
        "saga_type": "react_think",
        "context": {
            "runtime_id": runtime_id,
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "round_num": 1,
            "model": ctx.get("model", "gpt-4o"),
            "tools": ctx.get("tools", []),
        },
        "idempotency_key": f"react-think-{runtime_id}-round1",
    }


# RuntimeStart Saga 定义 (v3)
RUNTIME_START_SAGA = SagaDefinition("runtime_start")

# Step 1: 初始化 Runtime（构建初始 context、system prompt）
# 注：Runtime 已在 message_process 中原子创建，这里负责初始化
RUNTIME_START_SAGA.add_task_step(
    name="init_runtime",
    topic=TaskTopics.RUNTIME_CREATE,  # 复用 handler，它会检测已有 runtime 并初始化
    build_payload=_build_runtime_init_payload,
)

# Step 2: 创建 MCP Server
RUNTIME_START_SAGA.add_task_step(
    name="create_mcp",
    topic=TaskTopics.MCP_CREATE,
    build_payload=_build_mcp_create_payload,
)

# Step 3: 设置 SubAgent 为 awake
RUNTIME_START_SAGA.add_task_step(
    name="set_subagent_awake",
    topic=TaskTopics.SUBAGENT_SET_AWAKE,
    build_payload=_build_set_awake_payload,
)

# Step 4: 触发 ReactThink Saga
RUNTIME_START_SAGA.add_task_step(
    name="trigger_think",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_think_payload,
)

# 自动注册
RUNTIME_START_SAGA = register_saga_definition(RUNTIME_START_SAGA)
