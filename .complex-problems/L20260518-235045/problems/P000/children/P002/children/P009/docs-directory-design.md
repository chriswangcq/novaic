# 新文档目录结构设计

## 设计原则

1. **层级清晰**：总览 → 服务架构 → 跨服务主题 → 运维手册 → 参考
2. **一服务一文档**：每个子模块一个独立的架构文档
3. **跨服务主题独立**：Entangled 同步、Agent 执行链路、WebRTC 管线等跨多服务的主题单独成文
4. **CI 兼容**：保留 CI guard 脚本预期的文件路径
5. **全中文**：文档内容用中文编写，文件名用英文 kebab-case

## 目录结构

```
docs/
├── README.md                                    # 文档总入口与导航
├── overview.md                                  # 系统总览：愿景、技术栈、服务拓扑图
│
├── services/                                    # 各服务架构文档（一服务一文件）
│   ├── agent-runtime.md                         # Agent Runtime + Queue Service
│   ├── cortex.md                                # Cortex 上下文管理
│   ├── business.md                              # Business 实体管理 + Action Hooks
│   ├── gateway.md                               # Gateway API 网关
│   ├── device.md                                # Device 设备管理
│   ├── llm-factory.md                           # LLM Factory Provider 路由
│   ├── sandbox-service.md                       # Sandbox Service 进程隔离
│   ├── blob-service.md                          # Blob Service 对象存储
│   ├── entangled.md                             # Entangled 实体同步服务
│   └── vmcontrol.md                             # VmControl 设备控制
│
├── libraries/                                   # 库与工具模块
│   ├── common.md                                # novaic-common 共享库
│   ├── logicalfs.md                             # LogicalFS 文件系统抽象
│   └── mcp-vmuse.md                             # MCP-VMUSE VM 内桌面控制
│
├── client/                                      # 客户端架构
│   └── app.md                                   # novaic-app Tauri + React 客户端
│
├── architecture/                                # 跨服务架构主题
│   ├── agent-execution-pipeline.md              # Agent 执行链路全景
│   ├── entangled-sync-protocol.md               # Entangled 同步协议与数据流
│   ├── webrtc-display-pipeline.md               # WebRTC 显示管线
│   ├── auth-and-identity.md                     # 认证与身份体系
│   ├── generic-worker-substrate-plan.md         # [CI 保留] Generic Worker Substrate 计划
│   └── service-communication.md                 # 服务间通信模式
│
├── runbooks/                                    # 运维手册
│   ├── local-development.md                     # 本地开发环境搭建
│   ├── deploy.md                                # [CI 保留] 云端部署流程
│   └── troubleshooting.md                       # 故障排查手册
│
├── reference/                                   # 参考文档
│   ├── api-routes.md                            # 全服务 API 路由表
│   ├── ports-and-config.md                      # 端口清单与配置参考
│   └── environment-variables.md                 # 环境变量参考
│
└── roadmap/                                     # 路线图与变更记录
    ├── model-entity-refactor.md                 # [CI 保留] 实体模型重构
    └── tickets/
        └── PR-338-business-only-dsl-phase-bill.md  # [CI 保留] DSL Phase Bill
```

## 文件详细设计

### 总览层

#### 1. `docs/README.md`
**职责**：文档总入口，提供导航索引和快速查找指引
**大纲**：
- ## 文档导航
- ## 快速开始
- ## 文档组织说明

#### 2. `docs/overview.md`
**职责**：系统全景介绍，包括愿景、技术栈、服务拓扑图、子模块清单
**大纲**：
- ## 系统简介
- ## 技术栈
- ## 服务拓扑
- ## 子模块一览
- ## 数据流概览

---

### 服务架构层（docs/services/）

#### 3. `docs/services/agent-runtime.md`
**职责**：Agent Runtime 服务架构，含 Queue Service
**大纲**：
- ## 概述与职责
- ## 进程角色与启动方式
- ## Worker 类型清单
- ## Saga/Task 处理流程
- ## Queue Service 架构
- ## API 路由
- ## 依赖关系

#### 4. `docs/services/cortex.md`
**职责**：Cortex 上下文管理服务架构
**大纲**：
- ## 概述与职责
- ## 核心模块划分
- ## ContextEvent 模型
- ## Token Budget 压缩策略
- ## Scope Lock 机制
- ## API 路由
- ## 依赖关系

