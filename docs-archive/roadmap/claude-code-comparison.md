# NovAIC vs Claude Code 深度架构对比与迭代建议

> 对照源码：`thirdparty/claude-code`（Anthropic 2026-03-31 泄露版，~1900 文件）及 `thirdparty/openclaw`（社区开源版）
> 最后更新：2026-04-10

---

## 一、产品定位根本性差异（不要搞混赛道）

| 维度 | **Claude Code** | **NovAIC** |
|---|---|---|
| 形态 | 本地 CLI（终端 TUI，Bun 运行时） | 全云端微服务 + Tauri 桌面 App |
| 核心场景 | **单人编程开发辅助** | **多用户多设备 AI 自动化 + 物理设备控制** |
| 用户量模型 | 1 人 1 进程 | N 用户 × M Agent × K 设备 并发 |
| 持久化 | 本地 JSONL 文件 | 云端 S3 + Entangled 实时同步 |
| 设备控制 | ❌ 无 | ✅ WebRTC / VmControl / Scrcpy / QMP |
| 多端同步 | ❌ 无 | ✅ Entangled 三层协议（Server→SQL→App） |

**结论**：两者不是直接竞品。Claude Code 是极致的单兵编程武器，NovAIC 是带有物理操控能力的多用户 AI 平台。对比的目的是**从它的精致设计中提取可迁移的能力模块**。

---

## 二、能力矩阵逐项对比

### 2.1 上下文引擎 (Context Engine)

| 能力 | Claude Code | NovAIC Cortex | 差距评估 |
|---|---|---|---|
| 基础压缩 | ✅ 分块调 LLM 总结 | ✅ budget_compact 三级裁剪 | **平手**：各有侧重 |
| 自适应分块 | ✅ `computeAdaptiveChunkRatio` 根据消息平均大小动态调比例 | ❌ 固定策略 | ⚠️ **可借鉴** |
| 多阶段降级 | ✅ 全量→跳过大消息→兜底文字 | ⚠️ 有紧急截断但非多阶段 | ⚠️ **可借鉴** |
| 安全余量 | ✅ `SAFETY_MARGIN = 1.2`（20% token 估计误差保护） | ❌ 无显式余量 | ⚠️ **应加入** |
| 跨会话记忆 | ❌ 无（每次新会话从零开始） | ✅ Recall 模块扫归档 scope summary | **NovAIC 领先** |
| Scope 树与 DFS | ❌ 扁平消息列表 | ✅ 嵌套 scope + DFS 展开/折叠 | **NovAIC 领先** |
| 插件化替换 | ✅ OpenClaw 有 ContextEngine Slot 可替换 | ❌ 硬编码 | ⚠️ **可借鉴** |

### 2.2 沙盒执行 (Sandbox)

| 能力 | Claude Code | NovAIC Cortex | 差距评估 |
|---|---|---|---|
| 隔离级别 | **Docker 容器** | Subprocess + 临时目录 | 🔴 **Claude Code 远超** |
| TOCTOU 防护 | ✅ Pinned FD + PathGuard | ❌ 无 | 🔴 **应补** |
| 路径安全 | ✅ Symlink 检查 + 挂载映射 | ⚠️ `/ro` `/rw` ACL | 🔴 **应补** |
| 浏览器沙盒 | ✅ `Dockerfile.sandbox-browser` | ✅ MCP VMuse (不同路线) | **平手** |
| Git Worktree 隔离 | ✅ `EnterWorktreeTool` | ❌ 无 | ⚠️ 编程场景有用 |

### 2.3 工具系统 (Tools)

| 能力 | Claude Code | NovAIC | 差距评估 |
|---|---|---|---|
| 文件读写改 | ✅ 3 个专用 Tool | ✅ Cortex tool_read/write | 平手 |
| Shell 执行 | ✅ BashTool + PowerShellTool | ✅ Cortex tool_shell | 平手 |
| 代码搜索 | ✅ GlobTool + GrepTool (ripgrep) | ⚠️ Sandbox 内可用 | ⚠️ 无专用 Tool |
| LSP 集成 | ✅ **LSPTool（语言服务器）** | ❌ | 🟡 **高价值可借鉴** |
| Web 搜索/访问 | ✅ WebFetchTool + WebSearchTool | ✅ MCP VMuse 浏览器自动化 | **NovAIC 更强**（真实浏览器） |
| 设备控制 | ❌ | ✅ VmControl 全栈 | **NovAIC 独有** |
| 定时触发 | ✅ ScheduleCronTool | ⚠️ Scheduler 原始形式 | ⚠️ 可参考 |
| 按需工具发现 | ✅ ToolSearchTool | ❌ | 🟡 工具多了以后有用 |
| Notebook 编辑 | ✅ NotebookEditTool | ❌ | 低优 |

### 2.4 多 Agent 协调

| 能力 | Claude Code | NovAIC | 差距评估 |
|---|---|---|---|
| 子代理生成 | ✅ AgentTool | ✅ SubAgent | 平手 |
| 团队并行 | ✅ TeamCreateTool + Coordinator | ✅ **IM 消息链路天然支持** | **NovAIC 更优** |
| Agent 间通信 | ✅ SendMessageTool（内存管道） | ✅ **Entangled chat_messages（持久化、可见、可追溯）** | **NovAIC 更优** |
| 协调可视化 | ❌ 用户看不到中间过程 | ✅ 前端实时可见 Agent 对话 | **NovAIC 更优** |
| 容错性 | ❌ 进程死了全丢 | ✅ Saga 持久化断点续跑 | **NovAIC 更优** |
| Git 分支隔离 | ✅ Worktree 做物理隔离 | ❌ | ⚠️ 编程协作有用 |

### 2.5 记忆系统

