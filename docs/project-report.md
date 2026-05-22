# NovAIC 项目报告

> 生成日期：2026-05-23  
> 统计口径：基于当前工作区快照；排除 `node_modules/`、`.venv/`、`target/`、`dist/`、`build/`、缓存目录、锁文件和明显生成文件。行数统计覆盖 `.py`、`.ts`、`.tsx`、`.js`、`.rs`、`.html`、`.css`、`.md`、`.toml`、`.sh` 等源码、脚本与文档文件，属于工程规模估算，不等同于最终发行包体积。

## 1. 项目定位

NovAIC 是一个面向真实设备与虚拟环境的 AI Agent 平台。它不是单纯的聊天应用，也不是只在云端容器里运行命令的托管 Agent。项目的核心目标是让 Agent 能够进入用户的计算环境，观察屏幕、理解上下文、调用工具、控制设备，并把执行过程沉淀成可审计、可恢复、可同步的长期工作轨迹。

从产品形态看，NovAIC 覆盖三类能力：

| 能力 | 说明 |
| --- | --- |
| Agent 创建与运行 | 用户可以创建 Agent，配置模型、工具、上下文和绑定设备，由 Runtime 驱动推理循环与工具调用。 |
| 设备绑定与远程控制 | Agent 可以通过 Device / VmControl 操作 Linux VM、Android、Host Desktop 等目标环境。 |
| 多端产品体验 | 桌面/移动客户端通过 Entangled 同步产品状态，通过 WebRTC/Scrcpy/VNC 展示远程画面与执行过程。 |

项目更准确的定位可以概括为：

> NovAIC 是一个 agent-native computer platform：为 Agent 提供真实设备、虚拟机、沙箱、文件系统、上下文轨迹和多端控制面的执行底座。

## 2. 系统整体架构

NovAIC 采用多服务、强边界、事件驱动的架构。系统由客户端、网关、业务实体层、队列/运行时、上下文层、设备层、对象存储、沙箱、模型路由和同步引擎共同组成。

核心服务拓扑如下：

```text
App / Tauri
  |
  v
Gateway
  |
  v
Business  <->  Entangled
  |
  v
Queue Service  ->  Agent Runtime
                   |      |      |
                   v      v      v
                Cortex  LLM   Device / Sandbox
                   |             |
                   v             v
                 Blob        VmControl / VM / Android / Desktop
```

架构上可以分为六层：

| 层级 | 主要模块 | 职责 |
| --- | --- | --- |
| 产品交互层 | `novaic-app` | 桌面/移动客户端、聊天、Agent Monitor、设备画面、Entangled 本地缓存。 |
| 边缘入口层 | `novaic-gateway` | 外部 API、JWT 鉴权、WebSocket、Blob 代理、WebRTC 信令。 |
| 产品语义层 | `novaic-business` | Agent、设备、消息、环境、配置等业务实体与 Action Hooks。 |
| 执行编排层 | `novaic-agent-runtime` | Queue Service、Worker、Session/Saga/Task 生命周期、LLM 调用、工具分发。 |
| 工作轨迹层 | `novaic-cortex`、`novaic-blob-service`、`novaic-logicalfs` | ContextEvent、Scope、摘要、Blob 引用、文件系统快照与大对象外化。 |
| 执行环境层 | `novaic-device`、`novaic-sandbox-service`、`novaic-mcp-vmuse`、`novaic-quic-service`、`VmControl` | 真实设备、VM、沙箱、MCP 工具、远程画面与输入通道。 |

这套架构的关键特点是：产品状态、Agent 工作轨迹、工具执行结果、设备状态分别有明确归属，避免把所有状态塞进一个聊天上下文或一个调试接口里。

## 3. 核心执行链路

一次用户消息从客户端到 Agent 执行，大致经过以下路径：

```text
用户消息
  -> App
  -> Gateway
  -> Business action hook
  -> Queue Service
  -> Agent Runtime Worker
  -> LLM Factory
  -> Cortex context assembly
  -> Device / Sandbox / MCP tool
  -> Cortex observation
  -> Business / Entangled projection
  -> App UI update
```

这条链路体现了 NovAIC 的几个设计选择：

1. **业务实体与执行轨迹分离**  
   Business 负责产品语义，例如 Agent、消息、设备、环境通知；Cortex 负责 Agent 的工作轨迹，例如 action、observation、reasoning trace、scope summary。