#### 5. `docs/services/business.md`
**职责**：Business 实体管理服务架构
**大纲**：
- ## 概述与职责
- ## 双进程架构（API + Subscriber）
- ## Entity Schema 与 Action Hooks
- ## DispatchSubscriber 机制
- ## Internal API 路由
- ## 依赖关系

#### 6. `docs/services/gateway.md`
**职责**：Gateway API 网关服务架构
**大纲**：
- ## 概述与职责
- ## 认证体系（双 JWT）
- ## 路由结构
- ## WebSocket 信令
- ## Blob 代理
- ## 依赖关系

#### 7. `docs/services/device.md`
**职责**：Device 设备管理服务架构
**大纲**：
- ## 概述与职责
- ## 类型化命令 WebSocket 协议
- ## 设备类型（linux/android/host_desktop）
- ## Mounted Tools 系统
- ## API 路由
- ## 依赖关系

#### 8. `docs/services/llm-factory.md`
**职责**：LLM Factory 模型路由服务架构
**大纲**：
- ## 概述与职责
- ## Provider 路由机制
- ## API Key 加密存储
- ## 重试策略
- ## API 路由
- ## 依赖关系

#### 9. `docs/services/sandbox-service.md`
**职责**：Sandbox Service 进程隔离服务架构
**大纲**：
- ## 概述与职责
- ## AsyncProcessRunner 机制
- ## Mount Namespace 隔离
- ## API 路由
- ## 依赖关系

#### 10. `docs/services/blob-service.md`
**职责**：Blob Service 对象存储服务架构
**大纲**：
- ## 概述与职责
- ## 双 API 体系（blob:// + object tree）
- ## 存储后端（Disk + OSS）
- ## Multipart 上传协议
- ## API 路由
- ## 依赖关系

#### 11. `docs/services/entangled.md`
**职责**：Entangled 实体同步服务架构
**大纲**：
- ## 概述与职责
- ## Entity Schema 与 Store 类型
- ## WS 同步协议
- ## 服务端架构
- ## 依赖关系

#### 12. `docs/services/vmcontrol.md`
**职责**：VmControl 设备控制模块架构
**大纲**：
- ## 概述与职责
- ## 嵌入式服务架构
- ## WebRTC 连接管理
- ## Scrcpy 集成
- ## Cloud Bridge 协议
- ## 设备类型统一
- ## API 路由
- ## 依赖关系

---

### 库与工具层（docs/libraries/）

#### 13. `docs/libraries/common.md`
**职责**：novaic-common 共享库文档
**大纲**：
- ## 概述与职责
- ## ServiceConfig 配置加载
- ## HTTP 客户端
- ## Contract 模块
- ## LLM 内建工具定义
- ## Wake Assembler

#### 14. `docs/libraries/logicalfs.md`
**职责**：LogicalFS 文件系统抽象库文档
**大纲**：
- ## 概述与职责
- ## Snapshot/Authority/Store 抽象
- ## BlobObjectStore 适配器
- ## 使用方式

#### 15. `docs/libraries/mcp-vmuse.md`
**职责**：MCP-VMUSE VM 内桌面控制工具文档
**大纲**：
- ## 概述与职责
- ## 服务架构
- ## 工具清单（Desktop/Browser/Shell/File/Window/Context）
- ## 配置
- ## 与 VmControl 的集成

---

### 客户端层（docs/client/）

#### 16. `docs/client/app.md`
**职责**：novaic-app 桌面/移动客户端架构文档
**大纲**：
- ## 概述与技术栈
- ## React 组件结构
- ## Tauri 命令体系
- ## 状态管理（Zustand + TanStack Query）
- ## 路由机制
- ## Entangled 客户端集成
- ## 前后端通信架构

---

### 跨服务架构主题（docs/architecture/）

#### 17. `docs/architecture/agent-execution-pipeline.md`
**职责**：Agent 执行链路全景，从用户消息到工具执行的完整数据流
**大纲**：
- ## 链路总览
- ## 消息发送与调度
- ## Worker 执行流程
- ## 工具调用链路
- ## Cortex 上下文管理
- ## 错误处理与重试

