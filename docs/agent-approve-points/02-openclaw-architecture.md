# OpenClaw 代码架构

## 一、系统总览

OpenClaw 是一个**单体 TypeScript 应用**，所有逻辑在一个进程内运行。Agent loop 是经典的 `while(true)` 内联循环，通过 `pi-agent-core` 库驱动 LLM 交互。

```
Gateway HTTP/WS → runEmbeddedPi() → [retry loop] → runEmbeddedAttempt()
                                                          ↓
                                                    AgentSession.prompt()
                                                          ↓
                                                    LLM ⇌ Tool execution (内联)
                                                          ↓
                                                    subscribeEmbeddedPiSession
                                                    (实时 streaming 处理)
```

## 二、核心文件结构

```
thirdparty/openclaw/src/
├── agents/
│   ├── pi-embedded-runner/
│   │   ├── run.ts              # 外层 retry loop (1720 行)
│   │   └── run/
│   │       ├── attempt.ts      # 内层 agent loop (3213 行) — 核心
│   │       ├── params.ts       # 参数定义
│   │       ├── payloads.ts     # 请求构造
│   │       └── types.ts        # 类型定义
│   ├── pi-embedded-subscribe.ts  # 流式处理 pipeline (727 行)
│   ├── compaction.ts             # Context compaction
│   └── tool-catalog.ts          # 工具目录（profiles: minimal/coding/full）
├── plugins/
│   ├── types.ts              # Plugin 类型定义（25 种 hooks）
│   └── registry.ts           # Plugin 注册中心
├── context-engine/           # 可插拔 Context Engine
├── memory/                   # Memory 系统
├── hooks/                    # Hook 运行器
└── infra/                    # 基础设施（日志、事件等）
```

## 三、Agent Loop 架构

### 3.1 外层：`runEmbeddedPi()`（run.ts, 1720 行）

```
while (attemptsRemaining > 0) {
    result = await runEmbeddedAttempt(params)
    
    if (成功) break
    if (context overflow) → auto-compaction → retry
    if (auth 失败) → 轮换 auth profile → retry
    if (模型过载) → failover 备用模型 → retry
    if (rate limit) → exponential backoff → retry
}
```

负责：
- 模型解析和认证（支持多 auth profile 轮换）
- 失败重试策略（200 行 error classification）
- 模型 failover（主模型 → 副模型自动切换）
- Context overflow 恢复（compaction/截断）

### 3.2 内层：`runEmbeddedAttempt()`（attempt.ts, 3213 行）

这是 OpenClaw 的核心。一次 attempt 包含：

```
1. 环境设置
   ├── workspace 解析（sandbox vs 原生）
   ├── skills 发现和注入
   ├── bootstrap file 加载
   └── system prompt 构建（含 runtime info / channel capabilities / model hints）

2. Session 构建
   ├── SessionManager.open()（JSONL transcript）
   ├── acquireSessionWriteLock()
   ├── transcript 验证（Gemini/Anthropic 轮次修复）
   └── limitHistoryTurns (截断过长历史)

3. Context Engine 集成
   ├── contextEngine.bootstrap()
   ├── contextEngine.assemble()  → 注入 memory/RAG 到 system prompt
   └── (post-turn) contextEngine.afterTurn() / maintenance()

4. 工具设置
   ├── MCP tool runtime
   ├── LSP tool runtime  
   ├── Plugin 注册的工具
   ├── Client-hosted tools (OpenResponses)
   └── Extension factory tools

5. StreamFn 包装
   ├── Ollama num_ctx 注入
   ├── OpenAI WS bridge
   ├── Anthropic vertex bridge
   ├── Thinking block 剥离
   ├── Tool call ID sanitize
   ├── Tool name trim
   ├── Malformed args 修复（Kimi）
   ├── HTML entity decode（xAI）
   └── Anthropic payload logging

6. Prompt 执行
   ├── before_prompt_build hooks
   ├── prompt image detection & loading
   ├── llm_input hooks
   ├── AgentSession.prompt()  ← 实际 LLM 调用
   └── llm_output / agent_end hooks

7. 后处理
   ├── compaction wait + retry
   ├── cache-TTL timestamp append
   ├── context engine afterTurn / maintenance
   └── 构建返回结果
```

### 3.3 Streaming Pipeline：`subscribeEmbeddedPiSession()`

