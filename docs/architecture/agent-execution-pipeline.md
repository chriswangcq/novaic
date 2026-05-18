# Agent 执行链路全景

本文档描述一条用户消息从发送到工具执行、结果返回的完整数据流，横跨 App、Gateway、Business、Queue Service、Agent Runtime、Cortex、Device/Sandbox 等多个服务。

## 链路总览

```
用户输入                                                          结果展示
  │                                                                 ▲
  ▼                                                                 │
┌──────┐  HTTP   ┌─────────┐  HTTP   ┌──────────┐  HTTP   ┌───────────┐
│ App  │────────►│ Gateway │────────►│ Business │────────►│  Queue    │
│Tauri │         │ :19999  │         │ :19998   │         │  Service  │
└──────┘         └─────────┘         └──────────┘         │  :19997  │
                                                          └─────┬─────┘
                                                                │ spawn
                                                          ┌─────▼─────┐
                                                          │  Agent    │
                                                          │  Runtime  │
                                                          └──┬──┬──┬──┘
                                              ┌──────────────┘  │  └───────────────┐
                                              ▼                 ▼                  ▼
                                         ┌─────────┐    ┌────────────┐     ┌────────────┐
                                         │ Cortex  │    │ LLM Factory│     │  Device /  │
                                         │ :19996  │    │   :9100    │     │  Sandbox   │
                                         └─────────┘    └────────────┘     └────────────┘
```

## 消息发送与调度

用户消息从客户端到后端执行引擎的完整调度链路：

| 步骤 | 服务 | 动作 | 说明 |
|------|------|------|------|
| 1 | App (Tauri) | 用户输入消息，触发 dispatch | React 前端通过 Tauri IPC 发送到 Rust 侧 |
| 2 | Gateway :19999 | HTTP 代理 + JWT 校验 | 验证 Clerk RS256 或内部 HS256 Token |
| 3 | Business :19998 | message action hook | 创建消息记录，确定 Agent 上下文，组装任务参数 |
| 4 | Queue Service :19997 | 创建 task | 将任务写入队列，分配 task_id，标记状态为 pending |
| 5 | Agent Runtime | Worker dispatch | Queue Service spawn 对应 worker 进程执行任务 |

消息到达 Business 后，message action hook 负责：
- 校验 Agent 状态和权限
- 加载 Agent 配置（系统提示词、工具集合等）
- 构造 task payload（包含 conversation_id、message、tools 列表）
- 调用 Queue Service 创建任务

## Worker 执行流程

Agent Runtime 通过 Queue Service 的 worker dispatch 机制接收并执行任务。核心 worker 类型如下：

| Worker 类型 | 职责 | 调用链 |
|-------------|------|--------|
| `react_loop` | 主推理循环，LLM 多轮 reasoning + tool use | LLM Factory → 工具执行 → 循环 |
| `shell_execute` | 在设备或沙箱中执行 shell 命令 | Device Service 或 Sandbox Service |
| `observe_screen` | 截取设备屏幕，进行视觉感知 | Device → VmControl → 截图 → LLM 分析 |
| `perception_action` | 视觉感知 + 操作的组合 worker | 截图 → LLM 推理 → 鼠标/键盘操作 |
| `shell_display` | 带屏幕观察的 shell 执行 | shell_execute + observe_screen 组合 |
| `mcp_tool` | MCP 协议工具调用 | MCP Server → 工具执行 → 结果返回 |

### react_loop 主循环

```
┌──────────────────────────────────────────────────┐
│                  react_loop                       │
│                                                   │
│   ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│   │ 构建上下文 │───►│ LLM 推理  │───►│ 解析响应 │  │
│   │ (Cortex) │    │(LLM Fac.) │    │          │  │
│   └──────────┘    └───────────┘    └─────┬────┘  │
│        ▲                                 │       │
│        │          ┌───────────┐          ▼       │
│        │          │ 结果写入   │    ┌──────────┐  │
│        └──────────│  Cortex   │◄───│ 工具执行 │  │
│                   └───────────┘    └──────────┘  │
│                                                   │
│   循环终止条件：LLM 返回最终回复 / 达到最大轮次 /    │
│   出现不可恢复错误                                 │
└──────────────────────────────────────────────────┘
```

## 工具调用链路

工具执行根据目标环境分为两条路径：

### 路径 A：Device Service 执行（远程设备）

```
Agent Runtime → Device Service :19993 → VmControl (WS) → 目标设备
                                                         ├── LinuxVm（RFB/VNC）
                                                         ├── Android（scrcpy）
                                                         └── HostDesktop（native）
```

- shell 命令通过 Device Service HTTP API 下发
- VmControl 通过 WebSocket typed commands 与设备通信
- 屏幕操作（点击、输入、滚动）通过 DataChannel 输入管线

### 路径 B：Sandbox Service 执行（隔离沙箱）

```
Agent Runtime → Sandbox Service → 沙箱容器（隔离执行环境）
```

- 文件操作、代码执行等可在沙箱中安全运行
- 沙箱提供文件系统隔离和资源限制

### LLM Factory 调用

Agent Runtime 向 LLM Factory :9100 发起推理请求：
- 携带完整 prompt（系统提示 + 上下文 + 用户消息 + 工具定义）
- LLM Factory 管理多模型路由、API key 池、速率控制
- 返回结构化响应：文本回复或 tool_use 调用

## Cortex 上下文管理

Cortex :19996 是整个执行链路的上下文中枢，负责：

| 功能 | 说明 |
|------|------|
| ContextEvent 记录 | 每次工具调用、LLM 响应均写入 ContextEvent，形成完整审计日志 |
| Token 预算压缩 | 当上下文超过 token 预算时，自动压缩历史消息（摘要 / 截断） |
| Scope Lock | 基于 Redis 的分布式锁，防止同一 scope 下多个 worker 并发写入冲突 |
| 上下文装配 | 为 react_loop 组装完整的 LLM 输入（系统提示 + conversation 历史 + 工具结果） |
| Blob 外化 | 大对象（截图、文件内容）外化到 Blob Service :19995，Cortex 仅存储引用 |

## 错误处理与重试

### 错误分级

| 级别 | 场景 | 处理策略 |
|------|------|---------|
| 可恢复 | LLM 请求超时、速率限制 | 指数退避重试（最多 3 次） |
| 工具失败 | shell 命令非零退出、设备断连 | 将错误信息写入 Cortex，由 LLM 决定下一步 |
| 不可恢复 | 认证失败、服务不可达 | 标记 task 为 failed，通知上游 |

### 结果返回路径

```
Agent Runtime  ──写入结果──►  Cortex
                              │
Queue Service  ◄──任务完成────┘
    │
Business  ◄──状态回调────────
    │
Entangled  ◄──实体同步──────
    │
App (React)  ◄──Sync 帧─────  UI 更新
```

最终结果通过 Entangled 同步协议推送到客户端：Agent Runtime 写入 Cortex → Queue Service 标记完成 → Business 更新实体 → Entangled Sync 帧推送 → App SQLite 更新 → React Query 失效 → UI 渲染。