#### 18. `docs/architecture/entangled-sync-protocol.md`
**职责**：Entangled 同步协议与数据流的跨服务视角
**大纲**：
- ## 协议总览
- ## 服务端（Entangled 服务）
- ## 客户端（Rust crate）
- ## WS 消息格式
- ## 悲观写入 + 乐观展示
- ## 实体注册与同步合约

#### 19. `docs/architecture/webrtc-display-pipeline.md`
**职责**：WebRTC 显示管线，从屏幕捕获到前端渲染
**大纲**：
- ## 管线总览
- ## 信令流程（Gateway → AppBridge → VmControl）
- ## 视频编码（VNC/Scrcpy/HostDesktop → H.264）
- ## Broadcaster 架构
- ## DataChannel 输入管线
- ## 设备类型差异

#### 20. `docs/architecture/auth-and-identity.md`
**职责**：认证与身份体系全景
**大纲**：
- ## 认证架构总览
- ## 外部认证（Clerk RS256）
- ## 内部认证（HS256 JWT）
- ## 客户端 Token 管理
- ## 服务间认证

#### 21. `docs/architecture/generic-worker-substrate-plan.md`
**职责**：[CI 保留] Generic Worker Substrate 计划文档
**大纲**：保留现有内容，确保 CI marker 存在

#### 22. `docs/architecture/service-communication.md`
**职责**：服务间通信模式与拓扑
**大纲**：
- ## 通信模式总览
- ## HTTP 调用关系
- ## WebSocket 通道
- ## 消息传递模式
- ## 端口与服务发现（services.json）

---

### 运维手册（docs/runbooks/）

#### 23. `docs/runbooks/local-development.md`
**职责**：本地开发环境搭建指南
**大纲**：
- ## 前置条件
- ## 子模块初始化
- ## 服务启动顺序
- ## 常用开发命令
- ## 调试技巧

#### 24. `docs/runbooks/deploy.md`
**职责**：[CI 保留] 云端部署流程
**大纲**：保留现有内容，确保 CI marker 存在

#### 25. `docs/runbooks/troubleshooting.md`
**职责**：常见故障排查手册
**大纲**：
- ## 服务启动失败
- ## 连接问题
- ## Agent 执行异常
- ## WebRTC 连接失败
- ## Entangled 同步异常

---

### 参考文档（docs/reference/）

#### 26. `docs/reference/api-routes.md`
**职责**：全服务 API 路由汇总表
**大纲**：
- ## 路由表格式说明
- ## Gateway 路由
- ## Business 路由
- ## Cortex 路由
- ## Queue Service 路由
- ## Device 路由
- ## 其他服务路由

#### 27. `docs/reference/ports-and-config.md`
**职责**：端口清单与服务配置参考
**大纲**：
- ## 端口清单
- ## services.json 配置说明
- ## ServiceConfig 加载机制

#### 28. `docs/reference/environment-variables.md`
**职责**：环境变量参考
**大纲**：
- ## 全局环境变量
- ## 各服务特定环境变量
- ## 开发 vs 生产配置差异

---

### 路线图（docs/roadmap/）

#### 29. `docs/roadmap/model-entity-refactor.md`
**职责**：[CI 保留] 实体模型重构文档
**大纲**：需创建，确保 CI lint_current_docs_residue.sh 扫描通过

#### 30. `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md`
**职责**：[CI 保留] DSL Phase Bill 票据
**大纲**：保留现有内容

---

## 文件统计

| 类别 | 文件数 |
|------|--------|
| 总览 | 2 |
| 服务架构 | 10 |
| 库与工具 | 3 |
| 客户端 | 1 |
| 跨服务架构 | 6 |
| 运维手册 | 3 |
| 参考文档 | 3 |
| 路线图 | 2 |
| **合计** | **30** |

## CI 兼容性

以下文件路径被 CI guard 脚本引用，必须保留：

1. `docs/architecture/generic-worker-substrate-plan.md` — lint_docs_status_consistency.py 检查 marker
2. `docs/runbooks/deploy.md` — lint_deploy_fresh_smoke.py 检查 marker
3. `docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md` — lint_docs_status_consistency.py 检查 marker
4. `docs/roadmap/model-entity-refactor.md` — lint_current_docs_residue.sh 扫描目标

这 4 个文件需保留或创建，且内容中的 CI marker 必须匹配脚本期望。
