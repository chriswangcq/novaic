# Novaic 项目文档

## 快速开始

- 系统全景 → [overview.md](overview.md)
- 本地开发 → [runbooks/local-development.md](runbooks/local-development.md)
- 云端部署 → [runbooks/deploy.md](runbooks/deploy.md)

## 文档导航

### 总览

| 文档 | 内容 |
|------|------|
| [系统总览](overview.md) | 技术栈、服务拓扑、子模块清单、数据流概览 |

### 服务架构

| 文档 | 服务 | 端口 |
|------|------|------|
| [Agent Runtime](services/agent-runtime.md) | Agent 执行引擎 + Queue Service | :19997 |
| [Cortex](services/cortex.md) | 上下文管理 | :19996 |
| [Business](services/business.md) | 实体管理 + Action Hooks | :19998 |
| [Gateway](services/gateway.md) | API 网关 | :19999 |
| [Device](services/device.md) | 设备管理 | :19993 |
| [LLM Factory](services/llm-factory.md) | 模型路由 | :9100 |
| [Sandbox Service](services/sandbox-service.md) | 进程隔离执行 | :19994 |
| [Blob Service](services/blob-service.md) | 对象存储 | :19995 |
| [Entangled](services/entangled.md) | 实体同步 | :19900 |
| [VmControl](services/vmcontrol.md) | 设备控制 | 嵌入式 |

### 库与工具

| 文档 | 模块 |
|------|------|
| [Common](libraries/common.md) | 共享库（配置、客户端、契约、工具） |
| [LogicalFS](libraries/logicalfs.md) | 文件系统抽象 |
| [MCP-VMUSE](libraries/mcp-vmuse.md) | VM 内桌面控制工具 |

### 客户端

| 文档 | 模块 |
|------|------|
| [App](client/app.md) | Tauri + React 桌面/移动客户端 |

### 跨服务架构

| 文档 | 主题 |
|------|------|
| [Agent 执行链路](architecture/agent-execution-pipeline.md) | 从用户消息到工具执行的完整数据流 |
| [Entangled 同步协议](architecture/entangled-sync-protocol.md) | 实体同步协议与数据流 |
| [WebRTC 显示管线](architecture/webrtc-display-pipeline.md) | 屏幕捕获到前端渲染 |
| [认证与身份](architecture/auth-and-identity.md) | 双 JWT 认证体系 |
| [服务间通信](architecture/service-communication.md) | HTTP/WS/消息传递模式 |
| [Generic Worker Substrate](architecture/generic-worker-substrate-plan.md) | Worker 基底计划 |

### 运维手册

| 文档 | 内容 |
|------|------|
| [本地开发](runbooks/local-development.md) | 环境搭建与启动指南 |
| [云端部署](runbooks/deploy.md) | 部署流程 |
| [故障排查](runbooks/troubleshooting.md) | 常见问题排查 |

### 参考

| 文档 | 内容 |
|------|------|
| [API 路由表](reference/api-routes.md) | 全服务路由汇总 |
| [端口与配置](reference/ports-and-config.md) | 端口清单、services.json |
| [环境变量](reference/environment-variables.md) | 环境变量参考 |

### 路线图

| 文档 | 内容 |
|------|------|
| [实体模型重构](roadmap/model-entity-refactor.md) | Model-Entity 重构计划 |
| [DSL Phase Bill](roadmap/tickets/PR-338-business-only-dsl-phase-bill.md) | Business DSL 阶段票据 |
