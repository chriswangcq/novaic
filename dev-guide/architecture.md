# NovAIC Backend 架构

## 四组件模型

Backend 由四个独立进程组成，由 Tauri 统一拉起：

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri Application                       │
│  (启动顺序: Gateway → MCP Gateway → Master → Worker)         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│   Gateway     │   │   MCP Gateway   │   │    Master     │
│   (19999)     │   │    (19998)      │   │               │
├───────────────┤   ├─────────────────┤   ├───────────────┤
│ • REST API    │   │ • MCPManager    │   │ • Monitor     │
│ • SQLite DB   │   │ • Agent Shared  │   │ • Scheduler   │
│ • SSE Events  │   │ • Runtime MCP   │   │ • Runtime 管理│
│ • VM 管理     │   │ • Aggregate GW  │   │               │
└───────────────┘   └─────────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │    Worker     │
                      │               │
                      ├───────────────┤
                      │ • Think       │
                      │ • Tool Call   │
                      │ • LLM 调用    │
                      └───────────────┘
```

## 组件职责

### Gateway (端口 19999)
- **入口**: `python main.py` 或 `novaic-backend gateway`
- **职责**: 
  - REST API 提供
  - SQLite 数据库管理
  - SSE 事件广播
  - VM 进程管理
- **不含**: MCP（已拆到 MCP Gateway）、ProcessManager（Worker 由 Tauri 拉起）

### MCP Gateway (端口 19998)
- **入口**: `python mcp_main.py` 或 `novaic-backend mcp-gateway`
- **职责**:
  - MCPManager 管理所有 MCP 服务
  - Agent Shared MCP（local、memory、chat、qemudebug）
  - Runtime MCP（per-runtime）
  - Aggregate Gateway（聚合多个 MCP）
- **依赖**: 需要 `NOVAIC_GATEWAY_URL` 指向 Gateway

### Master
- **入口**: `python master_main.py` 或 `novaic-backend master`
- **职责**:
  - Monitor: 监控 Runtime 状态
  - Scheduler: 调度任务到 Worker
  - Runtime 生命周期管理
- **依赖**: 需要 `--gateway-url` 和 `--mcp-gateway-url`

### Worker
- **入口**: `python -m worker.worker` 或 `novaic-backend worker`
- **职责**:
  - Think: 调用 LLM 进行思考
  - Tool Call: 执行 MCP 工具
  - Reply: 回复用户
- **依赖**: 需要 `--gateway` 和 `--mcp-gateway-url`

## 端口分配

| 组件 | 默认端口 | 环境变量 |
|------|----------|----------|
| Gateway | 19999 | `NOVAIC_PORT` |
| MCP Gateway | 19998 | `NOVAIC_MCP_PORT` |
| VM SSH | 20000+ | 动态分配 |
| VM VNC | 20005+ | 动态分配 |

## 通信关系

```
Frontend (Web/App)
    │
    ▼ HTTP
Gateway (19999)
    │
    ├── SSE ──────────► Worker (订阅任务)
    │
    └── HTTP ─────────► Master (internal API)
                            │
                            └── HTTP ──► MCP Gateway (创建 MCP)
                                              │
Worker ◄──────────────────────────────────────┘
    │                                    MCP 工具调用
    └── HTTP ──────────────────────────► MCP Gateway (19998)
```

## 数据流

1. **用户发消息** → Gateway API → 存 DB → SSE 通知 Master
2. **Master 创建 Runtime** → 调 MCP Gateway 创建 MCP → 返回完整 MCP URL
3. **Master 调度任务** → Gateway 广播 → Worker 认领
4. **Worker 执行** → 调 MCP Gateway 的工具 → 结果回传 Gateway
