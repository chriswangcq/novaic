# Business 实体管理

## 概述与职责

Business 是 Novaic 平台的实体管理服务，运行在端口 `:19998`，基于 Python / FastAPI 构建。它承担平台所有业务实体的 CRUD 管理、Action Hook 触发和变更事件分发，是平台业务逻辑的核心载体。

核心职责包括：

- 管理 19 种业务实体的完整生命周期
- 提供 60+ 条 HTTP API 路由
- 通过 Action Hook 机制在实体变更前后执行业务逻辑
- 通过 DispatchSubscriber 将变更事件分发到 Agent Runtime

## 双进程架构

Business 服务采用双进程架构，两个进程协作但独立运行：

### API Server 进程

FastAPI 应用，处理 HTTP 请求，负责实体的 CRUD 操作和 API 暴露。

### DispatchSubscriber 进程

后台订阅进程，监听实体变更事件并将其转发到 Queue Service。

```
外部请求 → API Server → 实体 CRUD → 数据库写入
                                ↓
                          变更事件发布
                                ↓
              DispatchSubscriber 消费变更事件
                                ↓
                    转发到 Queue Service（Agent Runtime）
```

这种设计将请求处理和事件分发解耦，API Server 不会因事件分发延迟而阻塞响应。

## Entity Schema 与 Action Hooks

### 19 种实体 Schema

Business 管理的实体涵盖平台的核心业务域：

| 类别 | 实体 | 说明 |
|------|------|------|
| 用户与权限 | User, Team, ApiKey | 用户账户、团队组织、API 密钥 |
| Agent | Agent, AgentConfig, Skill | Agent 定义、配置和技能 |
| 设备 | Device, DevicePool | 设备实例和设备池 |
| 会话 | Session, Message | 用户与 Agent 的交互会话 |
| 模型 | Model, ModelProvider | LLM 模型和提供商配置 |
| 任务 | Task, TaskTemplate | 任务实例和任务模板 |
| 存储 | File, Workspace | 文件和工作空间 |
| 其他 | Notification, AuditLog, Setting | 通知、审计日志、系统设置 |

### 30+ Action Hooks

Action Hook 是在实体 CRUD 操作的特定时机触发的业务逻辑。系统定义了 30+ 个 Hook：

| Hook 类型 | 触发时机 | 示例 |
|-----------|----------|------|
| `before_create` | 实体创建前 | 校验 Agent 配置完整性 |
| `after_create` | 实体创建后 | 为新 Agent 初始化默认 Skill |
| `before_update` | 实体更新前 | 检查设备状态是否允许变更 |
| `after_update` | 实体更新后 | 同步更新关联实体 |
| `before_delete` | 实体删除前 | 检查关联依赖，阻止级联删除 |
| `after_delete` | 实体删除后 | 清理关联资源 |
| 自定义 Action | 显式调用 | Agent 启动、设备分配、会话创建等 |

Hook 支持异步执行，失败时可配置为回滚或仅记录日志。

## DispatchSubscriber 机制

DispatchSubscriber 是 Business 的变更事件分发引擎：

1. **事件源**：API Server 在实体 CRUD 完成后发布变更事件。
2. **事件订阅**：DispatchSubscriber 通过内部消息通道订阅这些事件。
3. **事件过滤**：根据配置的规则过滤需要转发的事件（不是所有变更都需要通知 Agent Runtime）。
4. **事件转发**：将过滤后的事件通过 HTTP 请求发送到 Queue Service 的任务入队接口。

关键设计决策：

- **At-least-once 语义**：事件可能重复投递，下游需要幂等处理。
- **异步非阻塞**：使用异步 HTTP 客户端，不阻塞事件消费循环。
- **失败重试**：转发失败时进行有限次指数退避重试。

## Internal API 路由

Business 通过 9 个 Internal API Router 组织 60+ 条 HTTP 路由：

| Router | 路由前缀 | 说明 |
|--------|----------|------|
| Agent Router | `/internal/agent` | Agent 实体 CRUD 和自定义操作 |
| Device Router | `/internal/device` | 设备注册、状态更新、分配 |
| Session Router | `/internal/session` | 会话创建、消息追加、历史查询 |
| User Router | `/internal/user` | 用户管理和认证信息 |
| Task Router | `/internal/task` | 任务创建、状态流转、结果写回 |
| Model Router | `/internal/model` | 模型配置和提供商管理 |
| Skill Router | `/internal/skill` | 技能定义和绑定 |
| File Router | `/internal/file` | 文件元数据管理 |
| Setting Router | `/internal/setting` | 系统设置读写 |

所有路由使用 `/internal` 前缀，表明这些是服务间内部调用接口，不直接暴露给外部客户端。

## 依赖关系

```
Business
├── 数据库（PostgreSQL/SQLite） — 实体持久化存储
├── Queue Service（Agent Runtime） — 变更事件分发目标
├── Cortex — 会话和消息相关实体的上下文关联
└── Entangled — 实体变更实时推送到前端
```

Business 是平台的业务数据中枢，被 Gateway、Agent Runtime 等服务广泛调用。