2. **Agent Runtime 专注执行**  
   Runtime 负责 Queue、Session、Saga、Task、Worker、LLM 调用和工具分发。它不是产品数据库，也不是设备状态源。

3. **大对象外化**  
   截图、文件、工具大输出等不直接塞进 Cortex 或前端日志，而是进入 Blob Service；Cortex 与 Agent Monitor 保存引用和摘要。

4. **设备控制是一级能力**  
   工具调用可以走 Sandbox，也可以走 Device Service。Device 再通过 VmControl 操作 Linux VM、Android 或 Host Desktop。

5. **前端读取投影状态**  
   App 尽量读取 Entangled 投影实体，而不是绕过业务层直接读 Cortex 调试接口。这让产品 UI 和后端状态更容易稳定。

## 4. 关键模块说明

### 4.1 novaic-app

`novaic-app` 是 Tauri 2 + React + TypeScript 客户端，承担桌面与移动端用户体验。它包含聊天界面、Agent Monitor、设备视图、模型/技能/设备配置、Entangled 本地缓存、Tauri IPC、WebRTC 展示等能力。

工程意义上，App 不是普通网页壳。它连接了本地安全存储、Rust bridge、远程输入、屏幕渲染、实体同步和 Agent 活动投影，是用户理解 Agent 执行过程的主要控制面。

### 4.2 novaic-agent-runtime

`novaic-agent-runtime` 是执行引擎，包含 Queue Service 和 Agent Runtime Worker。它承担：

- `react_loop` 主推理循环
- `shell_execute` 命令执行
- `observe_screen` 屏幕观察
- `perception_action` 感知-动作闭环
- `mcp_tool` MCP 工具调用
- Session / Saga / Task / Worker lease 等生命周期状态机

该模块测试体量最大，说明项目在执行可靠性、状态机迁移、恢复路径和边界清理上投入很重。

### 4.3 novaic-cortex

`novaic-cortex` 是 Agent 工作轨迹中心，负责 ContextEvent、Scope tree、Scope Lock、上下文装配、Token 预算压缩、摘要、payload manifest 和 Blob 引用。它不是业务记忆库，而是 Agent 执行过程的可审计轨迹层。

Cortex 的价值在于把“Agent 做了什么、看到什么、为什么下一步这么做”固化成结构化轨迹，而不是只留下聊天回复。

### 4.4 novaic-business

`novaic-business` 负责产品实体与业务 Action Hooks，包括 Agent、设备、消息、API key、模型配置、技能、环境通知等。它是产品语义的权威层，也是 Entangled schema 与实体注册的重要入口。

它和 Runtime/Cortex 的边界非常关键：Business 决定“产品上发生了什么”，Runtime 决定“执行怎么跑”，Cortex 记录“执行轨迹是什么”。

### 4.5 novaic-gateway

`novaic-gateway` 是边缘基础设施，负责外部 HTTP/WS、鉴权、App WebSocket、Blob proxy、WebRTC 信令、同步端点发现等。设计原则上 Gateway 不做业务编排，也不做 schema authority。

### 4.6 novaic-device 与 VmControl

`novaic-device` 管理设备实体、typed command、工具挂载、设备状态和 Device <-> Business/Gateway 的边界。VmControl 则负责宿主机与目标环境的实际操作，包括 QEMU、Scrcpy、键鼠输入、屏幕捕获和 WebRTC 显示管线。

这是 NovAIC 和普通托管 Agent 平台最明显的差异：Agent 不只是能在容器里执行命令，还能操作真实桌面、移动设备和 VM。

### 4.7 novaic-llm-factory

`novaic-llm-factory` 管理 LLM Provider 路由、模型选择、API key 加密和多模型接入。它让平台不绑定单一模型供应商，保留 OpenAI、Anthropic、Google 等多模型切换空间。

### 4.8 novaic-blob-service 与 LogicalFS

`novaic-blob-service` 负责对象存储、multipart upload/download、S3/OSS 后端和生命周期。`novaic-logicalfs` 在其上提供 Snapshot / Authority / Store 抽象，让 Agent 工作区具备可冻结、可回放、可替换存储后端的文件系统语义。

### 4.9 novaic-mcp-vmuse

`novaic-mcp-vmuse` 是 VM 内桌面控制工具层，通过 Python/aiohttp、xdotool、Playwright 等能力暴露屏幕、输入、文件、浏览器等工具端点。它是 Agent 进入 VM 桌面环境的重要桥。

### 4.10 Entangled

