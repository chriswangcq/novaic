# NovAIC 开发指南

> 指挥中心文档 — 面向开发者的实操指南

---

## 1. 项目结构（Split 架构）

NovAIC 采用多仓库拆分架构，各 repo 职责如下：

| 仓库 | 职责 | 端口 | 关键入口 |
|------|------|------|----------|
| **novaic-app** | Tauri 桌面客户端 + 前端 | - | `src-tauri/src/main.rs`, `src/` |
| **novaic-gateway** | API 网关、Agent/SubAgent 管理 | 19999 | `main_gateway.py`, `gateway/api/` |
| **novaic-runtime-orchestrator** | Runtime 编排、主 Agent 流程 | 19993 | `gateway/api/`, `task_queue/` |
| **novaic-tools-server** | 工具执行、MCP 集成 | 19998 | `tools_server/api.py`, `executor.py` |
| **novaic-agent-runtime** | Task/Saga Worker、Queue Service | 19997 | `queue_service/`, `task_queue/` |
| **novaic-storage-a** | File Service | 19997 | `file_service/` |
| **novaic-storage-b** | Tool Result Service (TRS) | 19994 | `tool_result_service/` |
| **novaic-mcp-vmuse** | VM 内 MCP 工具 | - | 资源内嵌 |

---

## 2. 环境准备

### 2.1 依赖

- **Python 3.11+**：各 backend 需 `.venv` 或 `venv`
- **Node.js 18+**：前端
- **Rust**：vmcontrol、Tauri
- **Cargo**：构建 Tauri

### 2.2 目录结构（假设 SPLIT_ROOT）

```
SPLIT_ROOT/
├── novaic-app/           # 应用
├── novaic-gateway/
├── novaic-runtime-orchestrator/
├── novaic-tools-server/
├── novaic-agent-runtime/
├── novaic-storage-a/
├── novaic-storage-b/
├── novaic-mcp-vmuse/
└── novaic-control-plane/ # 指挥中心
```

---

## 3. 编译与构建

### 3.1 完整 DMG 构建

```bash
cd novaic-app
./scripts/build-dmg.sh
```

步骤：
1. 构建 6 个 Python backend（PyInstaller）
2. 构建 vmcontrol（Rust）
3. 复制资源（android-sdk、scrcpy-server、novaic-mcp-vmuse）
4. 构建 Tauri DMG

产物：
- `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.x.x_aarch64.dmg`
- `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`

### 3.2 单仓库构建

```bash
# 单个 Python backend
cd novaic-gateway
source .venv/bin/activate
pyinstaller --clean --noconfirm novaic-gateway.spec

# 前端开发
cd novaic-app
npm run tauri:dev

# 仅 Tauri（跳过 Python）
./scripts/build-dmg.sh --skip-python
```

---

## 4. 开发模式运行

### 4.1 启动应用（开发模式）

```bash
cd novaic-app
npm run tauri:dev
```

会从 `SPLIT_ROOT` 拉起各 Python 服务，而非打包二进制。

### 4.2 单服务调试

```bash
# Gateway
cd novaic-gateway && python main_gateway.py --data-dir ~/Library/Application\ Support/com.novaic.app --port 19999

# Tools Server
cd novaic-tools-server && python -m tools_server.main --data-dir ~/Library/Application\ Support/com.novaic.app

# Queue Service
cd novaic-agent-runtime && python -m queue_service.main --queue-service-url http://127.0.0.1:19997
```

---

## 5. 调试常用路径

### 5.1 数据目录（macOS）

```
~/Library/Application Support/com.novaic.app/
├── gateway.db
├── runtime_orchestrator.db
├── queue.db
├── tool_results.db
├── logs/
│   ├── gateway-YYYYMMDD.log
│   ├── tools-server.log
│   ├── runtime-orchestrator.log
│   ├── task-worker-YYYYMMDD.log
│   ├── saga-worker-YYYYMMDD.log
│   └── tool-result-service.log
└── config/
```

### 5.2 常用 API 调试

```bash
# Agent 列表
curl -s "http://127.0.0.1:19999/api/agents" | python3 -m json.tool

# 聊天历史
curl -s "http://127.0.0.1:19999/api/chat/history?agent_id=xxx&limit=10" | python3 -m json.tool

# 执行日志
curl -s "http://127.0.0.1:19999/api/logs/entries?agent_id=xxx&limit=10" | python3 -m json.tool

# 健康检查
curl http://127.0.0.1:19999/api/health
curl http://127.0.0.1:19998/health
curl http://127.0.0.1:19997/health
```

### 5.3 SQLite 调试

```bash
DATA_DIR=~/Library/Application\ Support/com.novaic.app

# 任务队列
sqlite3 "$DATA_DIR/queue.db" "SELECT id, topic, status, error FROM tq_tasks ORDER BY created_at DESC LIMIT 10;"

# Saga
sqlite3 "$DATA_DIR/queue.db" "SELECT id, saga_type, status, current_step FROM tq_sagas ORDER BY created_at DESC LIMIT 5;"

# 执行日志
sqlite3 "$DATA_DIR/gateway.db" "SELECT id, kind, status, event_key FROM execution_logs ORDER BY id DESC LIMIT 10;"
```

---

## 6. 关键流程速查

### 6.1 消息处理流程

```
用户消息 → Gateway API → chat_messages
  → message_process Saga → message.route
  → runtime_start → react_think → llm.call
  → react_actions → tool.execute (Tools Server)
  → context.append → check_new_messages
  → react_think 或 runtime_complete
```

### 6.2 工具执行流程

```
tool.execute (Task Handler)
  → MCPBusiness.execute_tool
  → POST Tools Server /internal/runtimes/{runtime_id}/tools/call
  → ToolExecutor.execute
  → Gateway API 或 vmcontrol
  → 结果推 TRS (create_from_raw)
  → 返回 result_id
```

### 6.3 工具结果存储 (TRS)

- 工具执行结果统一通过 TRS 存储
- `create_from_raw` 将 raw 转为 `{text, files_created, display_files}` 三要素
- 注意：`display_files` 需 `{url, filename, modality}`，否则 TRS 校验失败

---

## 7. 常见问题

### 7.1 工具执行失败 / result_id 为空

- 检查 `runtime.agent_id` 是否为空（lazy_hydrate 分支）
- 检查 TRS 服务是否正常
- 查看 `tools-server.log` 中 `[ToolsAPI.call_tool]` 日志

### 7.2 subagent_query 返回 success=False

- 检查 Gateway subagent status API 返回格式
- 若 `error` 为业务数据（子任务失败），不应视为 API 失败

### 7.3 Saga 卡住

- 查 `tq_sagas` 的 `current_step`、`error`
- 查 `tq_tasks` 的 `status` 是否为 `claimed` 且长时间未完成
- 查 task-worker、saga-worker 日志

---

## 8. 相关文档

- [ARCHITECTURE.md](../../novaic/ARCHITECTURE.md) — 系统架构（novaic 仓库）
- [BACKLOG.md](../BACKLOG.md) — 开发待办
- [TOOL_ERRORS_ANALYSIS.md](../../docs/TOOL_ERRORS_ANALYSIS.md) — 工具错误分析
- [TOOL_ERRORS_TROUBLESHOOTING.md](../../docs/TOOL_ERRORS_TROUBLESHOOTING.md) — 工具错误排查
