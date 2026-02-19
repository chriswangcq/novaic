# Internal API 模块说明（当前状态）

## 概述

Internal API 已按职责拆分并完成 Gateway/Runtime Orchestrator 分家：

**边界约定：**
- **Runtime Orchestrator (RO)** 仅暴露 `/internal/runtimes*` 域（运行时编排）
- **Gateway** 持有业务域内部接口：messages、subagents、vm、task、agent、config、llm、web 等
- **Gateway 业务 API**：已迁移接口采用 `subagent_id` 作为主输入，不再依赖 `runtime_id`

## 文件结构

```
internal/
├── __init__.py          # 统一导出 router
├── runtime_orchestrator.py  # Runtime Orchestrator 专用 router（仅 agent-layer）
├── helpers.py           # 工具函数（resolve_runtime_ids, get_runtime_context, _runtime_to_dict, _subagent_to_dict）
├── subagent.py          # SubAgent 操作（包含 HRL）
├── message.py           # Message 操作
├── agent.py             # Agent 操作
├── config.py            # Config 操作
├── task.py              # 四象限任务 API
├── llm.py               # LLM 操作
├── web.py               # Web API
├── vm.py                # VM/SSH/QEMU/VM Tools
├── health.py            # Health Monitor
└── broadcast.py         # SSE Broadcast
```

**Note**: `/internal/runtimes*` 由 RO 独占；Gateway 不挂载 runtime 路由。self_drive API 已移除。

## 使用方式

**Gateway 进程**：挂载业务域 internal APIs（messages/subagents/vm/task 等）：

```python
from gateway.api.internal import router as internal_router
app.include_router(internal_router)
```

**Runtime Orchestrator 进程**：仅挂载 `/internal/runtimes*` 路由：

```python
from runtime_orchestrator.api.internal import router as internal_runtime_router
app.include_router(internal_runtime_router)
```

## 拆分详情

| 文件 | 主要功能 | 路由数 |
|------|---------|--------|
| `subagent.py` | SubAgent CRUD、状态管理、HRL | ~17 |
| `message.py` | 消息查询、标记、创建 | ~9 |
| `config.py` | Agent/LLM 配置 | ~5 |
| `task.py` | 四象限任务 API | ~10 |
| `web.py` | Web 搜索和抓取 | ~2 |
| `vm.py` | VM/SSH/QEMU/VM Tools | ~5 |
| `agent.py` | Agent 状态管理 | ~3 |
| `llm.py` | LLM 上下文压缩 | ~1 |
| `health.py` | 健康监控 | ~3 |
| `broadcast.py` | SSE 广播 | ~2 |
| `helpers.py` | 工具函数（无路由） | 0 |

## 注意事项

1. **helpers.py** 不包含 router，只提供工具函数
2. 其他文件都从 `helpers.py` 导入共享函数
3. 所有文件都使用 `prefix="/internal"`，并按职责分组 tags
4. Gateway 使用 `__init__.py` 聚合业务域路由；RO 仅挂载 `/internal/runtimes*`，显式声明路由边界
5. `runtime.py` 与 `self_drive.py` 已移除；`/internal/runtimes*` 由 RO 独占；self-drive API 已删除