`Entangled` 提供实体同步协议和本地缓存机制，让 App 能够通过增量同步拿到产品状态。它支撑多端一致性，也降低 App 对后端内部调试接口的耦合。

## 5. 代码工作量统计

当前源码口径统计约为：

| 指标 | 数量 |
| --- | ---: |
| 统计文件数 | 约 1,274 个 |
| 统计总行数 | 约 214,872 行 |
| 测试相关文件 | 约 412 个 |
| 测试相关行数 | 约 53,393 行 |

按模块拆分：

| 模块 | 文件数 | 行数 | 测试相关文件 | 测试相关行数 |
| --- | ---: | ---: | ---: | ---: |
| `novaic-app` | 375 | 71,552 | 23 | 2,086 |
| `novaic-agent-runtime` | 312 | 50,985 | 179 | 24,824 |
| `novaic-cortex` | 133 | 24,647 | 88 | 12,834 |
| `Entangled` | 69 | 14,301 | 21 | 3,449 |
| `novaic-business` | 76 | 12,828 | 37 | 4,304 |
| `novaic-common` | 73 | 8,510 | 29 | 2,638 |
| `novaic-device` | 30 | 5,734 | 7 | 329 |
| `novaic-mcp-vmuse` | 17 | 5,274 | 1 | 51 |
| `novaic-llm-factory` | 17 | 4,388 | 2 | 576 |
| `novaic-gateway` | 34 | 3,372 | 10 | 474 |
| `novaic-blob-service` | 20 | 3,163 | 5 | 942 |
| `scripts` | 40 | 2,925 | 3 | 239 |
| `docs` | 30 | 3,891 | 0 | 0 |
| `novaic-quic-service` | 14 | 1,081 | 0 | 0 |
| `novaic-logicalfs` | 10 | 953 | 3 | 290 |
| `novaic-sandbox-service` | 9 | 551 | 3 | 260 |
| `novaic-sandbox-sdk` | 7 | 377 | 1 | 97 |
| `byclaw-website` | 8 | 340 | 0 | 0 |

按语言/文件类型拆分：

| 类型 | 文件数 | 行数 |
| --- | ---: | ---: |
| Python (`.py`) | 853 | 144,624 |
| Rust (`.rs`) | 116 | 31,174 |
| TSX (`.tsx`) | 73 | 19,654 |
| TypeScript (`.ts`) | 99 | 8,898 |
| Markdown (`.md`) | 45 | 4,278 |
| Shell (`.sh`) | 61 | 3,884 |
| HTML (`.html`) | 4 | 1,074 |
| TOML (`.toml`) | 15 | 612 |
| CSS (`.css`) | 4 | 538 |
| JavaScript (`.js`) | 4 | 136 |

从工作量分布看，后端 Python 服务和执行可靠性测试是项目主体；客户端与 Rust/Tauri/VmControl 组成第二大投入；文档、脚本、部署与边界 lint 构成工程治理层。

## 6. 工程成熟度观察

项目不是一个单体 Demo，而是已经演化出较完整的工程治理方式：

1. **服务边界明确**  
   Business、Runtime、Cortex、Gateway、Device、Blob 等职责有清晰划分，文档中也持续强调“谁是状态源”。

2. **大量迁移与守卫测试**  
   Runtime 和 Cortex 的测试中包含大量 PR 编号型 guardrail，用来防止旧路径、旧字段、旧状态机逻辑回流。这说明项目经历过多轮架构迁移，而不是一次性脚手架。

3. **状态机化趋势明显**  
   Queue、Session、Saga、Task、Worker lease、message lifecycle 等都在向显式 FSM / ledger / outbox 迁移，目标是提升恢复能力和可审计性。

4. **大对象处理有专门策略**  
   Blob Service、LogicalFS、payload ref、Agent Monitor 摘要等设计避免了工具输出和截图污染上下文。

5. **设备执行闭环复杂但有差异化**  
   WebRTC、Scrcpy、VmControl、MCP-VMUSE、Device typed commands 组成真实环境控制链路，这部分复杂度高，但也是项目的技术差异来源。

## 7. 与普通 Managed Agent 平台的差异

普通 Managed Agent 平台通常解决的是：

- 帮开发者托管 Agent loop
- 给 Agent 一个云端容器
- 内置 bash、文件、web、MCP 工具
- 管理 session、上下文、日志和权限

NovAIC 的目标更靠近：

