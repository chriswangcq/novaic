# PR-133: Remove common `notebook_*` and `task_*` tool residues

## 背景

common 里的 `notebook_*` / `task_*` 是旧业务工具元数据。当前 Cortex 最小结构不应该包含自动记忆、业务任务系统、任务板等路径；这些工具没有 Runtime executor，继续留在 common 会造成工具目录熵增和维护误导。

## Scope

- 从 `common.tools.definitions` 物理删除 `NOTEBOOK_TOOLS` / `QUADRANT_TASK_TOOLS` 定义。
- 从 `BUILTIN_TOOLS` 删除 `notebook` / `quadrant_task` 分类。
- 清理相关 backward compatibility alias 或旧注释。
- 增加 guardrail：common active tool names 不包含 `notebook_*` / `task_*`。

## 非目标

- 不删除 Business 里尚作为内部 API/历史数据存在的 notebook/task 路由。
- 不改变 Queue Service 自身的任务队列概念。

## 单元测试

- Common：`BUILTIN_TOOLS` 不包含 `notebook` / `quadrant_task` 分类，active names 不包含 `notebook_*` / `task_*`。
- Business：工具配置接口仍能返回剩余工具分类。

## 冒烟测试

- Business `/internal/agents/{agent_id}/builtin-tools` 不再返回 notebook/task 工具。
- LLM request tools 仍只有 Runtime 真能执行的工具。

## 部署 Checklist

- Common / Business 测试通过。
- 部署 Common、Business。
- 线上确认工具配置面不再出现 notebook/task。

## GitHub / Merge

- 可单独 merge。
- Commit message: `refactor(tools): remove notebook and task residues`

