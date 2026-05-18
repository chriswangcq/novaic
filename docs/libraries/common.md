# novaic-common 共享库

## 概述与职责

novaic-common 是平台的共享 Python 库，**不是独立服务**，不监听任何端口。它为所有后端服务提供统一的配置加载、HTTP 通信客户端、数据契约定义以及 LLM 工具声明等基础能力。

各服务通过 `pip install` 或 monorepo 内部引用的方式依赖 novaic-common，确保跨服务的类型安全和协议一致性。

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Cortex    │  │   Runtime   │  │  Gateway    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                ┌───────▼───────┐
                │ novaic-common │
                │  (共享库)      │
                └───────────────┘
```

主要职责：

| 职责领域 | 说明 |
|---------|------|
| 配置加载 | 从 `services.json` 严格加载并校验所有服务 URL |
| HTTP 客户端 | 基于 httpx 的异步 HTTP 客户端，统一服务间通信 |
| 数据契约 | 9 个 contract 模块定义服务间数据结构 |
| LLM 工具 | 5 个内建工具定义，供 LLM 调用 |
| 消息组装 | Wake Assembler 负责消息组装流程 |
| WebSocket | EntangledServiceClient 提供 WS 长连接能力 |

## ServiceConfig 配置加载

ServiceConfig 实现了严格（strict）的配置加载机制，从 `services.json` 配置文件中读取所有服务的连接信息。

**加载流程：**

1. 读取 `services.json` 文件（路径通过环境变量或默认位置指定）
2. 解析 JSON 并提取各服务的 URL 配置
3. 对每个 URL 执行格式校验（scheme、host、port）
4. 校验失败时立即抛出异常，阻止服务启动

**配置项示例：**

```json
{
  "cortex":   { "url": "http://localhost:8100" },
  "runtime":  { "url": "http://localhost:8200" },
  "gateway":  { "url": "http://localhost:8300" },
  "blob":     { "url": "http://localhost:8400" }
}
```

这种严格校验的设计保证了所有服务在启动前就能发现配置错误，避免运行时因错误的 URL 导致级联故障。

## HTTP 客户端

novaic-common 基于 httpx 封装了异步 HTTP 客户端，为服务间通信提供统一的调用方式。

**核心特性：**

- **异步优先** — 所有客户端方法均为 `async`，基于 httpx 的 `AsyncClient`
- **连接复用** — 客户端实例维持连接池，减少 TCP 握手开销
- **超时配置** — 统一的超时策略，支持按调用场景覆盖
- **错误处理** — 标准化的异常封装，屏蔽 httpx 底层错误细节

**EntangledServiceClient** 是一个专用的 WebSocket 客户端，用于与 Entangled 服务建立持久长连接，支持实体同步和实时事件推送。它封装了 WebSocket 协议细节，对上层提供消息级别的收发接口。

## Contract 模块

共享库包含 **9 个 contract 模块**，以 Python 数据类（dataclass 或 Pydantic model）的形式定义了服务间交互的数据结构。

这些 contract 充当服务间的「协议边界」：

| 序号 | 模块职责 | 说明 |
|-----|---------|------|
| 1 | Agent 契约 | Agent 实体的创建、更新、状态表示 |
| 2 | Message 契约 | 消息结构、角色定义、附件格式 |
| 3 | Tool 契约 | 工具调用请求与响应格式 |
| 4 | Session 契约 | 会话生命周期相关结构 |
| 5 | Device 契约 | 设备信息与状态数据 |
| 6 | Blob 契约 | 二进制对象的引用与元数据 |
| 7 | Skill 契约 | 技能定义与配置结构 |
| 8 | Sync 契约 | 实体同步的增量变更格式 |
| 9 | Event 契约 | 系统事件的标准化表示 |

所有服务共同引用这些 contract 模块，确保序列化与反序列化的一致性，避免手工维护重复的数据结构定义。

## LLM 内建工具定义

novaic-common 中定义了 **5 个 LLM 内建工具**（builtin tools），这些工具以标准的 JSON Schema 格式声明，供 LLM 在推理过程中按需调用。

内建工具特点：

- **声明式定义** — 每个工具包含名称、描述、参数 schema
- **平台内置** — 不依赖外部 MCP server，由 Runtime 直接执行
- **跨模型兼容** — 工具定义遵循通用的 function calling 规范

这些工具定义在 Runtime 构建 LLM 请求时被自动注入到工具列表中，LLM 可根据上下文选择调用。

## Wake Assembler

Wake Assembler 负责消息的组装流程，将多源输入整合为 LLM 可消费的完整消息序列。

**组装过程：**

```
上下文窗口
  │
  ├── 系统提示词（system prompt）
  ├── 历史消息（history messages）
  ├── 工具结果（tool results）
  ├── 用户最新输入（user input）
  └── 附加上下文（context injections）
        │
        ▼
  Wake Assembler ──► 完整的 messages 数组 ──► LLM API
```

Assembler 的核心价值在于封装了消息拼接的复杂逻辑，包括令牌预算控制、消息截断策略、角色交替合规等，使上层调用者无需关心这些细节。