```
AgentSession events
  ├── text_delta → stripBlockTags → EmbeddedBlockChunker → onBlockReply
  ├── text_end → finalizeAssistantTexts → dedup check
  ├── tool_start → emitToolSummary
  ├── tool_end → emitToolOutput + commit messaging tool texts
  ├── message_end → flush + recordUsage
  ├── compaction_start/end → noteCompactionRetry
  └── reasoning events → onReasoningStream
```

关键能力：
- `<think>` / `<final>` 标签的**跨 chunk 状态追踪**
- Block chunking（按 maxChars/minChars/breakOn 智能分段）
- Messaging tool 去重（agent 通过工具发送的文本不再重复推送）
- Usage token 累计

## 四、25 种 Plugin Hooks

| 类别 | Hooks | 说明 |
|------|-------|------|
| 模型选择 | `before_model_resolve` | 运行时覆盖 model/provider |
| Prompt 构建 | `before_prompt_build`, `before_agent_start` | 注入 context 到 system prompt |
| LLM I/O | `llm_input`, `llm_output` | 监控/记录 LLM 交互 |
| Agent 生命周期 | `agent_end` | agent 运行结束后处理 |
| Compaction | `before_compaction`, `after_compaction`, `before_reset` | 压缩前后处理 |
| 消息处理 | `inbound_claim`, `message_received`, `message_sending`, `message_sent` | 消息拦截/修改 |
| 工具执行 | `before_tool_call`, `after_tool_call`, `tool_result_persist`, `before_message_write` | 工具调用拦截/修改 |
| Session | `session_start`, `session_end` | 会话生命周期 |
| Subagent | `subagent_spawning`, `subagent_delivery_target`, `subagent_spawned`, `subagent_ended` | 子 agent 管理 |
| Gateway | `gateway_start`, `gateway_stop` | 网关生命周期 |

## 五、Context Engine 生命周期

```
┌─── run 开始前 ───────────────────────────────────────┐
│ bootstrap()    → 从上次 state 恢复                    │
│ assemble()     → 根据当前 prompt 组装 context          │
│   ├── 注入 memory/RAG 到 system prompt                │
│   ├── 调整 messages 列表                              │
│   └── 管理 token budget                               │
└──────────────────────────────────────────────────────┘
                    ↓ LLM 执行 ↓
┌─── run 结束后 ───────────────────────────────────────┐
│ afterTurn()    → 更新 memory store，索引新 messages    │
│ ingestBatch()  → 批量 ingest 新 messages              │
│ maintenance()  → pruning, compaction, 过期清理         │
└──────────────────────────────────────────────────────┘
```

## 六、Session 管理

- **存储格式**: JSONL 文件（每行一个 entry）
- **Entry 类型**: `session_header`, `message`, `custom_entry`
- **Write Lock**: 分布式锁防止并发写入
- **分支**: 可从任意历史 entry 创建新分支
- **修复**: 自动检测和修复损坏的 JSONL

## 七、Provider 兼容层

| Provider | 兼容处理 |
|----------|---------|
| Ollama | 自动注入 `num_ctx` 参数 |
| Kimi/Moonshot | 修复畸形 tool call JSON |
| xAI/Grok | 解码 HTML entities |
| Anthropic | 剥离 `<thinking>` 块、轮次校验 |
| Google/Gemini | 轮次校验、reasoning pair 处理 |
| Mistral | Tool call ID 格式 sanitize |
| OpenAI | Responses API reasoning pair 降级 |
| OpenAI WS | WebSocket transport adapter |
| Anthropic Vertex | Vertex AI transport adapter |

## 八、OpenClaw 核心优势

| 特性 | 说明 |
|------|------|
| **Token streaming** | 逐 token 推送 + 智能 block chunking |
| **Context Engine** | 可插拔，支持 memory/RAG 注入 |
| **Plugin 系统** | 25 个 hook 点，第三方可扩展 |
| **Provider 兼容** | 10+ provider 的实时流修复 |
| **Session 分支** | JSONL transcript + 分支回退 |
| **Client tools** | 客户端执行工具（OpenResponses） |
| **Agent yield** | 主动暂停等待外部事件 |
| **成熟的错误恢复** | auth 轮换 + 模型 failover + overflow 恢复 |