| 能力 | Claude Code | NovAIC | 差距评估 |
|---|---|---|---|
| Session 记忆 | ✅ SessionMemory 服务 | ✅ Cortex scope 树 | 平手 |
| 持久记忆目录 | ✅ `memdir/`（文件目录式记忆） | ✅ Cortex `/ro/knowledge/` | 平手 |
| **自动记忆提取** | ✅ **`extractMemories/` 对话结束后自动抽取关键要点** | ❌ | 🔴 **高价值，应引入** |
| **团队记忆同步** | ✅ **`teamMemorySync/` 多 Agent 共享** | ❌ | 🟡 **中等价值** |
| 跨会话 Recall | ❌ | ✅ 归档 scope summary 自动注入 | **NovAIC 领先** |

### 2.6 IDE 与外部集成

| 能力 | Claude Code | NovAIC | 差距评估 |
|---|---|---|---|
| VS Code 桥接 | ✅ `bridge/` 双向通信 | ❌ | 🟡 非核心赛道 |
| JetBrains 桥接 | ✅ | ❌ | 🟡 非核心赛道 |
| 语音输入 | ✅ `voice.ts` + `voiceStreamSTT.ts` | ❌ | 🟡 体验升级 |
| OAuth + 多 Provider | ✅ 支持切换不同 LLM 提供商 | ✅ LLM Factory 做路由 | 平手 |
| Feature Flags | ✅ GrowthBook + Bun dead code strip | ❌ | 低优 |

---

## 三、NovAIC 独有护城河（Claude Code 完全做不到的事）

| 能力 | 说明 |
|---|---|
| **WebRTC 媒体流控制** | 实时视频画面传输、远程桌面操控 |
| **Android / QEMU 物理设备管理** | 通过 Scrcpy / QMP 直接操控真机 |
| **CloudBridge 跨网穿透** | NAT 穿透、云端与内网设备互通 |
| **Entangled 多端实时同步** | 服务端→客户端 Rust SQLite 全链路 |
| **OTA 前端发版** | 修 Bug 秒推全球用户，无需重装 |
| **H264 硬件编码 + Anti-Slowmo** | 视频流防卡顿、防延迟累积 |
| **多用户多租户隔离** | S3 按 user/agent 物理隔离存储 |

---

## 四、迭代优先级建议（按 ROI 排序）

### 🔴 P0 — 高价值低成本，建议尽快引入

| # | 能力 | 来源 | 预估工作量 | 为什么急 |
|---|---|---|---|---|
| 1 | **自动记忆提取 (Auto Extract Memories)** | `services/extractMemories/` | 2-3 天 | 每轮对话结束后自动抽取关键决策/要点写入 Cortex `/ro/knowledge/`，让 Recall 越用越聪明。现在我们的 Recall 只靠手动归档 scope summary，太弱了 |
| 2 | **Compaction 安全余量 (Safety Margin)** | `compaction.ts` | 半天 | 在 `budget_compact` 加入 20% token 估计误差保护，避免偶发的超长溢出导致 LLM 截断 |
| 3 | **自适应分块比例** | `computeAdaptiveChunkRatio` | 1 天 | 当消息平均体积大时自动缩小压缩分块，防止单块超模型上下文窗口 |

### 🟡 P1 — 中等价值，需要一定投入

| # | 能力 | 来源 | 预估工作量 | 说明 |
|---|---|---|---|---|
| 4 | **LSP 语言服务器集成** | `tools/LSPTool/` | 1-2 周 | 让 Agent 能查函数定义、引用、类型等，比 grep 暴搜精准 100 倍。对编程类 Agent 是质变 |
| 5 | **Cron 定时任务工具** | `ScheduleCronTool` | 3-5 天 | 让 Agent 能设定"每天早上 8 点检查一次邮件"等自主计划行为 |
| 6 | **Git Worktree 隔离** | `EnterWorktreeTool` | 3-5 天 | 多 Agent 并行改代码时物理隔离 Git 分支，避免互相踩脚 |
| 7 | **Sandbox Docker 化** | `sandbox/` | 1-2 周 | 将 Cortex Sandbox 从 subprocess 升级为 Docker 容器级隔离，提升安全性 |

### 🟢 P2 — 锦上添花，长期规划

| # | 能力 | 来源 | 预估工作量 | 说明 |
|---|---|---|---|---|
| 8 | 团队记忆同步 | `teamMemorySync/` | 1 周 | 多个 Agent 之间共享部分记忆片段 |
| 9 | 语音输入 | `voice.ts` | 2 周 | 对移动端和桌面端均有体验提升 |
| 10 | IDE Bridge | `bridge/` | 2-3 周 | VS Code / JetBrains 集成，但不是我们的核心赛道 |
| 11 | ToolSearchTool | `ToolSearchTool/` | 2 天 | 工具数量超过 20 个后，按需发现比全量注入更省 token |
| 12 | Plan Mode | `EnterPlanModeTool` | 3 天 | "先规划后执行"的显式模式切换 |

---

## 五、最终结论

```
Claude Code 是一把瑞士军刀 — 精致、全面、单兵作战极强
NovAIC 是一台航母战斗群 — 多端协同、物理控制、跨网穿透

瑞士军刀上有几个好零件值得拆下来装到航母上（自动记忆提取、LSP、安全余量）
但航母独有的舰载机、雷达、防空系统（WebRTC、VmControl、Entangled）
是瑞士军刀永远做不到的
```

**核心迭代方向**：不要试图把 NovAIC 变成另一个 Claude Code，而是把 Claude Code 在"认知精细度"上的优势（记忆提取、压缩算法、LSP）嫁接到我们的"物理控制平台"上，形成**既能操控设备又能精确思考**的超级体。
