# Agent 优化点汇总

> 每条优化点有独立编号和审批状态，逐条讨论。

---

## 状态说明

- `[ ]` 未讨论
- `[/]` 讨论中
- `[x]` 已审批通过
- `[-]` 已拒绝/不做

---

## 🔴 P0 — 核心缺失（用户体验/能力的根本差异）

### [-] OPT-01: Token-level Streaming

**现状**: NovAIC 等 LLM 完整返回后批量广播 `think_complete` 事件。用户看到的是等待 → 完整结果。

**OpenClaw 做法**: Token 级别的流式推送 + `<think>` 标签实时剥离 + block chunking（智能分段发送长回复）。

**影响**: Chat 场景下用户体验的根本差异。等 30 秒看完整回复 vs 立即看到 token 流出来。

**改造方向**:
1. LLM handler 改为 streaming 模式（使用 `stream=True`）
2. 新增 streaming 广播通道（token delta 事件）
3. 前端适配逐 token 渲染
4. 可选：block chunking（长回复分段）

**复杂度**: ⭐⭐⭐⭐ — 需要改 LLM handler + 广播机制 + 前端，但不影响 Saga 架构

---

### [ ] OPT-02: Context Engine 抽象

**现状**: NovAIC 的 context 是扁平 CRUD（append/read），Summary 只在 runtime 结束后运行，不参与 runtime 内部。

**OpenClaw 做法**: 可插拔 Context Engine，生命周期：bootstrap → assemble（注入 memory/RAG）→ afterTurn → maintenance。

**影响**: 无法实现：
- 长期记忆召回（memory recall → system prompt injection）
- RAG on conversation history（语义搜索历史对话）
- 动态 context budget（根据 model context window 自动调整）
- Plugin 注入 context

**改造方向**:
1. 定义 `ContextEngine` 抽象接口（Python protocol）
2. 在 `react_think` 的 `read_context` 前增加 `assemble` 阶段
3. 在 `runtime_complete` 中调用 `afterTurn` / `maintenance`
4. 默认实现：现有 context 逻辑
5. 扩展实现：memory + RAG 注入

**复杂度**: ⭐⭐⭐⭐⭐ — 架构级改动，需要仔细设计接口

---

## 🟡 P1 — 重要能力（可扩展性/健壮性）

### [ ] OPT-03: Plugin Hook 系统

**现状**: NovAIC 通过 `broadcast_event` 做单向状态推送，外部系统无法注入 context、拦截工具调用、修改 prompt。

**OpenClaw 做法**: 25 种双向 lifecycle hooks，第三方可运行时注册。

**影响**: 可扩展性受限。目前添加新行为（如工具审计、prompt 注入、消息过滤）需改源码。

**改造方向**: 
1. 定义 hook 接口（先实现最重要的几个）：
   - `before_llm_call` — 修改 prompt / 注入 context
   - `after_llm_call` — 处理 LLM 输出
   - `before_tool_call` — 拦截/修改工具调用
   - `after_tool_call` — 记录工具使用
2. 在 Saga handler 中增加 hook 调用点
3. Hook 注册机制（配置文件 or API）

**复杂度**: ⭐⭐⭐ — 接口设计简单，关键在确定 hook 边界

---

### [ ] OPT-04: 多 Provider 兼容层

**现状**: 基础适配（OpenAI/Anthropic/Google 格式转换），不处理 provider 特有的 quirk。

**OpenClaw 做法**: 10+ provider 的实时流修复（畸形 JSON、HTML entities、thinking block 剥离、轮次校验）。

**影响**: 接入新 provider（DeepSeek、Qwen、Moonshot）时可能遇到难以调试的 agent 执行失败。

**改造方向**:
1. 在 `llm.py` 中增加 post-processing pipeline
2. 每个 provider 的 quirk 作为独立 fixer 函数
3. Tool call response 的 validation + repair
4. 新增：Anthropic/Gemini 轮次校验

**复杂度**: ⭐⭐⭐ — 累积性工作，按 provider 逐步添加

---

### [ ] OPT-05: LLM 调用重试 + 模型 Failover

**现状**: LLM 调用失败直接返回 `[LLM Error]`，无重试，无 failover。

**OpenClaw 做法**: 
- 错误分类（200行）→ 重试 vs 不重试
- Auth profile 轮换（多个 API key 自动切换）
- 模型 failover（主模型过载自动切换副模型）
- Exponential backoff for rate limit

