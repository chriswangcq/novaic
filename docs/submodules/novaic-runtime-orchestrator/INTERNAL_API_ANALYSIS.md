# Gateway Internal API 功能分析

## 当前状态

`internal.py` 文件包含 **3047 行代码**，功能非常庞大，确实需要拆分。

## 功能模块统计

| 模块 | 行数 | 路由数 | 说明 |
|------|------|--------|------|
| Runtime Resolution Helper | ~60 | 0 | 工具函数 |
| SubAgent Operations | ~370 | 12 | SubAgent CRUD 和状态管理 |
| HRL and Summary Lock | ~130 | 5 | Hot Runtime List 和摘要锁 |
| Runtime Operations | ~600 | 20 | Runtime CRUD 和状态管理 |
| Message Operations | ~270 | 9 | 消息查询和管理 |
| Agent Operations | ~40 | 3 | Agent 状态管理 |
| SSE Broadcast | ~35 | 2 | SSE 广播 |
| Config | ~270 | 5 | 配置管理（Agent、LLM） |
| LLM Operations | ~80 | 1 | LLM 上下文压缩 |
| Health Monitor | ~45 | 3 | 健康监控 |
| TaskManager API | ~130 | 6 | 任务管理 |
| SSH Key API | ~30 | 2 | SSH 密钥管理 |
| Runtime Tools API | ~80 | 2 | Runtime 工具相关 |
| Web API | ~135 | 2 | Web 搜索和抓取 |
| Runtime-First API | ~600 | 20+ | 基于 runtime_id 的各种 API |
| VM Tools Discovery | ~65 | 1 | VM 工具发现 |
| **总计** | **~3047** | **~93** | |

## 拆分建议

### 方案一：按功能域拆分（推荐）

```
gateway/api/internal/
├── __init__.py              # 导出所有 router
├── runtime.py               # Runtime 相关（~600行）
├── subagent.py              # SubAgent 相关（~500行）
├── message.py               # Message 相关（~270行）
├── agent.py                 # Agent 相关（~40行）
├── config.py                # Config 相关（~270行）
├── task.py                  # TaskManager 相关（~130行）
├── llm.py                   # LLM 相关（~80行）
├── web.py                   # Web API（~135行）
├── vm.py                    # VM/SSH/QEMU 相关（~200行）
├── health.py                # Health Monitor（~45行）
├── broadcast.py             # SSE Broadcast（~35行）
└── helpers.py               # 工具函数（~60行）
```

### 方案二：按调用方拆分

```
gateway/api/internal/
├── __init__.py
├── master.py                # Master 调用的 API
│   ├── runtime.py
│   ├── subagent.py
│   ├── message.py
│   └── agent.py
├── tools_server.py          # Tools Server 调用的 API
│   ├── task.py
│   ├── runtime_tools.py
│   ├── web.py
│   └── vm.py
└── shared.py                # 共享的工具函数
    ├── helpers.py
    └── config.py
```

### 方案三：混合方案（最推荐）

结合功能域和调用方，但以功能域为主：

```
gateway/api/internal/
├── __init__.py              # 统一导出
├── runtime.py               # Runtime 操作（包含 Runtime-First API）
├── subagent.py              # SubAgent 操作（包含 HRL）
├── message.py               # Message 操作
├── agent.py                 # Agent 操作
├── config.py                # Config 操作
├── task.py                  # TaskManager API
├── llm.py                   # LLM 操作
├── web.py                   # Web API
├── vm.py                    # VM/SSH/QEMU/VM Tools
├── health.py                # Health Monitor
├── broadcast.py             # SSE Broadcast
└── helpers.py               # 共享工具函数
    ├── resolve_runtime_ids()
    ├── get_runtime_context()
    ├── _runtime_to_dict()
    └── _subagent_to_dict()
```

## 拆分步骤

1. **创建新目录结构**
   ```bash
   mkdir -p novaic-backend/gateway/api/internal
   ```

2. **提取工具函数** → `helpers.py`
   - `resolve_runtime_ids()`
   - `get_runtime_context()`
   - `_runtime_to_dict()`
   - `_subagent_to_dict()`

3. **按模块拆分**
   - 每个模块独立文件
   - 使用 `from .helpers import ...` 导入共享函数
   - 每个文件定义自己的 `router = APIRouter(prefix="/internal", tags=["internal"])`

4. **更新 `__init__.py`**
   ```python
   from .runtime import router as runtime_router
   from .subagent import router as subagent_router
   # ... 其他 router
   
   router = APIRouter(prefix="/internal", tags=["internal"])
   router.include_router(runtime_router)
   router.include_router(subagent_router)
   # ... 其他 router
   ```

5. **更新 `main_gateway.py`**
   ```python
   from gateway.api.internal import router as internal_router
   app.include_router(internal_router)
   ```

## 注意事项

1. **保持向后兼容**：所有路由路径不变
2. **避免循环导入**：使用相对导入
3. **共享依赖**：`get_db()` 等在每个文件中导入
4. **测试覆盖**：拆分后确保所有 API 仍正常工作

## 优先级

**高优先级**（代码量大、功能独立）：
- Runtime Operations (~600行)
- SubAgent Operations (~500行)
- Runtime-First API (~600行)

**中优先级**：
- Message Operations (~270行)
- Config (~270行)
- TaskManager (~130行)

**低优先级**（代码量小但可独立）：
- Web API (~135行)
- LLM Operations (~80行)
- Health Monitor (~45行)
- SSE Broadcast (~35行)
