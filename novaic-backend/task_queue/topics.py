"""Task Queue Topic 名称常量

集中管理所有 Task 和 Saga 的 Topic 名称，避免硬编码字符串。

使用方式：
    from task_queue.topics import TaskTopics, SagaTopics
    
    @register_handler(TaskTopics.RUNTIME_CREATE)
    def handle_runtime_create(...):
        ...
"""


class TaskTopics:
    """Task 相关的 Topic 名称
    
    Task Topic 是具体的业务操作，由 Task Handler 处理。
    """
    
    # Runtime Tasks - Runtime 生命周期管理
    RUNTIME_CREATE = "runtime.create"
    # RUNTIME_UPDATE_PHASE = "runtime.update_phase"  # DEPRECATED: Saga 步骤替代 phase 状态
    RUNTIME_SET_STATUS = "runtime.set_status"
    RUNTIME_INCREMENT_ROUND = "runtime.increment_round"
    RUNTIME_SET_SUMMARIZED = "runtime.set_summarized"
    RUNTIME_SET_NEED_REST = "runtime.set_need_rest"
    RUNTIME_CHECK_NEW_MESSAGES = "runtime.check_new_messages"
    RUNTIME_GENERATE_SIMPLE_SUMMARY = "runtime.generate_simple_summary"
    
    # LLM Tasks - LLM 调用
    LLM_CALL = "llm.call"
    LLM_CALL_SUMMARY = "llm.call_summary"
    LLM_CALL_HOT_COLD_SUMMARY = "llm.call_hot_cold_summary"
    
    # MCP Tasks - MCP Server 管理
    MCP_CREATE = "mcp.create"
    MCP_DESTROY = "mcp.destroy"
    
    # Tool Tasks - 工具执行
    TOOL_EXECUTE = "tool.execute"
    
    # Context Tasks - Context 管理
    CONTEXT_READ = "context.read"
    CONTEXT_APPEND = "context.append"
    CONTEXT_GET = "context.get"
    
    # Message Tasks - 消息处理
    MESSAGE_PROCESS = "message.process"
    MESSAGE_CLAIM = "message.claim"
    MESSAGE_ROUTE = "message.route"
    
    # SubAgent Tasks - SubAgent 状态管理
    SUBAGENT_WAKE = "subagent.wake"
    SUBAGENT_SET_AWAKE = "subagent.set_awake"
    SUBAGENT_SET_SLEEPING = "subagent.set_sleeping"
    
    # Summary Tasks - 摘要和历史合并
    SUMMARY_MERGE_HISTORY = "summary.merge_history"
    SUMMARY_ADD_TO_HRL = "summary.add_to_hrl"
    SUMMARY_MERGE_HISTORY_IF_NEEDED = "summary.merge_history_if_needed"
    
    @classmethod
    def all(cls) -> list[str]:
        """返回所有 Task Topic"""
        return [
            v for k, v in vars(cls).items()
            if not k.startswith('_') and isinstance(v, str) and not callable(v)
        ]


class SagaTopics:
    """Saga 相关的 Topic 名称
    
    Saga Topic 用于触发新的 Saga 流程。
    """
    
    # Saga Trigger - 通用 Saga 触发器
    SAGA_TRIGGER = "saga.trigger"
    
    @classmethod
    def all(cls) -> list[str]:
        """返回所有 Saga Topic"""
        return [
            v for k, v in vars(cls).items()
            if not k.startswith('_') and isinstance(v, str) and not callable(v)
        ]


def get_all_topics() -> list[str]:
    """获取所有 Topic（Task + Saga）"""
    return TaskTopics.all() + SagaTopics.all()


def validate_topics(registered_topics: set[str]) -> dict[str, list[str]]:
    """验证 Topic 注册一致性
    
    Args:
        registered_topics: 实际注册的 topic 集合
        
    Returns:
        dict with keys:
        - missing_in_constants: 已注册但未定义常量的 topics
        - unused_constants: 已定义常量但未注册的 topics
    """
    constant_topics = set(get_all_topics())
    
    missing_in_constants = registered_topics - constant_topics
    unused_constants = constant_topics - registered_topics
    
    return {
        "missing_in_constants": sorted(missing_in_constants),
        "unused_constants": sorted(unused_constants),
    }
