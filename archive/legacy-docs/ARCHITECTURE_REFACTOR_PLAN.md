# Novaic 架构重构实施计划

> 创建日期: 2026-02-04  
> 最后更新: 2026-02-04  
> 目标: 实现 Business System (Gateway/MCP) 与 Agent System (Watchdog/QS/Workers) 的清晰分层

## 核心设计原则

**所有 Saga 创建 = Watchdog → Queue Service**

- Gateway 永远不直接调用 Queue Service 创建 saga
- Gateway 只负责写入消息 (status=sending)
- Watchdog 监测消息 → 调用 Queue Service 创建 saga

---

## 目标架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Business System (API Layer)                      │
│                                                                         │
│   Gateway (19999)                         MCP Gateway (19998)           │
│   - /api/* (前端)                         - /internal/mcp/*             │
│   - /internal/* (Worker API)                                            │
│   - /internal/tq/handlers/execute (新增)                                │
│                                                                         │
│   ⚠️ 不直接调用 Queue Service                                           │
└─────────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Workers 调用 Gateway 执行业务
                              │
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agent System (Core Layer)                        │
│                                                                         │
│   Watchdog ──────────────→ Queue Service ──────────────→ Workers       │
│   (唤醒系统)               (纯调度中间件)               (执行者)        │
│   监控 Gateway 消息         无业务逻辑                  调 Gateway      │
│   创建 Saga 到 QS           独立运行                    执行 handler    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 当前问题清单

| # | 组件 | 问题 | 严重程度 |
|---|------|------|----------|
| 1 | Gateway | 缺少 `/internal/tq/handlers/execute` 端点 | P1-阻塞 |
| 2 | Watchdog | 调用错误端点创建 saga | P1-阻塞 |
| 3 | Gateway | `spawn_subagent` 直接调用 QS | P2-违规 |
| 4 | Gateway | `rt_subagent_spawn` 直接调用 QS | P2-违规 |
| 5 | Gateway | `/interrupt` 直接调用 QS | P2-违规 |
| 6 | QS | `saga.py` 导入 Gateway 模块 | P2-违规 |
| 7 | QS | 存在未使用的 router 定义 | P3-清理 |

---

## Phase 1: Gateway 解耦 + 基础设施 ✅ 已完成

### 1.1 Gateway 添加 Handler 执行端点 ✅

**目标**: Task Worker 能够调用 Gateway 执行 handler

**文件**: `novaic-backend/gateway/api/internal.py`

**修改内容**:
- 添加 `POST /internal/tq/handlers/execute` 端点
- 添加 `GET /internal/tq/handlers/topics` 端点

**检查清单**:
- [x] 阅读现有 handler 执行逻辑 (`task_queue/handlers/`)
- [x] 在 `internal.py` 添加路由
- [x] 实现 handler 分发逻辑
- [x] 添加错误处理 (RetryableError → 503)
- [x] 语法验证通过

**验证命令**:
```bash
curl -X POST http://localhost:19999/internal/tq/handlers/execute \
  -H "Content-Type: application/json" \
  -d '{"topic": "ping", "payload": {}}'
```

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: 在 gateway/api/internal.py 末尾添加了两个端点
- /internal/tq/handlers/execute - 执行 handler
- /internal/tq/handlers/topics - 列出所有 topics
```

---

### 1.2 Watchdog 调用 Queue Service 创建 Saga ✅

**目标**: Watchdog 正确调用 Queue Service 创建 saga

**文件**: `novaic-backend/task_queue/workers/watchdog.py`

**修改内容**:
1. 添加 `queue_service_url` 参数和环境变量支持
2. 分离 `_gateway_client` 和 `_queue_client`
3. 修改 saga 创建调用为 QS: `/api/queue/sagas/start`

**检查清单**:
- [x] 添加 QUEUE_SERVICE_URL 配置
- [x] 分离 Gateway 和 QS 客户端
- [x] 修改 HTTP 调用目标
- [x] 确保请求格式与 QS API 匹配
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: 重构 Watchdog 类
- 添加 queue_service_url 参数 (默认从 QUEUE_SERVICE_URL 环境变量)
- 分离 _get_gateway_client() 和 _get_queue_client()
- saga 创建改为调用 QS /api/queue/sagas/start
```

---

### 1.3 Gateway spawn_subagent 解耦 ✅

**目标**: Gateway 不再直接调用 QS，改为写消息让 Watchdog 处理

**文件**: `novaic-backend/gateway/api/internal.py`

**修改内容**:
- 删除直接调用 Queue Service 的代码
- 改为写入 `SPAWN_SUBAGENT` 消息 (status=sending)

**检查清单**:
- [x] 修改 `spawn_subagent` (line 302-326)
- [x] 修改 `rt_subagent_spawn` (line 2555-2579)
- [x] 使用 MessageRepository 写入消息
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: 两处 spawn 端点都改为写入 SPAWN_SUBAGENT 消息
- 消息包含 metadata: {subagent_id, trigger_id, initial_context}
- Gateway 不再直接调用 Queue Service
```

---

### 1.4 Watchdog 支持 SPAWN_SUBAGENT 消息类型 ✅

**目标**: Watchdog 能监测并处理 SPAWN_SUBAGENT 消息

**文件**: `novaic-backend/task_queue/workers/watchdog.py`

**修改内容**:
- 重构 `_create_saga_for_message` 方法
- 添加消息类型分发逻辑
- 新增 `_create_message_process_saga` 方法
- 新增 `_create_runtime_start_saga` 方法

**消息类型 → Saga 映射**:
| 消息类型 | Saga 类型 |
|----------|-----------|
| USER_MESSAGE | message_process |
| SPAWN_SUBAGENT | runtime_start |

**检查清单**:
- [x] 添加消息类型分发逻辑
- [x] 实现 `_create_message_process_saga`
- [x] 实现 `_create_runtime_start_saga`
- [x] 从 metadata 读取 subagent_id, trigger_id, initial_context
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: Watchdog 现在支持多消息类型
- USER_MESSAGE → message_process saga
- SPAWN_SUBAGENT → runtime_start saga
- metadata 字段用于传递 saga context
```

---

## Phase 2: /interrupt 端点解耦 + 扩展消息类型 ✅ 已完成

### 2.0 Queue Service 添加 cancel-all API ✅

**目标**: 提供任务/saga 取消接口

**文件**: 
- `novaic-backend/queue_service/routes.py`
- `novaic-backend/queue_service/queue_db.py`
- `novaic-backend/queue_service/saga_repo.py`

**修改内容**:
- 添加 `POST /api/queue/recover/cancel-all` 端点
- TaskQueue 添加 `cancel_all()` 方法
- SagaRepository 添加 `cancel_all()` 方法

**检查清单**:
- [x] routes.py 添加 cancel-all 端点
- [x] queue_db.py 添加 TaskQueue.cancel_all()
- [x] saga_repo.py 添加 SagaRepository.cancel_all()
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: 发现原 cancel-all API 不存在，需要先添加
- cancel_all 支持可选的 agent_id 参数过滤
```

---

### 2.1 重构 /interrupt 端点 ✅

**目标**: /interrupt 不再直接调用 QS

**文件**: `novaic-backend/gateway/api/routes.py`

**目标流程**:
```
Gateway./interrupt
  → 立即更新 Gateway 数据库 (runtimes, subagents)
  → 写入 INTERRUPT 消息 (status=sending)
  → Watchdog 监测到
  → 调用 QS cancel API
```

**检查清单**:
- [x] 定位 routes.py 中 interrupt 代码
- [x] 保留 Gateway 数据库更新（立即响应）
- [x] 删除 QS 直接调用
- [x] 写入 INTERRUPT 消息
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: interrupt 改为混合模式
- Gateway 数据库更新保持同步（用户立即看到效果）
- QS cancel 通过 Watchdog 异步处理
```

---

### 2.2 Watchdog 支持 INTERRUPT 消息 ✅

**目标**: Watchdog 能处理 INTERRUPT 消息并调用 QS cancel

**文件**: `novaic-backend/task_queue/workers/watchdog.py`

**修改内容**:
- 在消息分发中添加 INTERRUPT 类型
- 添加 `_handle_interrupt()` 方法
- 调用 QS `/api/queue/recover/cancel-all`

**检查清单**:
- [x] 添加 INTERRUPT 消息处理
- [x] 实现 `_handle_interrupt()` 方法
- [x] 调用 QS cancel-all API
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: Watchdog 现在支持三种消息类型
- USER_MESSAGE → message_process saga
- SPAWN_SUBAGENT → runtime_start saga
- INTERRUPT → QS cancel-all API (不创建 saga)
```

---

## Phase 3: Queue Service 清理 ✅ 已完成

### 3.1 移除 Gateway 模块导入 ✅

**目标**: Queue Service 完全独立，不依赖 Gateway 模块

**文件**: `novaic-backend/queue_service/saga.py`

**修改内容**:
- 删除 `SagaRepository` 类（原导入 Gateway 模块）
- 删除 `SagaOrchestrator` 类（原导入 Gateway 模块）
- 保留类型定义和协议（`TaskQueueProtocol`, `SagaDefinition` 等）

**检查清单**:
- [x] 定位所有 Gateway 导入
- [x] 删除不需要的类（实际使用 saga_repo.py 的实现）
- [x] 验证无 Gateway 导入
- [x] 语法验证通过

**验证命令**:
```bash
grep -r "from gateway" queue_service/
# 结果: No Gateway imports found
```

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: saga.py 中的 SagaRepository 和 SagaOrchestrator 只是代理类
- 实际使用的是 saga_repo.py 中的实现
- 删除代理类后 QS 完全独立
```

---

### 3.2 删除未使用的 Router 定义 ✅

**目标**: 清理 QS 中不应存在的业务 API 定义

**文件**: `novaic-backend/queue_service/routes.py`

**删除内容**:
- `create_handler_router()` 函数
- `create_business_router()` 函数
- `HandlerExecRequest`, `HandlerExecResponse` 模型
- `MessageProcessRequest`, `MessageProcessResponse` 模型

**检查清单**:
- [x] 确认这些 router 未被使用
- [x] 删除 `create_handler_router`
- [x] 删除 `create_business_router`
- [x] 删除相关模型定义
- [x] 语法验证通过

**完成状态**: ✅ 已完成

**备注**:
```
实施记录:
- 2026-02-04: 这些 router 原本返回 501，表示不支持
- Handler 执行 API 已移至 Gateway /internal/tq/handlers/execute
- QS 现在是纯调度中间件
```

---

## 新增消息类型汇总

| 消息类型 | 触发场景 | 对应 Saga | metadata 结构 |
|----------|----------|-----------|---------------|
| `USER_MESSAGE` | 用户发消息 | `message_process` | `{...}` |
| `SPAWN_SUBAGENT` | 创建子 agent | `runtime_start` | `{subagent_id, runtime_id, initial_context}` |
| `INTERRUPT` | 用户中断 | `cancel_tasks` | `{action: "cancel_all"}` |

---

## 回滚方案

如果某个 Phase 出现问题:

### Phase 1 回滚
```bash
# 1.1 回滚: 删除新增的 handler 执行端点
git checkout novaic-backend/main_gateway.py

# 1.2 回滚: 恢复 Watchdog 原有调用
git checkout novaic-backend/task_queue/workers/watchdog.py
```

### Phase 2 回滚
```bash
# 恢复 Gateway 直接调用 QS 的代码
git checkout novaic-backend/gateway/api/internal.py
git checkout novaic-backend/gateway/api/routes.py
git checkout novaic-backend/task_queue/workers/watchdog.py
```

### Phase 3 回滚
```bash
# 恢复 QS 原有代码
git checkout novaic-backend/queue_service/saga.py
git checkout novaic-backend/queue_service/routes.py
```

---

## 完成检查清单

### Phase 1 完成标准
- [x] ~~Gateway `/internal/tq/handlers/execute`~~ **已删除** - Task Worker 本地执行 handler
- [x] Task Worker 本地执行 handler ✅ 运行时测试通过 (2026-02-04 20:06)
- [x] Watchdog 能成功调用 QS 创建 saga (代码已修改)
- [x] Gateway spawn_subagent 不再直接调用 QS
- [x] Watchdog 支持 SPAWN_SUBAGENT 消息类型
- [x] 用户消息处理流程正常 ✅ 运行时测试通过 (2026-02-04 19:49)

### Phase 2 完成标准
- [x] Gateway 不再直接调用 QS 创建 saga
- [x] spawn_subagent 通过 Watchdog 模式工作 (代码已修改)
- [x] interrupt 通过 Watchdog 模式工作 (代码已修改)
- [x] 端到端测试通过 ✅ 消息发送 -> Watchdog -> QS Saga -> 完成

### Phase 3 完成标准
- [x] QS 不导入 Gateway 模块 (grep 验证通过)
- [x] QS 可独立启动运行 ✅ 运行时测试通过
- [x] 所有测试通过 ✅ 2026-02-04 19:49

---

## 最终验证

```bash
# 1. 检查 Gateway 不直接调用 QS
grep -r "queue_service_url" novaic-backend/gateway/
# 预期: 无结果

# 2. 检查 QS 不导入 Gateway
grep -r "from gateway" novaic-backend/queue_service/
# 预期: 无结果

# 3. 端到端测试
python comprehensive_smoke_test.py
```

---

## 变更日志

| 日期 | Phase | 任务 | 状态 | 备注 |
|------|-------|------|------|------|
| 2026-02-04 | 1.1 | Gateway Handler 执行端点 | ✅ | internal.py 添加 /internal/tq/handlers/execute |
| 2026-02-04 | 1.2 | Watchdog 调用 QS | ✅ | 分离 gateway/queue 客户端，调用 /api/queue/sagas/start |
| 2026-02-04 | 1.3 | spawn_subagent 解耦 | ✅ | 改为写入 SPAWN_SUBAGENT 消息 |
| 2026-02-04 | 1.4 | Watchdog 支持多消息类型 | ✅ | USER_MESSAGE, SPAWN_SUBAGENT |
| 2026-02-04 | 2.0 | QS cancel-all API | ✅ | 新增 /api/queue/recover/cancel-all |
| 2026-02-04 | 2.1 | interrupt 端点解耦 | ✅ | 改为写入 INTERRUPT 消息 |
| 2026-02-04 | 2.2 | Watchdog 支持 INTERRUPT | ✅ | 调用 QS cancel-all API |
| 2026-02-04 | 3.1 | QS 移除 Gateway 导入 | ✅ | 删除 saga.py 中的代理类 |
| 2026-02-04 | 3.2 | QS 删除未使用 router | ✅ | 删除 handler/business router |
| 2026-02-04 | 3.3 | 删除 Gateway handler 执行端点 | ✅ | Task Worker 本地执行 handler |
| 2026-02-04 | 3.4 | QS 新增 /api/queue/topics | ✅ | Task Worker 从 QS 获取 topics |
| 2026-02-04 | 4.1 | 删除异步 Worker 版本 | ✅ | 统一使用同步版本 (_sync.py) |
| 2026-02-04 | 4.2 | 更新 main_*.py 入口 | ✅ | 使用同步 Worker + QS URL |
| 2026-02-04 | 4.3 | 修复 message_process 决策 | ✅ | 正确解析 route_message 结果 |
| 2026-02-04 | 4.4 | Task Worker 添加 saga_client | ✅ | 支持 saga.trigger handler |
| 2026-02-04 | 4.5 | run-dev.sh 添加 Queue Service | ✅ | 开发脚本自动启动 QS |
| 2026-02-04 | 4.6 | Task Worker 添加 mcp_client | ✅ | 支持 tool.execute handler |
| | | | | |

---

## 附录: 文件修改清单

| 文件 | Phase | 修改类型 | 状态 |
|------|-------|----------|------|
| `gateway/api/internal.py` | 1.1, 1.3 | 新增端点 + 修改 spawn | ✅ |
| `task_queue/workers/watchdog.py` | 1.2, 1.4, 2.2 | 重构 + INTERRUPT | ✅ |
| `gateway/api/routes.py` | 2.1 | 修改 interrupt | ✅ |
| `queue_service/routes.py` | 2.0 | 新增 cancel-all 端点 | ✅ |
| `queue_service/queue_db.py` | 2.0 | 新增 cancel_all 方法 | ✅ |
| `queue_service/saga_repo.py` | 2.0 | 新增 cancel_all 方法 | ✅ |
| `queue_service/saga.py` | 3.1 | 移除 Gateway 导入 | ✅ |
| `task_queue/workers/saga_worker_v2.py` | 4.1 | 删除 | ✅ |
| `task_queue/workers/task_worker_v2.py` | 4.1 | 删除 | ✅ |
| `task_queue/workers/health_worker_v2.py` | 4.1 | 删除 | ✅ |
| `main_saga.py` | 4.2 | 改用 SagaWorkerSync | ✅ |
| `main_task.py` | 4.2 | 改用 TaskWorkerSync + gateway_url | ✅ |
| `main_health.py` | 4.2 | 改用 HealthWorkerSync | ✅ |
| `task_queue/sagas/message_process.py` | 4.3 | 修复 _decide_action | ✅ |
| `task_queue/workers/task_worker_sync.py` | 4.4, 4.6 | 添加 saga_client, mcp_client | ✅ |
| `dev-guide/run-dev.sh` | 4.5 | 添加 start_queue | ✅ |
