# NovAIC 项目交接文档与更新纪要 (Changelog)

> ⚠️ **架构说明大转移**：
> 从 2026 年 04 月开始，为了提供最细粒度的源码映射和模块剖析，所有的架构文档、组件拆解（Entangled/Cortex/Runtime/VmControl/Gateway/前端等）已**全量抽离**到 [`docs/README.md`](docs/README.md) 索引下。
> **本文档 (`HANDOVER.md`) 经过“超级瘦身”，从现在起仅保留核心的【快速部署命令】与随时间推移的【大版本更新日志 (Changelog)】供 AI/人类进行上下文追溯。**

---

## 一、架构体系阅读入口 (Architecture Entry)

请立即前往 **👉 [`docs/README.md`](docs/README.md) 👈** 阅读系统级拓扑以及多达 9 大模块库的深层设计！
- 需要看端对端端口映射与拓扑：[`docs/architecture/overview.md`](docs/architecture/overview.md)
- 需要看各个具体服务如 Cortex, Entangled, VmControl 的底层重构与源码说明：进入 `docs/` 目录下同名的文件夹。

## 二、快速上手与部署 (Deployment)

| 需求 | 操作 (在根目录或对应目录执行) |
|---|---|
| 本地环境准备 | Node>=18, Rustup (stable), macOS 需 xcode-select |
| 本地跑客户端 | `cd novaic-app && npm install && npm run tauri:dev` |
| 纯 UI 调试 | `cd novaic-app && npm run dev` (http://localhost:5173) |
| **部署前端 OTA** | `./deploy frontend [version]` |
| **部署全部后端** | `./deploy services` (含 Gateway 等主力后端) |
| **部署 Relay/网络**| `./deploy relay` |
| **构建桌面 App** | `./deploy desktop` (输出至 src-tauri/target/release/bundle/...) |
| **构建安装 iOS** | `cd novaic-app && ./scripts/build-and-install-ios.sh` |
| **清空本地缓存** | 客户端 Settings → Clear Cache (重置 Rust SQLite DB 连同挂起列) |

## 三、大版本更新与系统重构交接日志 (Changelogs)

> （由 `/update-handover` Slash 工作流命令追记生成使用，请自顶向下追加）

> 最后更新：2026-04-21 — **Roadmap `message-wake-refactor.md` 与 tickets/ SSOT 对齐**：按 `tickets/README.md` index 逐条翻牌 Phase 1–5 的 `Status` 与 sub-task（原本大量残留编制期 `[ ]`，与 PR-01..PR-35 全 `[x]` 的真相严重漂移）。翻牌规则：✅`[x]` = 有 PR 合并、✅`[!]` = 落地时策略改 / 并入别 PR / 明确判无需做（均附 PR 号或 ADR 原因）、`[ ]` 保留给真未做的开口；最终全文只剩 P4-4 一条正式告警通道 TODO 是真开口（现状：log marker + `ORPHAN`/`PERMANENT_ORPHAN` 前缀已落，待接 pagerduty/飞书/Slack）。顶部 SSOT 提示段同步改写：不再自我描述为"过时勾位"，而是声明状态已对齐。顺带标注的策略变更：P3-2 "保留旧字段一个 release" → `[!]`（PR-30 直接清零，配合"历史数据全删"决策）；P4-2 histogram/pending_count gauge → `[!]`（`outbox_lag_seconds` + `outbox_backlog_count` + `orphans_total` 组合覆盖）；P5-4 迁移脚本 → `[!]`（废弃，规范 `CREATE TABLE` 为准）。

> 最后更新：2026-04-20 — **Command Center 从工单系统进化为 AI-Native 组织引擎**：新增 `novaic-command-center/` 独立服务（FastAPI + SQLite, port 9800）。**组织架构**：实现角色认证体系（coder/reviewer/qa/deployer），考试=非对称鉴权（公钥=考题，私钥=能力），三权分立（Owner 出题 / Interviewer 判卷 / Worker 干活）；防自审机制（同 agent 或同 provider 不能在同一 ticket 上既写码又 review）；skip_preflight 简单票跳过预审。**可测试性架构**：抽取 `logic.py` 纯函数层（零 I/O 依赖），39 个零 mock 单测 0.21s 全通过；`validate_submit_evidence` 强制检查 `[unit]` checklist 项必须提供 `kill_test` evidence；新增 `scripts/lint_logic_purity.py` AST lint 扫描 `*_logic.py` 文件禁止 import I/O 库。**文件命名约定**：`*_logic.py`=纯函数必须单测 / `*_actions.py`=glue 层 / `*_ports.py`=接口定义。**Agent ID 规范**：`{tool}-{model}`（如 antigravity-gemini, cursor-claude）。**状态**：16 态状态机 + 认证流水线已 E2E 验证通过；下一步实现 Master cron 调度器和 Worker dispatcher。

> 最后更新：2026-04-16 — **Signaling-via-Business + user_id Protocol Fix + 文档全面对齐**：修复 Business entity proxy 的 user_id 协议缺陷（`_split_scope` 正确拆分 user_id→X-User-ID / notify→X-Notify / order_by→query / 剩余→X-Params），修复 Device `BusinessEntityClient` 四个 bug（order_by 未转发、notify=False 被吞、delete_where 丢失 filters、update_where 丢弃 params）；WebRTC 信令全链路改走 Business（新增 `business/internal/signaling.py` 三端点：connected-devices / relay-to-device / push-to-user；Gateway `app_client.py` 改调 Business；Device `gateway_signaling.py` 回程走 Business）；彻底删除 `gateway/device_client.py`，Gateway 不再直连 Device Service；修复 `gateway/api/routes.py` health 端点残留 device_client 引用；15 篇过时文档全面对齐 Business-Centric 架构。

> 最后更新：2026-04-16 — **Entangled-via-Business: Entity CRUD 全面收敛**：消除了 Device Service、Workers（Agent Runtime）、Gateway 对 Entangled 的全部直接 HTTP 调用，改为统一经 Business Service `/internal/entities/*` 代理。Business `entity.py` 新增 DELETE/PUT(upsert)/delete-where/batch-update/update-where/count/cas-update/schema-register 八个 proxy endpoint；Device Service 新增 `BusinessEntityClient` 替换原 `DeviceEntityStore`（`EntangledServiceClient` 依赖移除），`schema_push.py` 改走 Business `/internal/entities/schema/register`；Workers `BusinessClient.entity_*` 方法全部改走 Business HTTP（`self.entangled` 删除）；Gateway 新增 `GatewayBusinessEntityClient`，`files/registry.py`、`infra/deps.py`、`main_gateway.py` startup 全部改用 Business 代理，仅 LOCAL_ONLY auth 实体留在 `gateway.db`。`start.sh` 移除 Device `--entangled-url` 参数。架构目标：**仅 Business Service 直连 Entangled HTTP**。

> 最后更新：2026-04-15 — **Business-Centric Backend 架构重构**：Business Service 升级为中枢编排层——所有 Entangled action hooks（含 13 个 devices actions）统一回调 Business；Device Service 降级为纯硬件执行层，新增 `/internal/hardware/*` API，删除 `device_actions.py` 和 entity action dispatcher；Cortex `GatewayProxy` 重命名为 `BusinessProxy`，`--gateway-url` 改为 `--business-url` 直接指向 Business Service（:19998），不再经 Gateway 中转；Business 新增 `device_orchestrator.py` 编排设备生命周期，`device_client.py` 新增 `hw_*()` 系列方法调用 Device 硬件 API；Business 新增 `vm/*`/`mobile/*`/`hd/*` proxy routes 转发到 Device（Cortex 工具链路完整覆盖）；Gateway 删除已无引用的 `device_client.py`，彻底瘦身为纯边缘网关（Auth + File Proxy + App WS）；`start.sh` 更新 Device `--business-url` 和 Cortex `--business-url` 参数。

> 最后更新：2026-04-15 — **CloudBridge-VmControl 硬切重构 + 多层 Bug 修复链**：Device Service 彻底删除本地 QEMU/VNC 遗留代码（-4700 行），CloudBridge 切换为 typed WebSocket 协议，`proxy_request/proxy_response` 全部清除；修复 `entity_action` 吞没 `HTTPException` 导致 HD 启动报 500 而非真实错误码的 bug（Device Service + Business Service 同修）；修复 Entangled `_call_action_hook` 未解析 `urllib.error.HTTPError` 响应体的问题；修复 `DELETE /{entity}/where` 路由冲突（被 `/{entity}/{id}` 吞掉），改为 `POST /{entity}/delete-where`（同步更新 `entangled_client.py`）；前端 dispatch 管线新增 `upsert` intent，`createFormStore` 支持 `useUpsert` 标志，解决 agent-binding 首次保存因 `update` 找不到记录而静默丢失的持久化 bug。
> 最后更新：2026-04-15 — **novaic-business / novaic-device 独立 repo + submodule**：`novaic-business` 与 `novaic-device` 从主仓直录目录改为 Git submodule（`git@github.com:chriswangcq/novaic-{business,device}.git`），与 gateway/common 等一致；子仓各含 `.gitignore` 忽略 `__pycache__`。克隆主仓请 `git submodule update --init --recursive`。
> 最后更新：2026-04-14 — **Gateway 微服务拆分 + 前端 TS 编译修复 + iOS mobile state 注册修复**：完成 Gateway God Module 拆分，抽离 Business Service（业务逻辑/Agent/Skill/Form/Model）和 Device Service（设备管理/PC-Bridge WS/VM 操作）为独立 FastAPI 进程，Gateway 瘦身至纯网关（Auth + Entity Proxy + Turn + File Proxy）；全部 Python 服务统一 `uvicorn.run(app, ...)` 直传 app 对象模式（解决 CLI args 在 worker 进程中丢失的 module re-import 问题）；修复前端 35 个 TS 编译错误（缺失的 `services/setup` 模块引用、`AICAgent` 类型补充 `vm`/`setup_complete`/`setup_progress` 可选属性、`AgentDisplayStatus` 补充 `needs_setup`/`setting_up` 状态、Chat 组件 `fullUrl`/`displayUrl` 未定义变量修正）；修复 iOS 端 `EntangledState` 和 `NavState` 未在 mobile setup 路径注册导致 Tauri command 报 "state not managed" 的问题（移入 `setup_shared`）；修复 `setup_shared` 中 `data_dir` 目录不存在导致 SQLite pool 创建 panic 的 iOS crash（添加 `create_dir_all`）；Device 注册改用 `upsert` 解决用户切换后设备归属不变的问题；Nginx 新增 `/device/` 路由块支持 Device Service 独立端口；deploy 脚本增加 Business/Device/Entangled 独立部署目标与全服务状态检查。
> 最后更新：2026-04-12 — **Entangled Standalone 实体路由分裂 + 设备全链路修复**：完成 Entity routing split，`LOCAL_ONLY_ENTITIES`（users/tokens/api-keys/vm-users/models）留 gateway.db，其余（devices 等）代理到独立 Entangled Service；修复 WS subscribe 因 `_local_store` 缺少 remote entity 定义导致 `vm-users` parent 查找 `devices` 时 KeyError 崩溃（3 秒断连循环）；修复前端"错误"状态（`get_status_action` 回退 EntityStore 读 Entangled）；Host Desktop type 从错误的 `linux` 改为 `host_desktop`；删除设备增加 PC Client pre-delete hook（`vm_delete` = shutdown + `DELETE /api/vms/{id}` 删磁盘，Android 走 `avd_delete`）；去除 `vm_status_report` 的 auto-create 防止删后重建。
> 最后更新：2026-04-11 — **Gateway v2 全面收官：清理废弃端点 + HealthWorker 补完**：删除 `subagent.py` 中 Worker 已不再调用的 9 个过渡期 HTTP 端点（`/sleeping`、`/awake`、`/completed`、`/failed`、`/summarizing`、`/rest`、`/check-and-clear-rest` 等），所有状态变更统一走 EntityStore entity_update；修复 `HealthWorkerSync._scan_unhandled_messages` 引用已删除 `GatewayInternalClient` 的 bug 并增加 Queue Service 活跃 session 查询以避免重复 dispatch；`gateway_v2_checklist.md` 全项打勾封闭。
> 最后更新：2026-04-11 — **Gateway v2 事件驱动解耦 (完美收官)**：扫清最后盲区，撤除 `gateway/api/internal/subagent.py` 中的大量轮询僵尸端点与僵化方法，将内部 `spawn_subagent` 与 `subagent_send` 完全改写为直接向 Queue Service 推送的实时 dispatch 请求；新立 `HealthWorkerSync` `_scan_unhandled_messages` 兜底检查，接管网络波动遗留的实体用户消息发起强制 dispatch，系统彻底步入无状态秒秒即达的纯事件驱动架构。
> 最后更新：2026-04-11 — **Gateway v2 事件驱动解耦 (Steps 1-4)**：新增 Queue Service Session Coordinator（`tq_active_sessions`、`tq_pending_triggers`）确保 session 排他性与原子分发；切断 Worker 对 Gateway 的依赖，所有 handler（`subagent`、`context`、`runtime`、`tool` 等）直写 EntityStore（基于新开辟的 Gateway `/internal/entities` 端点）；重写 Watchdog 仅保留定时唤醒和中断拦截，取消 `sending` 状态轮询；大幅清理废弃端点与死代码，全面从“轮询状态”倒向“事件并发队列”。
> 最后更新：2026-04-10 — **Gateway 架构清理与 Cortex 配置正规化**：彻底移除了遗留的 Runtime Orchestrator (RO) 死代码，清理了 `agent.py` 及 `subagent.py` 中的大量废弃调用。同时修复了 Cortex URL 长期依赖硬编码环境变量的技术债，统一收口至 `services.json` 及 `strict_config.py`，所有 Runtime Worker 严格执行 `--cortex-url` 入参标准。
> 最后更新：2026-04-09 — **横跨架构维度的终局补充**：建立了统一数据字典（Entity Data Models）、Common 依赖生成链库（解决了多端类型生成与19996本地夺口战）、以及记录了处于公网隔离最顶层的 Nginx 网关重载 /internal 保卫阵列布置，完美闭环封库。
> 最后更新：2026-04-09 — **全域架构文档 L3 级大爆发与总盘瘦身**：针对 Entangled, Gateway, Runtime, Vmcontrol, MCP, Frontend, Network, Storage 等由于年久失修积攒的大量特性，重新生成了专属的大目录与几十篇细节详表，挂载于 `docs/` 目录下。本文档 `HANDOVER.md` 正式抛弃过往动辄上千行的繁重冗余组件解说，转为纯粹的变更追踪集。
> 最后更新：2026-04-09 — **Entangled 架构三层大一统**：废弃独立 `entangled-service` repo，逻辑全部并入 Entangled 本库（分拆为 server / sql / app 三层）。清理过时的架构文档（移除了 Tools Server、TRS 等端口引用），统一通过自带的 `entangled.app` 启动外壳。
> 最后更新：2026-04-09 — **§12 与 schema v63**：用户消息与 Agent/SubAgent 业务实体持久化已完全归顺于 **Entangled**（Path C）；Gateway `gateway.db` 仅保留运维与用户注册表（`agents` / `chat_messages` / `subagents` 等由于耦合已彻底 DROP 斩断）。
> 最后更新：2026-04-06 — **Cortex 存储模型修正 + DFS Step Tree**：明确 `/ro/` (核心配置只读区域) 与 `/rw/` (读写沙箱区) 的隔离边界；引入 `_sys_write`；实现 ContextEngine 基于 Step Tree 深度优先的数据大合叠与 summary 展开技术。
> 最后更新：2026-04-06 — **桌面「清空本地缓存」幽灵 Bug 修复**：`Cache::clear_all()` 现强制清整包裹 `pending_ops`（乐观锁滞留库）在内的所有的 `sqlite_master` 表并重置原子计数，彻底终结了重连后满屏 Sending 假死消息。
> 最后更新：2026-04-05 — **Agent Loop 统一无工具直接调用**：不再使用旧版注入合成的 `tool_calls`；Cortex `cortex.prepare_llm_context` 全包揽 messages + tools prompt；由 `llm_handlers` 直接拿回吐字，抹平了传统调用栈。
> 最后更新：2026-04-03 — **Cortex v3 无状态引擎定稿**：废弃内存旧引擎 Context Stack！新的基于文件的引擎核心代码由 ~5600 行压至 ~700 行。确立基于 S3 的四大组件（CortexStore, Workspace, Sandbox, Compactor）。
> 最后更新：2026-04-02 — **OpenClaw 子模块考察借签**：引入 `thirdparty/openclaw` 旁支用于架构比对论证；总结了五份关于 Skills、隔离、市场分发的报告但确认不影响当前 NovAIC 端托底拓扑。
> 最后更新：2026-04-01 — **Sync Contract 与 Slot 订阅隔离机制 (NavState)**：彻底修理了 AppWS 的跨组件踩脚重连 Bug，实现了 `navChanged` 与 Rust 多 `tokio::Mutex` 插槽槽位，保证不同组件独立维持视图生命！
> 最后更新：2026-03-31 **Agent-Binding 持久化修复**：修正乐观锁引起的绑定丢失，`useAgentBinding.ts` 强迁移表单引擎并与 `nav.rs` 实现深度联动，设备面板挂靠响应全活。

*(更古老的架构变更由于时间久远或被新架构文件所覆盖映射，可参阅 `docs/historical-doc-links.md` 通过 git 追溯旧版大体量 HANDOVER)*
