# Saga 定义目录

此目录包含所有 NovAIC 业务流程的 Saga 定义。

## 已注册的 Saga

系统会自动发现并注册此目录下的所有 Saga：

- `message_process` - 消息处理入口
- `runtime_start` - Runtime 启动流程
- `react_think` - ReAct Think 阶段
- `react_actions` - ReAct Actions 阶段
- `runtime_complete` - Runtime 完成流程
- `summarize` - 异步摘要生成

## 添加新 Saga

### 1. 创建 Saga 文件

在此目录创建新文件，例如 `my_saga.py`：

```python
"""
My Saga - 描述

流程：
1. 步骤 1
2. 步骤 2
"""

from ..saga import SagaDefinition
from . import register_saga_definition


def _build_step1_payload(ctx):
    """构建步骤 1 的 payload"""
    return {
        "key": ctx["value"],
    }


def _build_step2_payload(ctx, prev_result):
    """构建步骤 2 的 payload"""
    return {
        "result": prev_result.get("data"),
    }


# 定义 Saga
MY_SAGA = SagaDefinition("my_saga")

MY_SAGA.add_task_step(
    name="step1",
    topic="some.topic",
    build_payload=_build_step1_payload,
)

MY_SAGA.add_task_step(
    name="step2",
    topic="another.topic",
    build_payload=_build_step2_payload,
)

# 注册（必须！）
MY_SAGA = register_saga_definition(MY_SAGA)
```

### 2. 完成！

- ✅ 无需修改任何其他文件
- ✅ Worker 会自动发现新 Saga
- ✅ 启动时会打印注册信息

### 3. 验证注册

启动 Saga Worker 时会看到：

```
[Saga Registry] Registered 7 saga types:
  - my_saga: 2 steps
  - message_process: 4 steps
  ...
```

## Saga 定义 API

### 基本步骤类型

```python
# Task 步骤 - 发布一个 Task
saga.add_task_step(
    name="step_name",
    topic="topic.name",
    build_payload=lambda ctx: {"key": ctx["value"]},
    optional=False,  # 失败是否继续
    condition=None,  # 条件执行
)

# Parallel 步骤 - 并行发布多个 Task
saga.add_parallel_step(
    name="parallel_step",
    build_tasks=lambda ctx: [
        {"topic": "topic1", "payload": {}},
        {"topic": "topic2", "payload": {}},
    ],
)

# Decision 步骤 - 纯计算决策
saga.add_decision_step(
    name="decide",
    decide=lambda ctx, results: {"action": "next"},
)

# Saga 步骤 - 触发子 Saga
saga.add_saga_step(
    name="trigger_child",
    saga_type="child_saga",
    build_saga_context=lambda ctx: {"parent_id": ctx["id"]},
)
```

### Context 和 Results

- `ctx` - Saga 启动时的 context
- `prev_result` - 上一步的结果
- `results` - 所有步骤的结果字典

### 条件执行

```python
def _decide(ctx, results):
    return {"should_continue": results["check"]["status"] == "ok"}

saga.add_task_step(
    name="conditional_step",
    topic="some.topic",
    build_payload=lambda ctx: {},
    condition=lambda d: d.get("should_continue", False),
)
```

## 注意事项

### ✅ 必须做

1. **导入注册函数**：`from . import register_saga_definition`
2. **调用注册**：`MY_SAGA = register_saga_definition(MY_SAGA)`
3. **唯一的 Saga 名称**：确保 `SagaDefinition("name")` 中的名称唯一

### ❌ 不要做

1. **不要修改 `__init__.py` 的硬编码列表**（已移除）
2. **不要手动导入 Saga 模块**（自动导入）
3. **不要在 Saga 中执行副作用**（应该通过 Task 完成）

## 调试

### 查看已注册的 Saga

```python
from task_queue.sagas import get_all_saga_types, validate_saga_registration

# 验证并打印
validate_saga_registration()

# 获取类型列表
saga_types = get_all_saga_types()
```

### 检查导入错误

如果 Saga 没有被注册，检查：
1. 文件是否在 `task_queue/sagas/` 目录
2. 是否有语法错误（阻止导入）
3. 是否调用了 `register_saga_definition()`

## 相关文档

- [Saga 自动发现机制](../../../SAGA_AUTO_DISCOVERY.md) - 实现细节
- [Task Queue 架构](../../README.md) - 整体架构
- [Saga 设计](../../saga.py) - Saga 核心实现

## 历史

- **2026-02-05**: 实现自动发现机制，移除硬编码列表
- **2025-xx-xx**: 初始 Saga 系统实现
