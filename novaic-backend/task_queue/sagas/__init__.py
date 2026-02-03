"""
Saga Definitions - 业务流程编排 (v2)

定义 NovAIC 的核心业务流程 Saga:
- MessageProcessSaga: 消息处理入口 (v2 新增)
- RuntimeStartSaga: Runtime 启动流程
- ReactThinkSaga: ReAct Think 阶段
- ReactActionsSaga: ReAct Actions 阶段
- RuntimeCompleteSaga: Runtime 完成流程
- SummarizeSaga: 异步摘要生成 (v2 新增)
"""

from ..saga import SagaDefinition

# 导入所有 Saga 定义
from .message_process import MESSAGE_PROCESS_SAGA
from .runtime_start import RUNTIME_START_SAGA
from .react_think import REACT_THINK_SAGA
from .react_actions import REACT_ACTIONS_SAGA
from .runtime_complete import RUNTIME_COMPLETE_SAGA
from .summarize import SUMMARIZE_SAGA


def get_all_saga_definitions() -> list:
    """获取所有 Saga 定义"""
    return [
        MESSAGE_PROCESS_SAGA,
        RUNTIME_START_SAGA,
        REACT_THINK_SAGA,
        REACT_ACTIONS_SAGA,
        RUNTIME_COMPLETE_SAGA,
        SUMMARIZE_SAGA,
    ]


def register_all_sagas(saga_worker):
    """向 SagaWorker 注册所有 Saga"""
    for saga_def in get_all_saga_definitions():
        saga_worker.register(saga_def)
