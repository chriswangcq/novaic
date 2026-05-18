# Cortex 上下文管理

## 概述与职责

Cortex 是 Novaic 平台的上下文管理服务，运行在端口 `:19996`，基于 Python / FastAPI 构建。它为 Agent 的推理循环提供结构化的上下文存储、检索和压缩能力，是连接 Agent Runtime 与 LLM 之间的上下文桥梁。

核心职责包括：

- 管理 Agent 会话的完整上下文生命周期
- 提供结构化的 ContextEvent 事件流
- 在 Token 预算内智能压缩上下文
- 通过 Scope Lock 保证并发安全
- 管理 Shell 会话和 Sandbox 状态

## 核心模块划分

Cortex 内部按职责划分为 5 个核心模块：

| 模块 | 职责 | 关键能力 |
|------|------|----------|
| `scope` | 作用域管理 | 定义上下文的边界和生命周期，管理 scope 的创建/销毁/嵌套 |
| `context` | 上下文存储与检索 | ContextEvent 的 CRUD、查询、排序和序列化 |
| `shell` | Shell 会话管理 | 维护 Shell 进程状态、输出缓冲和历史记录 |
| `sandbox` | 沙箱状态管理 | 跟踪沙箱环境的挂载点、文件系统和进程状态 |
| `payload` | 载荷处理 | 大型载荷（图片、文件）的外部化存储和引用管理 |

## ContextEvent 模型

ContextEvent 是 Cortex 的核心数据模型，表示 Agent 交互过程中产生的每一个结构化事件。系统定义了 10 种事件类型：

| 事件类型 | 说明 | 典型来源 |
|----------|------|----------|
| `user_message` | 用户输入的消息 | Gateway 转发 |
| `assistant_message` | Agent 生成的回复 | Agent Runtime |
| `tool_call` | Agent 发起的工具调用 | ReAct Loop |
| `tool_result` | 工具执行返回的结果 | Worker |
| `observation` | Agent 的环境观察结果 | 屏幕观察 Worker |
| `action` | Agent 执行的操作 | 感知-动作 Worker |
| `thought` | Agent 的内部推理过程 | ReAct Loop |
| `summary` | 上下文压缩后的摘要 | 压缩引擎 |
| `system` | 系统级指令和提示 | 系统初始化 |
| `error` | 错误事件 | 各 Worker |

每个 ContextEvent 包含时间戳、scope_id、序列号等元数据，支持按时间和因果关系排序。

## Token Budget 压缩策略

Cortex 实现了 3 级 Token 预算压缩策略，确保上下文在 LLM 窗口限制内保持最大信息密度：

**第 1 级 — 裁剪（Truncation）**

对超长的单条事件内容（如大段 Shell 输出）进行尾部裁剪，保留头部和尾部关键信息。

**第 2 级 — 摘要（Summarization）**

当上下文总 Token 数接近预算时，对较早的事件序列调用 LLM 生成摘要，替换原始事件为 `summary` 类型事件。

**第 3 级 — 淘汰（Eviction）**

在极端情况下，按优先级淘汰最低价值的事件。淘汰优先级：`thought` < `observation` < `tool_result` < `tool_call` < `assistant_message` < `user_message` < `system`。

```
原始上下文（可能超出窗口）
  ↓ 第 1 级：裁剪超长单条事件
  ↓ 第 2 级：摘要早期事件序列
  ↓ 第 3 级：淘汰低优先级事件
压缩后上下文（适配 Token 预算）
```

## Scope Lock 机制

Cortex 使用 Redis 分布式锁实现 Scope 级别的并发访问控制：

- **锁粒度**：每个 Scope 独立加锁，不同 Scope 可并行操作。
- **锁实现**：基于 Redis `SET NX EX` 原语，带自动过期防死锁。
- **读写分离**：读操作不加锁（最终一致），写操作必须持有锁。
- **竞争处理**：写请求在锁竞争时进行有限次重试，超时后返回错误。

这保证了同一个 Agent 会话在多 Worker 并发写入上下文时的数据一致性。

## API 路由

Cortex 对外暴露 40+ 条 HTTP API 路由：

| 路由前缀 | 说明 |
|----------|------|
| `/scope` | Scope 创建、查询、销毁、嵌套管理 |
| `/context` | ContextEvent 的写入、批量查询、按类型过滤 |
| `/context/compress` | 触发手动压缩、查询压缩状态 |
| `/shell` | Shell 会话创建、输出查询、状态管理 |
| `/sandbox` | 沙箱环境状态查询和管理 |
| `/payload` | 大型载荷的上传引用和检索 |
| `/health` | 健康检查和就绪探针 |

## 依赖关系

```
Cortex
├── Redis       — Scope Lock 分布式锁 + 缓存
├── SQLite      — ContextEvent 持久化操作存储
└── Blob Service — 大型载荷的外部化存储（通过 payload 模块）
```

Cortex 本身是被动服务，不主动调用其他业务服务。Agent Runtime 和 Business 是它的主要调用方。