- 让 Agent 绑定和操作真实设备
- 让用户通过客户端看到 Agent 的执行过程
- 让执行轨迹进入 Cortex 和产品状态投影
- 让工具结果、屏幕、文件和长期工作区有结构化归属
- 让平台不绑定单一模型供应商

因此 NovAIC 不应被包装成“另一个 Managed Agent”。更准确的差异化叙事是：

> Managed Agent 让模型在云端环境中执行任务；NovAIC 让 Agent 进入用户的计算环境并持续工作。

## 8. 当前优势

| 优势 | 说明 |
| --- | --- |
| 真实设备控制 | 支持 Linux VM、Android、Desktop 等执行目标，具备屏幕观察和输入操作能力。 |
| 多模型底座 | LLM Factory 让平台不被单一模型供应商锁死。 |
| 复杂任务轨迹 | Cortex 让 Agent 的行动、观察、推理和摘要进入结构化轨迹。 |
| 产品状态同步 | Entangled 支撑 App 端实体同步和本地缓存，而不是只依赖一次性 API 响应。 |
| 工程防回归意识强 | 大量测试和 lint guard 防止旧路径回流。 |
| 控制面潜力大 | Tauri App + WebRTC + Agent Monitor 可以形成比普通控制台更强的用户体验。 |

## 9. 当前风险与短板

| 风险 | 说明 | 建议 |
| --- | --- | --- |
| 系统复杂度高 | 多服务、多协议、多状态源，部署与排障门槛高。 | 保持文档与 runbook 最新，继续收敛 active path。 |
| 历史包袱仍需清理 | 仓库中存在 docs-archive、迁移票据、旧路径 guard。 | 对活跃文档与归档文档保持强区分。 |
| 控制端体验需要产品化 | 技术链路已有基础，但用户需要稳定、直观的执行可视化。 | 优先打磨设备选择、实时画面、Agent Monitor、失败恢复提示。 |
| 端到端验收成本高 | 真实设备、VM、WebRTC、Agent loop 的组合测试复杂。 | 建立分层 smoke：服务健康、设备通道、工具执行、完整 Agent 任务。 |
| 商业叙事需要聚焦 | 如果只说“Agent 平台”，容易和托管 Agent API 混淆。 | 聚焦 agent-native computer、真实设备执行、用户环境控制。 |

## 10. 后续建设建议

### 10.1 控制端先轻后重

控制端可以先聚焦最小闭环：

1. 设备/会话选择器
2. 实时画面窗口
3. 键鼠、文本、文件、命令入口
4. Agent 执行日志与当前状态
5. 断线重连和错误提示

这部分不需要一开始做成庞大控制台。真正重要的是它要把后端执行闭环清楚地呈现出来。

### 10.2 把“可恢复执行”做成核心卖点

NovAIC 的技术价值不只是 Agent 能点屏幕，而是失败后能知道：

- 当前任务在哪个 Scope
- 上一次观察到了什么
- 哪个工具调用失败
- 大对象在哪里
- 用户消息是否已消费
- Session 是否可以恢复

这正是 Runtime + Cortex + Blob + Entangled 的组合价值。

### 10.3 对外叙事聚焦三句话

建议对外使用更聚焦的表达：

1. NovAIC lets agents operate real computers, not just cloud containers.
2. NovAIC combines device control, agent runtime, work memory, and multi-model routing.
3. NovAIC turns agent work into observable, recoverable execution trajectories.

中文版本：

1. NovAIC 让 Agent 操作真实计算环境，而不是只在云容器里跑命令。
2. NovAIC 把设备控制、Agent Runtime、工作轨迹和多模型路由做成一体化平台。
3. NovAIC 让 Agent 的工作过程可观察、可恢复、可审计。

## 11. 结论

NovAIC 已经具备一个复杂 AI Agent 平台的主要骨架：多端客户端、网关、业务实体、运行时、上下文轨迹、对象存储、设备控制、沙箱、模型路由和同步引擎。按当前快照估算，项目已有约 21.5 万行统计源码/文档/脚本，其中测试相关内容约 5.3 万行，说明工程投入已经明显超过原型阶段。

项目最大的差异化不在“能不能跑 Agent loop”，而在“Agent 能不能进入真实设备和用户环境，并把工作过程稳定地呈现、记录和恢复”。如果控制端体验继续收敛，后端 active path 继续清理，NovAIC 可以从一个复杂工程系统进一步变成一个有清晰产品边界的 agent-native computer 平台。