**改造方向**:
1. `llm_handlers.py` 增加 retry decorator（指数退避）
2. 错误分类：可重试（429、5xx、timeout）vs 不可重试（400、401）
3. 配置 fallback model（model_id → fallback_model_id）
4. Auth profile 轮换（多 key 支持）

**复杂度**: ⭐⭐ — 相对独立，不影响架构

---

### [ ] OPT-06: Context Overflow 自动恢复

**现状**: Context 超出 token 限制时，LLM 报错，runtime 异常终止。

**OpenClaw 做法**: 
- 检测 overflow 错误 → 自动触发 compaction → 重试
- 截断过长的 tool result
- `limitHistoryTurns` 限制历史轮数

**改造方向**:
1. `react_think` 中检测 LLM 返回的 overflow 错误
2. 触发 context compaction（使用 LLM 压缩历史）
3. 压缩后重试 LLM 调用
4. 可选：tool result 截断策略

**复杂度**: ⭐⭐⭐ — 需要在 Saga 中增加"retry after compaction"路径

---

## 🟢 P2 — 差异化能力（特定场景需要）

### [ ] OPT-07: Agent Yield（主动暂停）

**现状**: `need_rest` = 终止 runtime。`check_new_messages` 可唤醒，但是新 runtime。

**OpenClaw 做法**: Agent 主动 yield → 暂停但不终止 → 保留 session state → 新消息来时恢复。

**影响**: SubAgent 协作场景（发消息给其他 agent 等回复）需要"暂停等待"而非"终止重启"。

**改造方向**:
1. 新增 `subagent_yield` 工具（暂停但不完成）
2. Runtime 增加 `yielded` 状态
3. Watchdog 或新消息触发时恢复执行
4. 恢复时保留原 context + 注入 yield 期间的新消息

**复杂度**: ⭐⭐⭐⭐ — 需要新的 runtime 状态和恢复机制

---

### [ ] OPT-08: Client-Hosted Tools

**现状**: 所有工具在服务端通过 MCPBusiness → ToolsServer 执行。

**OpenClaw 做法**: 支持客户端定义和执行工具。LLM 调用这些工具时，结果返回给客户端执行。

**影响**: 无法实现前端工具（浏览器操作、本地文件系统访问等）。

**改造方向**:
1. Gateway WebSocket 协议增加 `tool_call_request` / `tool_call_response` 消息
2. Agent 可标记某些工具为 `client_hosted`
3. 执行到 client-hosted 工具时，通过 WS 下发给前端
4. 前端执行后回传结果，agent 继续

**复杂度**: ⭐⭐⭐ — 主要是 WS 协议扩展

---

### [ ] OPT-09: 实时 Context Compaction

**现状**: Summary 只在 runtime 完成后异步运行（Summarize Saga）。Runtime 执行期间 context 持续增长。

**OpenClaw 做法**: Runtime 内部实时 compaction — 当 context 接近 token limit 时自动压缩，不中断执行。

**改造方向**:
1. `react_think` 的 `read_context` 后增加 token 估算
2. 接近阈值时触发 compaction（使用 LLM 压缩历史部分，保留最近 N 轮）
3. 压缩后替换 context，继续正常执行

**复杂度**: ⭐⭐⭐ — 需要 token 估算 + compaction logic

---

## ⚪ P3 — 可选优化（现有方案可接受）

### [ ] OPT-10: Session 分支/回退

**现状**: Context 是线性的 messages 列表，无法回退到历史节点重新对话。

**OpenClaw 做法**: JSONL transcript + branch/rollback + write lock。

**影响**: 目前影响有限，适用于探索性对话场景。

**复杂度**: ⭐⭐⭐⭐ — 需要重新设计 context 存储模型

---

### [ ] OPT-11: 最大轮次限制

**现状**: 无内置限制，agent 理论上可以无限循环。

**OpenClaw 做法**: 配置 `maxHistoryTurns`，超出时拒绝新 prompt。

**改造方向**: `react_actions` 的 `decide_continue` 中增加 `round_num > max_rounds` 检查。

**复杂度**: ⭐ — 一行代码

---

---

## 讨论记录

> 在下方记录每次讨论的结论和修改意见

### 讨论 1: _待开始_

_日期: ____
_讨论内容: ____
_结论: ____
