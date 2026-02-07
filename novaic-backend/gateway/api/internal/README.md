# Internal API 模块拆分

## 概述

`internal.py` 文件（3047行）已按功能模块拆分为多个文件，便于维护和管理。

## 文件结构

```
internal/
├── __init__.py          # 统一导出 router
├── helpers.py           # 工具函数（resolve_runtime_ids, get_runtime_context, _runtime_to_dict, _subagent_to_dict）
├── runtime.py           # Runtime 操作（包含 Runtime-First API）
├── subagent.py          # SubAgent 操作（包含 HRL）
├── message.py           # Message 操作
├── agent.py             # Agent 操作
├── config.py            # Config 操作
├── task.py              # TaskManager API
├── llm.py               # LLM 操作
├── web.py               # Web API
├── vm.py                # VM/SSH/QEMU/VM Tools
├── health.py            # Health Monitor
└── broadcast.py         # SSE Broadcast
```

## 使用方式

导入方式保持不变：

```python
from gateway.api.internal import router as internal_router
app.include_router(internal_router)
```

所有路由路径保持不变，向后兼容。

## 拆分详情

| 文件 | 主要功能 | 路由数 |
|------|---------|--------|
| `runtime.py` | Runtime CRUD、状态管理、Runtime-First API | ~20+ |
| `subagent.py` | SubAgent CRUD、状态管理、HRL | ~17 |
| `message.py` | 消息查询、标记、创建 | ~9 |
| `config.py` | Agent/LLM 配置 | ~5 |
| `task.py` | TaskManager API | ~6 |
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
3. 所有文件都使用相同的 `prefix="/internal"` 和 `tags=["internal"]`
4. `__init__.py` 统一导出所有 router

## 备份文件

原文件已备份为 `internal.py.backup`，确认一切正常后可删除。

## 拆分脚本

拆分由 `scripts/split_internal_api.py` 自动完成，可以随时重新运行。
