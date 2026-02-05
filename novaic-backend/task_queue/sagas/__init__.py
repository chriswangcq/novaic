"""
Saga Definitions - 业务流程编排 (v2)

定义 NovAIC 的核心业务流程 Saga:
- MessageProcessSaga: 消息处理入口 (v2 新增)
- RuntimeStartSaga: Runtime 启动流程
- ReactThinkSaga: ReAct Think 阶段
- ReactActionsSaga: ReAct Actions 阶段
- RuntimeCompleteSaga: Runtime 完成流程
- SummarizeSaga: 异步摘要生成 (v2 新增)

自动注册机制：
- 使用 register_saga_definition() 注册 Saga
- 自动导入所有 Saga 模块以触发注册
- 无需手动维护 Saga 列表
"""

from typing import Dict, List
from ..saga import SagaDefinition

# Saga 注册表
_SAGA_REGISTRY: Dict[str, SagaDefinition] = {}


def register_saga_definition(definition: SagaDefinition) -> SagaDefinition:
    """注册 Saga 定义
    
    用法:
        RUNTIME_COMPLETE_SAGA = register_saga_definition(
            SagaDefinition("runtime_complete")
        )
    """
    _SAGA_REGISTRY[definition.name] = definition
    return definition


def get_all_saga_definitions() -> List[SagaDefinition]:
    """获取所有已注册的 Saga 定义"""
    return list(_SAGA_REGISTRY.values())


def get_all_saga_types() -> List[str]:
    """获取所有已注册的 Saga 类型"""
    return list(_SAGA_REGISTRY.keys())


def get_saga_definition(saga_type: str) -> SagaDefinition:
    """根据类型获取 Saga 定义"""
    if saga_type not in _SAGA_REGISTRY:
        raise ValueError(f"Unknown saga type: {saga_type}")
    return _SAGA_REGISTRY[saga_type]


def validate_saga_registration():
    """验证所有 Saga 都已正确注册"""
    if not _SAGA_REGISTRY:
        raise RuntimeError("No Sagas registered! Check imports.")
    
    print(f"[Saga Registry] Registered {len(_SAGA_REGISTRY)} saga types:")
    for saga_type in sorted(_SAGA_REGISTRY.keys()):
        definition = _SAGA_REGISTRY[saga_type]
        print(f"  - {saga_type}: {len(definition.steps)} steps")
    
    return True


def register_all_sagas(saga_worker):
    """向 SagaWorker 注册所有 Saga"""
    for saga_def in get_all_saga_definitions():
        saga_worker.register(saga_def)


# 自动导入所有 Saga 模块以触发注册
import importlib
import pkgutil
from pathlib import Path

_saga_dir = Path(__file__).parent
for module_info in pkgutil.iter_modules([str(_saga_dir)]):
    if module_info.name not in ['__init__']:
        try:
            importlib.import_module(f'task_queue.sagas.{module_info.name}')
        except Exception as e:
            print(f"[Saga Registry] Warning: Failed to import {module_info.name}: {e}")
