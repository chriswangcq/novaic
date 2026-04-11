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
