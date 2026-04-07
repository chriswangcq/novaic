# Context Stack v2 设计文档：内置依赖 + 被动式宿主循环

> **状态**：设计稿（实现前评审用，已合并 2026-04 评审修订 + 2026-04 架构评审修订 + 2026-04-03 生产化评审修订）  
> **范围**：`context-stack/` Python 包的重构方向  
> **前提**：**不保留**与 v1 构造方式/协议的兼容承诺；当前无外部生产接入，可一次性替换公开 API。

---

## 一、背景与目标

### 1.1 现状（v1）摘要

v1 将宿主耦合在四个 **Protocol** 上：`AgentExecutor`、`Summarizer`、`TokenCounter`、`MemoryBackend`，且 **EXECUTE（③）** 通过同步调用 `executor.execute(messages, extra_tools)` 阻塞直到宿主返回**完整**消息列表。这对以下场景不友好：

- **队列 / Saga / Worker**：需要可序列化的进度、跨进程恢复、超时与取消；长阻塞的 `execute` 难以与任务步进对齐。
- **集成成本**：每个宿主都要组装四个实现，默认行为分散，易不一致。
- **观测与调试**：单调用黑盒内包含多轮 LLM，生命周期阶段在 trace 上不够细。

### 1.2 v2 目标

| 目标 | 说明 |
|------|------|
| **内置四件套** | `Summarizer`、`TokenCounter`、`CompactConfig`、`Store` 由**本库默认提供**；宿主不再强制注入（仍允许高级覆盖，见 §6）。 |
| **被动式 EXECUTE** | 引擎在**单次调用内**不跑完 Agent 循环；**宿主**步进「LLM → 工具」；**scope 开闭**由模型 **`skill_*` 工具** + 引擎内部状态机完成（**不是**「模型不参与引擎」）。可选 **`pull_turn_context` / `push_turn`** 仅 Worker/高级场景；**主路径**见 §3、§4.0。 |
| **保留六步语义** | ①～⑥ 的**语义不变**；变化的是 ③ 从单次阻塞调用变为**可跨多次宿主调用的子状态机**。 |
| **可恢复** | Session 状态可被序列化/恢复（至少定义规范与最小实现），适配 NovAIC Task Worker。 |

---

## 二、核心概念

### 2.1 术语

- **Engine**：进程级单例或按 runtime 实例化；负责注册表、全局 hook、默认实现工厂、压缩策略入口。
- **ScopeSession**：一次「技能事务」的句柄，对应 v1 中一次 `LifecycleExecutor.run` 所覆盖的范围；**一个 Session 对应一个 scope_id**。
- **Phase（可观测）**：宿主可见的粗粒度阶段；**①② 在内部 `_begin_scope` 内原子完成**，不单独暴露为 `session.phase` 枚举值（见 §4.2.0）。
- **Turn**：在 **Tier B**（§4.0）下，宿主完成的一轮「`pull_turn_context` → 调 LLM/工具 → `push_turn`」的单位；可多轮直到 **`finalize`（由 `push_turn(..., done=True)` 触发）** 或 **`abort`**。**Tier A 主路径**可不使用 `pull`/`push`，而以 **LLM 回合 + 工具 dispatch + `prepare_messages_for_llm`** 步进；**finalize** 仍以 **`skill_end` / 内部状态机**为准。  
- **Skill 栈（SkillStack）**：由内置工具 **`skill_begin` / `skill_end`**（名称可配置）驱动的 **后进先出** 打开状态列表；每一层对应一个 **ScopeSession**（或等价帧）。栈顶即「当前 skill 上下文」。  
- **Summarizer LLM（狭义）**：指 **`Summarizer.summarize` / `StructuredSummarizer`** 用于 **scope finalize ⑤** 的路径。与 **`prepare_messages_for_llm` 内**为减 token 可能调用的 LLM、以及 **`nested_fold_summarizer=llm`**（§4.6.8）在 **观测与配置**上须分列（见 §2.4）。

### 2.2 设计不变量

1. **Skill 栈与 Scope**：**`begin_scope` / `ScopeSession` 为引擎内部实现，不对外暴露**（§4.0）。**禁止**宿主绕过引擎维护栈；模型经 **`skill_begin` → … → `skill_end`** 形成 **多层栈**（最大深度可配置，默认如 4）。**禁止**在未 `skill_end` 栈顶帧时丢弃引擎侧栈。**栈空**时：若 **`auto_meta_when_stack_empty`**（§4.6.7）为真，则在 **下一 LLM 前**自动开 **Meta**；若为假，则允许空栈（不推荐生产）。
2. **消息真相源**：引擎内 **`messages` 为权威列表**；`pull_turn_context` 返回的是**只读快照**，仅以 `push_turn` 推进状态（宿主不得假设跨 `pull` 的「实时连接视图」）。
3. **Checkpoint 与 PRE 的次序（必须）**：`message_start_idx` 记录在 **① CHECKPOINT 时刻**的 `len(messages)`，即 **② PRE-HOOKS（注入 skill system 消息等）开始之前**的边界。因此 **scope 内消息** = 从该索引起到当前列表末尾；`replace_from_checkpoint` 表示 **丢弃自该索引起的全部消息** 并替换为宿主给定子列表。PRE 注入的内容**属于 scope 内**，不计入「pre-scope」前缀。
4. **Skill prompt 标记（引擎独占）**：带 `metadata["skill_prompt"] = True` 的 **SYSTEM** 消息**仅允许由引擎**在 PRE 阶段注入；宿主传入的 `Message` 若携带该键，实现**必须剥离或拒绝**（`ValidationError`/`RuntimeError`），防止伪造污染 raw 过滤与审计语义（与 v1 Fix #1 一致）。
5. **Recall 工具**：`memory_expand` / `memory_search` 的**结果补全**在 **`push_turn` 提交路径上、返回宿主之前**执行（见 §4.2.3、§9）；`pull_turn_context` 所见的列表可能仍含**未闭合**的 memory_* 调用，属正常。
6. **Skill 工具与关闭报告**：`skill_end` 触发的 scope **finalize** 中，**scope 内折叠摘要（⑤ 的正文）以工具入参/约定 report 为准**，**不**再调用 Context Stack 内置 **Summarizer LLM**（§4.6.2）；TOOL 返回的结构化 **report** 仍须让模型确认「本层已闭合」。
7. **堆栈在 Context 中可见**：**在 `skill_begin` 成功时**向 **权威 `messages` / RO `context`** 追加 **栈镜像片段**（§4.6.3），使后续每一轮 LLM 读到的都是**写进历史的打开状态**，而非仅运行时临时注入。**自动 Meta**（§4.6.7）成功时**同样**写入快照，并带 **`auto_meta`** 标记。
8. **无孤儿 LLM（可配置）**：当 **`auto_meta_when_stack_empty=True`** 时，**每次**进入 LLM 前若栈空则 **自动 `_begin_scope(MetaSkill)`**，保证任意 LLM 调用都落在某一 skill scope 内（至少 Meta）。
9. **嵌套下潜折叠（可配置，默认关）**：见 §4.6.8；**默认 `nested_skill_fold=False`**（首版生产先证 flat 栈 + 恢复，再开折叠）。与 **`skill_end` 最终 report**（§4.6.2）独立。

### 2.3 信任边界与安全前提

- **宿主在信任边界内**：任何能改写 **权威 `messages`** 或伪造工具结果的代码都能操纵对话历史；**对外不暴露 `begin_scope`** 可减少「误开 scope」面，但不能替代运行时 **鉴权 / 租户隔离**（Gateway / Worker / Agent 绑定）。
- **Store**：多租户场景下，`store` 实例必须 **按租户或 runtime 隔离**；禁止在多个信任域之间共享同一 `MemoryBackend` 而不加键前缀/行级隔离。
- **checkpoint_blob**：持久化载荷含 `messages` 与 `meta`，须 **防篡改与加密**（MAC/签名、可选字段级加密、与 `scope_id`/任务身份绑定）；否则恢复等价于执行攻击者选定上下文。
- **engine_config_hash**：对 **规范化后的 `CompactConfig`（及任何影响序列化/语义的引擎构建参数）** 做 **SHA-256**（或更强）摘要；文档写明参与哈希的字段列表；**version 与包 semver** 的对应关系在 CHANGELOG 维护（见 §十五）。
- **日志与 Trace**：默认 **INFO 不得打印完整 message body 或 tool 输出**；调试需显式开关并脱敏。Summarizer 外发 LLM 时，摘要请求含全量 scope 内容，须在集成文档中说明 **数据出境/留存** 责任（§5.3）。
- **引擎独占元数据键**：除 `skill_prompt`（§2.2 不变量 4）外，**`skill_stack_snapshot`、`skill_fold`、`auto_meta`、`origin=engine`** 等保留键 **仅允许引擎写入**；宿主/模型伪造的同名 `metadata` **须剥离或拒绝**，防止伪造栈深与折叠态（与审计、展开恢复一致）。
- **`skill_end` 入参**：`user_visible_summary` / `report` 视为 **不可信用户内容**——须 **最大长度、schema、可选注入扫描**；高保证场景结合规则抽取字段与网关审计，**勿**单独采信模型 narrative。

### 2.4 四条「摘要 / 压缩」机制对照（防混淆）

| 机制 | 触发 | 是否走 scope **⑤⑥ finalize** | 是否调用 **`Summarizer.summarize`（狭义）** | 改权威 `messages` |
|------|------|-------------------------------|-------------------------------------------|-------------------|
| **路径 A：`skill_end`** | 模型关栈顶 scope | **是**（⑤⑥） | **否**（正文用工具入参；**除非** Fallback §4.6.2） | **是**（⑥ RELOAD） |
| **路径 B：`push_turn(done)` 非 skill_end** | 测试 / 程序化关 scope | **是** | **是**（Stub 或 HTTP） | **是** |
| **`prepare_messages_for_llm` 内 _maybe / _emergency** | 每轮 LLM 前阈值 | **否** | **否**（**不得**调用 finalize ⑤ 的 Summarizer；若内部 auto 段需 LLM，须为 **独立预算压缩路径**，与 ⑤ 区分） | **是**（须遵守 checkpoint / **禁删 `skill_fold` 占位** §4.6.8） |
| **§4.6.8 嵌套折叠 / 展开** | 下潜 `skill_begin` / 子层 `skill_end` | **否** | **`stub` 为默认**；`nested_fold_summarizer=llm` 时用 **同一 `Summarizer` 协议实例 + 独立 prompt**（§4.6.8），指标/span 用 **`nested_fold`** 标签，与 ⑤ 分列 | **是**（占位 ↔ stash） |

**术语**：**「Summarizer LLM（狭义）」** = `Summarizer.summarize` / `StructuredSummarizer` 用于 **scope finalize ⑤**；**不得**与「预算压缩里为减 token 调用的 LLM」口语混称「同一个 Summarizer」而不看上下文。

---

## 三、架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        ContextEngine (v2)  ← 对外只接这里             │
│  match / prepare_messages_for_llm / status / registry / hooks   │
│  可选: pull_turn_context / push_turn → 转发内部「栈顶 scope」       │
│  内置工具定义: skill_begin / skill_end + Recall memory_*          │
└────────────────────────────┬────────────────────────────────────┘
                             │ 内部仅：skill_begin 内调 _begin_scope 等
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           （内部）SkillStack → ScopeSession / 六步状态机          │
│  ①…③ EXECUTE* → finalize：④ POST → ⑤ SUMMARIZE* → ⑥ RELOAD            │
│  *Skill 经 skill_end：⑤ 默认不跑 Summarizer LLM；例外见 §4.6.2 Fallback │
│  *与 §4.6.8 嵌套折叠 LLM（`nested_fold_summarizer=llm`）无关            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              宿主：LLM + 工具执行；skill_* 交给引擎 dispatch         │
└─────────────────────────────────────────────────────────────────┘
```

**集成速览（Read me first）**：

1. **主路径（推荐）**：**`prepare_messages_for_llm` →（NovAIC：`expand_messages_for_llm` 顺序见 §4.6.9）→ LLM**；工具轮 **`skill_*` / `memory_*` 经引擎 dispatch**；**finalize 以模型 `skill_end`（路径 A）为主**；**宿主不调用 `begin_scope`**（§4.0）。  
2. **可选路径**：`pull_turn_context` / `push_turn` 供 **Task Worker / 显式步进**（§4.0）；**不是**所有宿主的必选项。  
3. **预算**：**只**通过 `prepare_messages_for_llm` 做阈值压缩，**不**对外 `maybe_compact`；栈非空时与 `_ScopeSession` 协同（§4.4）。  
4. **两条 finalize 摘要源**：**`skill_end`** → 工具 report（⑤ 无狭义 Summarizer LLM，除 Fallback）；**程序化 `push_turn(done)`** → 路径 B（§9.1）。

---

## 四、公开 API 设计

### 4.0 对外边界（订稿：**不暴露** `begin_scope` / `ScopeSession`）

**结论**：集成方 **只依赖「Skill 工具 + `ContextEngine` 编排面」**；**Scope 六步状态机、`begin_scope`、`ScopeSession` 均为包内实现细节**，**不**列入稳定公开 API（不导出、不保证签名长期不变）。单元测试与 fork 若需直达内部，使用 **`context_stack._internal.*` 或文档标注的 debug 入口**，不作为 semver 承诺。

**对外应暴露的能力**：

| 类别 | 内容 |
|------|------|
| **引擎门面** | `ContextEngine`：`match`、**`prepare_messages_for_llm`**（**唯一**对外上下文压缩入口；内建阈值温和/激进逻辑）、`status`、`registry`、`hooks`（§4.1、§4.4） |
| **Skill 边界** | 内置 **`skill_begin` / `skill_end`** 的 **工具 schema**（JSON）+ 由 **`SkillToolRouter` / 统一 dispatch** 在工具执行阶段回调引擎内部逻辑 |
| **Recall** | `memory_expand` / `memory_search` 同上 |
| **被动步进（可选）** | 若宿主仍需「拉快照 / 推全量」：仅暴露 **`engine.pull_turn_context()` / `engine.push_turn(payload)`**，语义为 **「当前 Skill 栈顶 scope」**；**不**返回 `ScopeSession` 句柄，**不**暴露 `begin_scope` |

**宿主禁止**：直接调用 **`begin_scope`**、持有 **`ScopeSession`**、或在无 `skill_begin` 的情况下伪造栈顶 scope（除非使用标注为内部的测试 API）。

**集成分层**：**Tier A（主路径）** — `prepare_messages_for_llm` + 统一工具 dispatch（`skill_*` / `memory_*`）+ 模型 **`skill_end`**；**Tier B（Worker / 显式步进）** — 在 A 之上叠加 **`pull_turn_context` / `push_turn`**、checkpoint、幂等。**跨进程恢复时**：在 checkpoint **未**序列化 §4.6.8 的 stash / 占位关联（§8.1）前，**不得**假定折叠态可恢复；默认视为 **仅同进程内** 特性或 **M3+** 与 blob 同步交付。

---

### 4.1 `ContextEngine`

**职责**：构造默认依赖；**对外**提供匹配、**`prepare_messages_for_llm`**（含预算压缩）、状态、注册表与钩子；**内部**维护 SkillStack 与 Scope 状态机；可选提供 **转发到栈顶** 的 `pull_turn_context` / `push_turn`。

建议签名（示意）：

```python
class ContextEngine:
    def __init__(
        self,
        *,
        config: CompactConfig | None = None,
        store: MemoryBackend | None = None,
        summarizer: Summarizer | None = None,
        counter: TokenCounter | None = None,
    ) -> None: ...

    # 对外稳定
    def match(self, task: str, ...) -> Skill | None: ...
    def status(self, messages: list[Message] | None = None) -> StackStatus: ...

    # 每次 LLM 前：auto Meta（若栈空）+ 阈值压缩（原 maybe/emergency 逻辑内聚于此，不另开 API）
    def prepare_messages_for_llm(self, messages: list[Message]) -> list[Message]: ...

    # 可选：被动步进（转发栈顶内部 Session，不暴露 Session 类型）
    def pull_turn_context(self) -> TurnContext: ...
    def push_turn(self, payload: TurnPayload) -> LifecycleResult | None: ...

    # 生命周期管理
    def close(self) -> None: ...
    def __enter__(self) -> "ContextEngine": ...
    def __exit__(self, *exc) -> None: ...
```

- 所有构造参数 **可选**；`None` 一律使用库内默认实现（§6）。
- **移除**对外必填的 `executor`；LLM 循环在引擎外，**scope 开闭仅经 `skill_*` 工具（+ 内部 `_begin_scope`）**。

**`registry` / `hooks`**：保留。

**`close()` 与上下文管理器**：`ContextEngine` 可能持有 Store（SQLite 连接）、Lock、后台统计等资源。**`close()`** 负责释放这些资源（关闭 Store 连接、清理 stash 缓存等）。支持 **`with`** 上下文管理器（`__enter__` / `__exit__`），`__exit__` 内调用 `close()`。**`close()` 后**再调用任何引擎方法 → **`RuntimeError`**。M1 实现中 `close()` 至少关闭 Store；后续版本可扩展（后台线程清理、指标导出等）。

**与内部分工**：**仅** `prepare_messages_for_llm` 改写「将发给 LLM 的」消息列表；`status` 只读。**栈顶 EXECUTING** 期间压缩须遵守 §4.4，避免破坏 checkpoint。

### 4.2 内部实现参考：`ScopeSession` / `_begin_scope`（**非公开 API**）

以下描述 **包内行为**，供实现者与贡献者阅读；**集成方以 §4.0 为准**。

推荐 **显式阶段 + Turn 拉推**，便于持久化与日志。

#### 4.2.0 合法调用序列与可观测 Phase

- **`_begin_scope` 成功后**：内部 `session.phase == EXECUTING`（**不**单独暴露 `CHECKPOINT` / `PRE` 子阶段给宿主）。
- **`pull_turn_context`**：
  - 在 `EXECUTING` 下 **任意次**允许；多次 `pull` 在未介入 `push_turn` 时 **返回等价快照**（同一 turn 内幂等读）。
  - **推荐**模式：`pull` → 宿主工作 → `push` → 再下一 turn `pull`……
- **`push_turn`**：在 `EXECUTING` 下推进权威 `messages`；可与 `pull` **串行**交替，**禁止**同一 Session 上并发 `pull_turn_context` 与 `push_turn`（§十）。
- **终止路径（唯一）**：`push_turn(..., done=True)` **同步触发** ④ POST → ⑤ SUMMARIZE → ⑥ RELOAD，完成后 `session.phase == CLOSED`。**不再**依赖隐式 `close()` 完成生命周期。
- **`finalize_result` 读取**：`push_turn` 在 `done=True` 时返回 `LifecycleResult`，或提供 `session.last_result` / `session.get_result()`（实现二选一，文档与类型统一即可）。
- **`session.close()`**（可选保留）：**仅**用于 **CLOSED 后**释放句柄/连接；若在未 `done` 时调用 → **`RuntimeError`**（禁止「隐式 done」歧义）。
- **`session.abort(reason=..., summarize: bool = False)`**：在 `EXECUTING` 下终止；`summarize=True` 时走简短 SUMMARIZE+RELOAD，`False` 时直接丢弃 scope 不写 store（或仅写 tombstone，实现定义），然后 `CLOSED`。

#### 4.2.1 创建

```python
# 内部示意（不对外导出）：
session = engine._begin_scope(  # 或 SkillToolRouter 内调用
    skill: Skill,
    messages: list[Message],
    *,
    task: str = "",
    meta: dict | None = None,
) -> _ScopeSession
```

`_begin_scope` 内部顺序：**① CHECKPOINT**（记录 `message_start_idx = len(messages)`）→ **② PRE-HOOKS**（注入 prompt、跑 pre-hooks，**追加**到 `messages`）→ `session.phase = EXECUTING`。  
**唯一对外开 scope 路径**：模型调用 **`skill_begin`** → 引擎解析后调用 **`_begin_scope`**。

#### 4.2.2 宿主拉取「本回合输入」

```python
turn_ctx = session.pull_turn_context() -> TurnContext
```

`TurnContext` 字段：

| 字段 | 含义 |
|------|------|
| `scope_id` | 当前 scope |
| `messages` | 当前完整消息列表的 **只读视图**（默认不 deep copy；宿主禁止原地变异） |
| `extra_tools` | 本 scope **最终**可用工具 schema（见 §4.5） |
| `skill` | 当前 Skill 快照（只读） |
| `recall_router_enabled` | 为 `False` 时，本回合 `push_turn` **不**自动补全 memory_*（宿主自管或回放）；默认 `True` |
| `token_estimate` | 可选；**默认在 `push_turn` 后增量更新**，避免每次 `pull` 全量 tiktoken（实现可优化为尾部重算） |
| `turn_id` | 单调递增整数，供日志与幂等（§8.3） |
| `correlation_id` / `task_id` | 可选字符串，由 **内部** `meta` 或引擎工厂注入，贯穿 trace（§十一） |
| `trace_context` | 可选：W3C `traceparent` 或 Opaque，用于跨 `pull→LLM→push` 续接 span（§十一） |
| `skill_stack` | **只读**：与引擎权威栈一致；**模型侧主真相**为 **已在 context 中插入的栈快照**（§4.6.3，`skill_begin` 时写入） |

#### 4.2.3 宿主推回「本回合输出」

```python
session.push_turn(
    payload: TurnPayload,
) -> LifecycleResult | None

# TurnPayload 建议为显式类型（可与 dict 等价，但文档以类型为准）：
@dataclass
class TurnPayload:
    messages: list[Message]       # M1：见 §4.2.5
    mode: Literal["full", "replace_from_checkpoint"] = "full"
    done: bool = False
    error: str | None = None
    idempotency_key: str | None = None  # 可选，§8.3
```

**M1 语义（与 `mode` 的关系）**：

- **`mode="full"`（默认）**：`messages` **必须**为当前回合结束后的 **完整会话列表**（含 pre-scope 前缀 + scope 内全部消息），且长度与内容与引擎权威列表在 **replace 语义**下一致：实现将用 `messages` **整体替换**引擎内部从 0 起的列表，并校验 `messages[:message_start_idx]` 与引擎 pre-scope 一致，否则 `ValidationError`。**校验策略（前缀哈希快速路径）**：M1 阶段 **推荐**使用 **前缀哈希校验**替代字节级全量深度比较——在 `_begin_scope`（① CHECKPOINT）时对 `messages[:message_start_idx]` 计算 **SHA-256 摘要**并缓存到 `StackFrame.prefix_hash`；`push_turn(mode="full")` 时仅比较 `hash(payload.messages[:message_start_idx]) == prefix_hash`，**不**逐条深度相等比较。**降级**：`debug=True` 或 `CompactConfig.full_prefix_validation=True` 时走 **完整逐条比较**（用于排查 hash 碰撞或序列化差异）。此策略将每轮校验从 O(n) 降至 O(1)（哈希已缓存时）。  
  **禁止**在 M1 仅传「本轮 delta」却使用 `mode="full"`。  
- **`mode="replace_from_checkpoint"`**：`messages` 表示 **自 `message_start_idx` 起的新子列表**；引擎执行 `messages = pre_messages + payload.messages`，其中 `pre_messages = internal[:message_start_idx]`。用于宿主分支重做；与 Worker 重试故事对齐时，`idempotency_key` 应区分 logical turn vs attempt（§8.3）。
- **`done=True`**：在本 `push_turn` 内先完成 **Recall 补全**（若启用），再跑 ④⑤⑥，返回 `LifecycleResult`；此后 `phase=CLOSED`。（若本 finalize 由 **`skill_end`** 触发，⑤ 按 §4.6.2 **省略 Summarizer LLM**。）
- **`done=True` 且从未产生任何「有效」EXECUTE 内容**：**允许**（零 turn scope），POST/SUMMARIZE/RELOAD 仍执行，摘要可为空转模板。
- **`error` 与 `done`**：见 §七矩阵。

**Recall 补全（时间线）**：仅在 **`push_turn` 内部**、对**即将提交的**列表扫描未闭合的 `memory_expand` / `memory_search`（与 v1 `RecallToolRouter` 一致），插入 `TOOL` **之后**再进入 `done` 触发的 POST。`pull_turn_context` **之前**可能仍见未闭合 tool 调用。

**工具表示**：实现须支持 **至少一种**规范格式，并在文档写明：  
  (A) `Message.role == ASSISTANT` 且 `tool_name` / `tool_input` 填充；或  
  (B) 宿主适配层将 provider `tool_calls` 转为 (A)。  
  **禁止** silent 忽略与 memory_* 成对的结构，导致 Recall 漏补全。

#### 4.2.4 对称类型命名

- **`TurnContext`**：输入快照。  
- **`TurnPayload`**：输出提交（上节）。  
可选别名 `TurnOutput` = `TurnPayload`，便于检索与代码生成。

#### 4.2.5 M1 全量列表策略（已定稿）

| 版本 | 宿主传参 | 说明 |
|------|----------|------|
| **M1** | 每回合 `TurnPayload.messages` 在 `mode="full"` 下为 **全量列表** | 实现简单、易校验 tool 配对；**前缀校验用哈希快速路径**（§4.2.3），避免 O(n) 深度比较 |
| **v2.1+** | 引入 `append_messages: list[Message]` 或纯增量 API | 降低拷贝与序列化开销 |

### 4.3 （已合并至 §4.2.5 / §4.2.3）

原「增量 vs 全量」表格由 §4.2.5 取代，避免与 `push_turn` 默认 `mode` 冲突。

### 4.4 上下文预算压缩：**不对外暴露 `maybe_compact` / `emergency_compact`**

**订稿**：v1 风格的 **`maybe_compact` / `emergency_compact` 不作为 `ContextEngine` 公开方法**；其语义（温和 micro/auto、激进 emergency）**全部内聚**在 **`prepare_messages_for_llm`** 内部，由 **`CompactConfig` 阈值**驱动。宿主**只调** `prepare_messages_for_llm`，避免「又调 maybe 又调 prepare」重复压两遍。

- **CHECKPOINT 一致性**：内部 `message_start_idx` 相对于 **`skill_begin` / auto Meta 开 scope 时**列表快照；`prepare_messages_for_llm` 在 **有未闭合栈顶 scope** 时**不得**做破坏该索引的全表替换，除非实现显式支持「只压 checkpoint 前前缀」并与 `_ScopeSession` 同步（§4.4.1）。  
- **禁止**：宿主在引擎外对**同一条**权威 `messages` **并行**另一套压缩再写回 RO，与引擎内栈状态冲突。

#### 4.4.1 `prepare_messages_for_llm`：唯一入口与内部阶段

**调用点**：每次从 RO/内存取出 `messages`、在 **`expand_messages_for_llm` / `llm.call` 之前**（NovAIC `llm_handlers` 对齐）。

**内部强制拆分为两个独立 Phase**（禁止合并为单一函数体）：

```text
prepare_messages_for_llm(messages)
  ├── Phase A: _ensure_stack_ready(messages)   → 只处理栈状态
  │     └── ensure_auto_meta（§4.6.7）：栈空则 _begin_scope(MetaSkill) + 栈快照
  │     └── 独立 span: context_stack.prepare.stack_ready
  │     └── 独立错误路径：栈操作失败不影响 Phase B 判断
  │
  └── Phase B: _budget_compact(messages)       → 只做纯 token 预算压缩
        └── TokenCounter + CompactConfig 算 usage_ratio
        └── usage_ratio >= emergency_threshold → _emergency_compact（不导出）
        └── 否则若 >= compact_threshold → _maybe_compact（不导出）
        └── 否则原样（可仍过 micro 无损截断）
        └── 防抖：同轮去重 / 冷却，避免每请求 O(n) 抖动
        └── 独立 span: context_stack.prepare.budget_compact
```

**Phase 拆分理由**：`prepare_messages_for_llm` 同时承担「栈状态变更（可能开 scope、写消息）」和「纯 token 预算压缩（只删/缩消息）」两个**正交**职责。合并在一个函数体内时，故障排查难以定位「是栈操作改了消息还是压缩改了消息」。拆为两个 Phase 后：

- **Phase A** 的 span 可独立监控 auto_meta 注入频率与耗时；
- **Phase B** 的 span 可独立监控压缩命中率与 token 节省；
- 各自的错误路径清晰：Phase A 失败（栈状态异常）不应静默掩盖为 Phase B 的「无需压缩」。

**调用顺序（严格）**：Phase A **必须**先于 Phase B——避免无 scope 时对索引不明的列表先压再开 scope（与 §4.6.7 `ensure_auto_meta` → compact 的次序一致）。

**与 scope finalize ⑤（关键区分）**：内部 **`_maybe_compact` / `_emergency_compact`**（Phase B）只服务 **「发给 LLM 的整条 `messages` 预算」**，**不是** ⑥ 的「单 scope 折叠写回」；**不得**在此路径调用 **`Summarizer.summarize`（狭义）** 充当 **⑤ 主摘要**。若实现选择用 **独立 LLM** 做全局预算压缩，须 **独立配置与 instruction**，且 trace 上 **与** `context_stack.scope.summarize`（⑤）**分列**，避免运维误判「每轮都在 finalize」。与 §2.4、§9.1「非 scope 压缩边界」一致。

**与 Skill 栈**（Phase B 约束）：

- **栈非空**：仅允许 **不破坏 scope 边界** 的压缩（前缀、micro 截 tool 等），由引擎与 **`_ScopeSession`** 协同。  
- **栈空**（含仅 auto Meta）：可按阈值全量走温和/激进内部路径。

**运维 / 测试**：若需「强制压一次」，可暴露 **debug / `_internal` 钩子**，**不**列入稳定 semver API；或临时调低 `compact_threshold` 走正常 `prepare_messages_for_llm`。**Phase A 与 Phase B 可独立测试**：单测 Phase A 时 mock TokenCounter 使 Phase B 空转；单测 Phase B 时 mock SkillStack 使 Phase A 空转。

### 4.5 `extra_tools` 与 Skill 工具交集

- **定义**：`TurnContext.extra_tools` = **（Skill.allowed_tools ∩ 宿主注册能力）∪ Recall 工具（若本 scope 为 RECALL 且 recall 未关闭）∪ `skill_begin` / `skill_end`（§4.6）**。  
- **宿主**负责执行 **除 `memory_*` 与 `skill_begin`/`skill_end` 外** 的所有在 `extra_tools` 中出现的工具；**memory_*** 默认由引擎在 `push_turn` 补全；**skill_*** 由 **`SkillToolRouter`**（或等价）在 tool 执行阶段解析并操作 **SkillStack**（§4.6）。  
- **越权调用**：若模型调用了不在 `extra_tools` 中的工具，宿主 **不应**伪造 TOOL 结果；应记 `scope.errors` 或在 `push_turn` 前修复消息；具体 **拒绝 vs 记错** 策略由产品在宿主层定，引擎可对明显结构违规 `ValidationError`。

### 4.6 Skill 边界工具、关闭 Report、Context 堆栈镜像与 LLM 堆栈意识

> **产品决策**：Skill 的**打开与关闭**通过**工具调用**驱动；关闭时**必须**返回可读的 **report/summary 结果**；**打开状态**在 **`skill_begin` 成功时写入 context**（插入消息，随对话持久化），使 **LLM 从 transcript 即可读栈**，主动维护 **LIFO** 闭合。

#### 4.6.1 内置工具（名称示意）

| 工具 | 作用 |
|------|------|
| **`skill_begin`** | 参数：`skill_name`（须在 Registry 或 Meta 规则内）、可选 `task`、`reason`。引擎 **压栈** → **内部** **`_begin_scope`**（注入对应 Skill 的 PRE）。**随后将「当前完整 skill 栈快照」插入权威 context**（见 §4.6.3，与 TOOL 返回配套）。TOOL 返回：确认 `scope_id`、深度、`skill_name`、可选栈 JSON。 |
| **`skill_end`** | 参数：**必填或强约束** `user_visible_summary` / `report`（模型对本轮 skill 的结论文本或结构化体）。引擎对**栈顶** finalize：**④ POST** → **⑤ 跳过 Summarizer LLM**，**摘要正文 = 工具提交内容（经校验/长度裁剪）** → **⑥ RELOAD**；再组装 TOOL 返回 JSON（可含 `scope_id`、`tokens_saved` 等）。栈顶弹出。见 §4.6.2。 |

- **执行者**：与 `memory_*` 类似，推荐 **`SkillToolRouter`**（或并入统一 `ContextToolRouter`）：在 **ReactActions / 宿主 tool 管道**中由引擎处理，避免业务工具服务器实现栈语义。
- **白名单**：`skill_name` **必须**解析为已注册 Skill 或 Meta；未知名称 → TOOL 返回错误字符串，**不**压栈。
- **嵌套策略**：默认 **允许嵌套**（内层先 `skill_end`）；若产品只要单层，配置 **`max_skill_depth=1`**，`skill_begin` 在非空栈时返回错误。

#### 4.6.2 `skill_end` 的 Report / Summary 与 **⑤ 不再由 Context Stack 执行 LLM**

**定稿**：经 **`skill_end`** 关闭的 scope，**折叠进对话的那条「scope 摘要消息」的正文**来自 **模型在 `skill_end` 工具调用里提交的内容**（如 `user_visible_summary` 或 `report.summary`），**不再**由 Context Stack 调用内置 **`Summarizer`（LLM）** 生成。这样 **⑤ SUMMARIZE** 在 Skill 路径上退化为 **「采纳工具 report」**（+ 可选纯规则元数据，见下），避免 **二次 LLM**、也让结论文责在调用方模型。

**仍执行**：

- **④ POST-HOOKS**（校验、指标、元数据收集）照旧。
- **⑤ 的可选子步骤**：可对 scope 内消息做 **无 LLM** 的规则抽取（decisions/files/tools 计数），写入 `ScopeRecord` / store，**不**覆盖模型给出的主摘要正文。
- **⑥ RELOAD**：用上述正文生成 **单条摘要消息** 替换 scope 内 raw（与现设计一致）；raw 落盘、token 统计照旧。

**TOOL 返回 JSON**（示例字段，可与入参 echo + 引擎补字段）：

- `scope_id`, `skill_name`, `depth_after_pop`
- `summary`：**应与写入对话的折叠正文一致**（或明确为「模型提交 + 引擎裁剪版」）
- 可选：`decisions` / `files_changed` / `tools_used`（可来自规则抽取，非 LLM）
- `errors`, `tokens_saved`, `ok`

**与 `push_turn(done=True)` 的关系**：宿主驱动的 **纯 Session finalize**（无 `skill_end`）仍走 **④ → ⑤ Summarizer LLM → ⑥**；**仅 Skill 栈顶 `skill_end`** 触发 **⑤ 跳过 Summarizer**。

**Fallback**（须实现其一并文档化）：

- `skill_end` **未提供**或 **空摘要** → `stub` 固定模板 / 单行错误说明，或配置 **`skill_end_empty_fallback=engine_summarize`** 时 **仅此情况**调用一次 Summarizer。

**Report 质量 Post-Validation Hook（可选，M2）**：

摘要质量与诚实度依赖模型；除 Fallback 外，引擎支持可选的 **`SkillEndReportValidator`** 钩子，在 ⑤ 采纳 report 前对内容进行校验：

```python
class SkillEndReportValidator(Protocol):
    def validate(self, report: str, scope: ScopeRecord) -> str | None:
        """返回 None 表示通过；返回字符串表示拒绝原因。
        拒绝后引擎在 TOOL 返回 JSON 中附加 error + rejection_reason，
        要求模型重新 skill_end 并提交更详细的 report。"""
        ...
```

- **默认不启用**（`config.skill_end_report_validator = None`），避免模型反复被拒导致死循环。
- **启用时须配置 `max_skill_end_retries`（默认 1）**：超出重试次数后走 Fallback（Stub 或 `engine_summarize`）。
- **示例校验规则**：最小长度（如 `len(report) >= 20`）、禁止纯重复字符、可选正则匹配必填字段（如 `files_changed` 不为空）。
- **注册方式**：`engine.hooks.register_skill_end_validator(validator)` 或构造参数 `config.skill_end_report_validator`。
- **与 POST-HOOKS 的关系**：Validator 在 **④ POST-HOOKS 之后、⑤ 采纳 report 之前** 执行；拒绝后 **不进入 ⑤⑥**，而是返回 TOOL error 让模型重试 `skill_end`。

**权衡**：宿主还可通过 **最大长度 / 禁止空 / schema 校验**（在 `skill_end` 工具 schema 层面）降低胡编风险。TOOL 返回仍须可读、可审计；宿主可将 JSON **原样**写入 `TOOL` 的 `content`，供下一轮 planning。

#### 4.6.3 在 Context 中体现「打开状态」（堆栈镜像）

**主路径（已定稿）**：在 **`skill_begin` 成功、压栈且内部 `_begin_scope` 完成后**，立刻向 **权威消息列表**（进而 **NovAIC `CONTEXT_APPEND` / RO `context`**）**追加一条（或固定一对）可见消息**，内容为 **当前完整 skill 栈的快照**，而非仅在 `pull_turn_context` 时临时拼进 prompt。

- **形态（已定稿：统一 `role=system`）**：追加一条 **`role=system`**，正文为短文本 + 可选 JSON，例如：  
  `## Skill stack (after begin)\nTop→bottom (inner→outer):\n1. code-review scope=abc12\n2. meta scope=def34`  
  **不使用 `role=user`**。理由：(1) `user` role 消息会被部分模型（Claude、Gemini）解释为用户发言，可能触发不必要的回复；(2) `system` 消息在大部分 provider 中被视为环境注入，不会被模型当做需要回应的内容；(3) 与 `skill_prompt`（也是 `system`）保持一致，减少认知负担。
- **元数据**：`metadata["skill_stack_snapshot"]=True`，**不要**与 `skill_prompt` 混用；**RELOAD / raw 落盘**时与 `skill_stack_mirror` 同样规则：**可过滤**不进长期 raw，或**保留**以便 Recall 能重建栈历史——由 `CompactConfig` 或产品开关二选一，**默认建议过滤**以省 token。
- **与 TOOL 消息顺序**：同一轮工具执行中，顺序建议为：`assistant(tool_calls skill_begin)` → **`tool`（skill_begin 返回值）** → **`system`（栈快照插入）** → 后续消息；保证模型下一轮先读到 tool 结果再读到**持久化**的栈文本（或合并为 tool 内容极长时，仍以 **单独 system 行写入 context** 为主，避免 tool 结果超长被截断丢栈信息）。
- **`skill_end` 时（推荐对称）**：finalize 后除 TOOL report 外，可再追加一条 **`## Skill stack (after end)`** 反映弹出后的栈（空栈则显式写 `empty`），便于 transcript 连贯；**至少**依赖 `skill_end` 的 TOOL JSON 也可，但**打开态**必须以 **begin 时插入**为准。

**辅助（非替代）**：

- **`TurnContext.skill_stack`**：与引擎 **`SkillStack` 权威状态**一致；可用于 UI、`pull` 时校验，**不能**替代「已写入 messages 的快照」作为唯一真相。
- **仅 pull 时拼 banner**：仅作调试或旧宿主兼容；**正式集成必须以 begin/end 时写入 context 为主**。

**不变量**：已追加的栈快照与引擎内部 **`SkillStack` 在同一提交点**一致；禁止只更新内存栈而不追加消息（或只改 prompt）。

#### 4.6.4 LLM 堆栈维护意识（提示与约束）

- **系统提示模板**（库可提供默认英文/中文片段）：明确写出  
  - 引擎可能已 **自动打开 MetaSkill**（栈快照中带 `auto_meta`）；若要做领域任务可再 **`skill_begin(具体 skill)`**（栈深按 §4.6.7 配置增长或替换）。  
  - 完成时用 **`skill_end`**，并阅读返回的 **report**；**仅 Meta(auto)** 时是否允许模型 `skill_end` 掉由产品定（通常保留底 Meta 直到会话结束）。  
  - **嵌套时**必须先 end **内层**再 end 外层；  
  - 当前打开列表以 **对话里最近一次 `## Skill stack (after begin)` / `(after end)` 与 `skill_begin`/`skill_end` 的 TOOL 结果** 为准（均以写入 context 的为准），勿与已过期的 mental stack 冲突。
- **违规检测**：若模型在未打开 skill 时调用仅允许栈内使用的工具，宿主可返回 TOOL 错误并引用当前 `skill_stack`。
- **兜底**：超时 / 最大步数 / 进程恢复时，宿主可 **自动 `skill_end` 栈顶** 并带 `error` 报告，避免永久泄漏；行为写进运维文档。

#### 4.6.5 与 NovAIC `react_think` / `react_actions` 的衔接

- **`skill_*` 与 `memory_*` 同属「引擎解析工具」**：宜在 **同一执行顺序**中优先处理（例如先闭合 recall，再 skill，再业务工具——具体顺序在实现中固定并文档化）。**完整约束**（RO 镜像、`prepare`/`expand` 顺序、幂等）见 **§4.6.9**。
- **一轮 Actions** 内可同时存在多个 tool_calls：`skill_begin` → 业务工具 → `skill_end` 的顺序由 **模型**决定；宿主按 **拓扑或声明顺序**执行时，须保证 **skill_end 只对应当前栈顶**。

#### 4.6.6 `extra_tools` 扩展

- 全局或 Meta 模式下，**始终**在 `extra_tools` 中声明 **`skill_begin` / `skill_end`**（除非产品关闭 skill 栈特性）。
- 某一 Skill 若**禁止**子 skill，可在 Skill 元数据中 `allow_nested_skills: false`，引擎在 `skill_begin` 时若栈非空则拒绝。

#### 4.6.7 确保「一切都在 skill 里」：**栈空自动 MetaSkill**（订稿）

**目标**：不出现「没有打开任何 skill scope 就调 LLM」的**孤儿回合**；与 v1「Meta 兜底」一致，但 v2 用 **内部 `_begin_scope(MetaSkill)`** 实现，**不**要求模型先手动 `skill_begin(meta)`。

**触发（推荐主路径）**：在 **`prepare_messages_for_llm` / 每次组装 LLM 上下文之前**（或与 `pull_turn_context` 同一节拍），引擎执行：

```text
if skill_stack.is_empty():
    _begin_scope(MetaSkill.create(name="meta", task=...), messages, meta={"auto_meta": True})
    # 并写入与 §4.6.3 一致的栈快照，建议 metadata 带 auto_meta / origin=engine
```

**条件**：仅当 **`SkillStack` 为空**；若模型已 `skill_begin` 或上一轮未 `skill_end` 完，**不**重复插入第二个 Meta。

**`skill_end` 弹出后栈变空**：下一波 LLM 前会再次命中上述逻辑 → **自动再开一层 Meta**，形成「永远至少有一层 Meta」除非显式关闭特性。

**与模型显式 `skill_begin` 的关系**（二选一，**配置项**）：

| 模式 | 行为 |
|------|------|
| **`stack_under_auto_meta`（默认）** | 自动 Meta 在底；模型 `skill_begin(X)` → 栈 `[meta(auto), X]`；须先 `skill_end` X 再 `skill_end` meta（或只 end X 保留 meta，取决于是否允许空中间层——**建议** end X 后栈剩 meta(auto)，勿强制再 end meta 除非要关会话）。 |
| **`replace_auto_meta_on_explicit`（可选）** | 栈上**仅有**一层且为 `auto_meta` 时，模型 `skill_begin(X)` → **先内部弹出 auto meta** 再 `_begin_scope(X)`，栈为 `[X]`，减少双层。 |

**透明性**：自动 Meta 与显式 skill **共用同一套栈快照格式**（§4.6.3），并在快照或 `ScopeRecord` 上可区分 **`auto_meta`**，便于 UI 与审计。

**关闭特性**：`CompactConfig.auto_meta_when_stack_empty: bool = True` 设为 `False` 时，恢复「允许空栈调 LLM」（不推荐生产）。

**与 §4.4.1 顺序**：建议 **`ensure_auto_meta` → `prepare_messages_for_llm` 内阈值 compact`**，避免无 scope 时对索引不明的列表先压再开 scope。

**关闭「自动打开的 Meta（auto_meta）」与路径 A / B**：

- **推荐（生产）**：由模型对栈顶执行 **`skill_end`** → **路径 A**（§9.1）：⑤ **不**跑狭义 Summarizer LLM（除 Fallback），摘要正文来自工具入参；下一 LLM 前若栈空则 **`ensure_auto_meta`** 可再开一层 Meta（§4.6.7）。  
- **程序化关栈顶（含 auto Meta）**：若宿主用 **`push_turn(done=True)`** / 内部 finalize **且非** `skill_end` → **路径 B**：⑤ **会**调用 **`StructuredSummarizer` / Stub**；适用于测试、Worker 特殊收尾。**生产对话**应优先 **`skill_end`**，避免无意承担路径 B 的 **二次 LLM** 与摘要语义差异。

#### 4.6.8 嵌套 Skill：**进入子层时折叠父层 begin→当前，回到父层再展开**（订稿）

**前置**：本节逻辑仅在 **`nested_skill_fold=True`** 时启用（默认 **`False`**，§5.1）。

**目标**：模型进入 **更深层** `skill_begin` 时，**每一层被留在下面的 skill** 在对话里从「本层 `_begin_scope` 起点 → 进入子层前一刻」这一段不再以**全文**占用上下文，而是 **压成一条（或少量）折叠摘要**；**仅当栈再次弹回该 skill（子层 `skill_end` 之后）** 时，再把该层 **展开** 为完整消息段，继续在该层推理。

**与 `skill_end` report 的区别**：

| 机制 | 时机 | 作用 |
|------|------|------|
| **§4.6.8 层级折叠 / 展开** | **每次** `skill_begin` 压入子 skill **之前**；**子 skill `skill_end` 弹出之后** | **临时**省 token：父层在「下潜」期间只见摘要，**回到本层**恢复原文。 |
| **`skill_end` + report**（§4.6.2） | **关闭该 skill 事务** | **永久**折叠进一条 scope 摘要消息写回 transcript / store，**不是**简单的「展开回去」。 |

**触发 — 进入子层（`skill_begin` 且当前栈非空）**：

1. 设 **父帧** = 当前栈顶（即将被压在下面的那一层）。  
2. 取父层 **open 区间**：`[parent.message_start_idx, len(messages) - 1]`（或「进入子层 PRE 之前」的截断点，与实现一致后写死）。  
3. **切片** `raw_segment = messages[parent.message_start_idx :]`（子层 PRE 尚未 append 前）。  
4. **生成 `fold_summary`**：对该段做摘要（**不**等同于 `skill_end` 的模型 report；推荐 **引擎侧 Stub**；可选 **`nested_fold_summarizer=llm`** 时走 **同一 `Summarizer` 协议实现** + **`nested_fold_instructions`**（与 ⑤ finalize **分列**），span/指标用 **`nested_fold`** 标签，**禁止**裸旁路 HTTP 绕过统一超时、租户与日志）。  
5. **持久化父层 stash（分级策略）**：在 **父 `StackFrame`**（或并列 `FoldState`）保存 `raw_segment`，并在内存/元数据中标记 `folded_until_child=True`。**存储策略按大小分级**（`CompactConfig.nested_fold_stash_threshold`，默认建议 **30_000 chars**）：  
   - **小段**（`len(raw_segment) < stash_threshold`）：**内存 stash**（直接保存在 `StackFrame.stash_segment`），展开时零 I/O。  
   - **大段**（`len(raw_segment) >= stash_threshold`）：**外存降级**——将 `raw_segment` 写入 **Store 临时表 / 本地文件 / RO 大字段**，`StackFrame` 仅保留 `stash_ref: str`（引用 ID）+ `stash_hash: str`（SHA-256），展开时通过 `store.fetch_stash(stash_ref)` 读回并校验 hash。**防止**四层嵌套（`max_skill_depth=4`）时每层 ~30k token 的 `raw_segment` 同时常驻内存导致峰值 ~2x。  
   - **配置**：`CompactConfig.nested_fold_stash_threshold: int = 30_000`；外存后端复用 `MemoryBackend`（Store）实例或独立临时表（实现定义）。  
   - **清理**：外存 stash 在父层 **展开** 或 **abort** 后 **立即删除**；`engine.close()` 时清理所有残留 stash。  
6. **改写权威 `messages`**：将上述区间 **替换为** 少量消息（推荐一条 **`system` 或 `user` 占位**，`metadata["skill_fold"]=True`, `parent_scope_id=...`），正文为 `fold_summary` + 可选「子 skill 进行中，回到本层后恢复详情」提示。  
7. 再执行子层的 **`_begin_scope`**、栈快照（§4.6.3）等。

**触发 — 回到父层（子层 `skill_end` 完成并弹栈后）**：

1. 弹出子帧后，**新栈顶** = 父层。  
2. 若父帧存在 **stash 的 `raw_segment`**：  
   - **从 `messages` 中移除** 对应的折叠占位消息（靠 `metadata` / `scope_id` 定位）；  
   - **按原序插回** `raw_segment`（或与当前前缀拼接规则写死，避免双插）。  
3. 清除父帧 `folded_until_child`；此后 **本层** 继续正常 `push_turn` / LLM，直到再一次下潜或本层 `skill_end`。

**`prepare_messages_for_llm` 的关系**：

- **物化给 LLM 的视图** =：全局前缀（若有） + **各祖先层若处于 folded 状态则只含折叠摘要** + **栈顶层全文**（未折叠部分）。  
- 若 stash 与 `messages` 已同步维护，则 `prepare` 可 **直接**在现有列表上跑阈值压缩；**禁止**在父层仍 folded 时删掉占位导致 **无法展开**。  
- **全局** `compact_threshold` 处理：建议对 **折叠占位** 与 **栈顶段** 分级策略（占位已很短，主要压栈顶过长 tool）。

##### 4.6.8.1 形式化不变量与执行顺序（实现契约）

以下与 §2.2 不变量 3 一并作为 **单测 / 属性测试** 目标。

1. **`message_start_idx`（父帧）**：父层进入折叠时，**父** `StackFrame.message_start_idx` **不得**因占位替换而漂移；占位替换 **仅**改写 `[parent.message_start_idx, …)` 区间内消息，**不**改变「本 scope 自该索引起算」的语义（实现可用「逻辑起点 + 占位句柄」双轨，展开后须与 §2.2 不变量 3 一致）。  
2. **子层 checkpoint**：子层 **`_begin_scope`** 的 ① 记录在 **子 PRE 追加前**的 `len(messages)`（与 §4.2.1 一致）；折叠占位 **必须先**落盘，再执行子 ①②。  
3. **单个子 skill 的时序**：父折叠（stash + 占位）→ 子 `_begin_scope` + `skill_begin` 栈快照 → … → 子 **`skill_end`** → 子 scope **完整跑完** ④（POST）→ ⑤（路径 A 或 B 按子层是否经 `skill_end`）→ **⑥ RELOAD** → **栈弹出子帧** → **再**执行父层 **展开**（删占位、按序插回 `raw_segment`）→ 父层继续 `EXECUTING`。  
4. **多级下潜**：每一层父帧 **独立** `stash`；**展开**仅在 **直接子层** `skill_end` **之后**、且 **仅**恢复 **该**父帧占位，**LIFO** 与 skill 栈一致；**禁止**外层未 end 内层却展开祖先导致 transcript 与 `SkillStack` 不一致。  
5. **与 ⑥ 的区分**：嵌套折叠的占位 / stash **不是** scope finalize 的 ⑥ 产物；**不得**把「父层折叠」误走成「父层 `skill_end`」的 RELOAD。  
6. **stash 缺失**：**必须** `scope.errors`（或引擎级 `errors`）记 **`nested_fold_stash_missing`**；**保留**折叠占位与摘要；指标见 §十一；**禁止**静默丢弃父层正文。

**边界**：

- **仅一层栈**（无子 skill）：不触发折叠逻辑。  
- **`replace_auto_meta_on_explicit`**（§4.6.7）与折叠顺序：先处理 auto meta 替换，再判定是否进入「下潜折叠」。  
- **恢复失败**（stash 丢失）：同 **4.6.8.1 第 6 条**。

**配置（见 §5.1）**：`nested_skill_fold` 默认 **`False`**；`nested_fold_summarizer`、`nested_fold_max_chars`、`nested_fold_instructions` 等。

#### 4.6.9 NovAIC / `react_actions` 集成约束（订稿）

- **引擎工具串行化**：一轮 **`react_actions`** 内可出现 **并行** `tool_calls`；**凡命中 `skill_*` / `memory_*` 的调用**须在宿主侧 **固定全序**执行（建议：**先**闭合 recall，**再** skill，**再**业务工具——与 §4.6.5 一致），且 **`skill_end` 仅对应当前栈顶**。禁止多线程同时对 **同一**权威 `messages` 应用引擎突变。  
- **单一真相源**：引擎改写 **权威 `messages`** 后，**必须**在同一工步内 **镜像**到 NovAIC **RO `context`**（或等价存储）；**禁止**只改内存列表而不同步 RO，导致下一轮 `prepare` 读到陈旧列表。  
- **`prepare_messages_for_llm` 与 `expand_messages_for_llm` 顺序（建议）**：对 **同一条**将发给模型的列表：**先** `engine.prepare_messages_for_llm(messages)`（含 `ensure_auto_meta`、阈值压缩），**再** `expand_messages_for_llm`（Recall 热记忆展开等）；若产品必须先 expand 再压，须在集成文档 **显式**写明并与引擎 **协同测试** checkpoint（默认 **prepare → expand**）。  
- **幂等与 RO**：`push_turn` / 工具提交的幂等键与 RO **`CONTEXT_APPEND`**（或等价）对齐方式见 §8.3；**重放**时须保证引擎与 RO **同一提交点**一致。  
- **观测**：并行工具批处理 span 应能关联到 **顺序化后的** `skill_begin` / `skill_end` 子 span（§十一）。

---

## 五、内置实现规格（四件套）

### 5.1 `CompactConfig`（默认）

- 沿用 v1 字段：`context_window`、`compact_threshold`、`emergency_threshold`、`scope_store_raw`、`raw_max_chars_per_scope`、micro/auto 相关阈值等。
- **前缀校验**（§4.2.3）：`full_prefix_validation: bool = False`（默认用哈希快速路径；设为 `True` 走逐条深度比较，用于调试/排查序列化差异）。
- **Skill 栈兜底**（§4.6.7）：`auto_meta_when_stack_empty: bool = True`；`auto_meta_explicit_mode: Literal["stack_under", "replace_when_only_auto"] = "stack_under"`（命名实现可调整，语义见 §4.6.7 表）。
- **Skill End Report 校验**（§4.6.2）：`skill_end_report_validator: SkillEndReportValidator | None = None`（默认不启用）；`max_skill_end_retries: int = 1`（启用 Validator 时，超出重试次数走 Fallback）。
- **嵌套折叠**（§4.6.8）：`nested_skill_fold: bool = False`（首版生产默认关；验证恢复与 RO 后再开）；`nested_fold_summarizer: Literal["stub", "llm"] = "stub"`；可选 `nested_fold_max_chars`、`nested_fold_instructions`（`llm` 时）；`nested_fold_stash_threshold: int = 30_000`（超过此阈值的 `raw_segment` 走外存降级，防止内存峰值；§4.6.8 步骤 5）。
- 默认值以 **保守、可预测** 为原则；变更需在 CHANGELOG 标明行为影响；**参与 `engine_config_hash` 的字段列表**在实现源码与本文同步维护。

### 5.2 `TokenCounter`（默认）

- **首选**：依赖可选的 `tiktoken`（或项目统一 tokenizer），编码与模型族在配置中指定；若未安装则 **显式降级**。
- **降级**：字符数或字节数启发式，并在 `StackStatus` 或日志中标记 `estimate=true`，避免 silent 误判。
- **性能**：避免在每次 `pull` 对全历史做 tiktoken；推荐在 `push_turn` 提交后 **增量累计** 或仅超阈值时重算（§十九）。

### 5.3 `Summarizer`（默认）

| 层级 | 行为 | 用途 |
|------|------|------|
| **Stub** | 截断最后若干 assistant 消息 + 固定模板 | 单测、离线 CI、无密钥环境 |
| **HTTP/LLM** | 由集成层注入；可读取 env / Factory | 生产 |

**默认安装**：库默认构造 **Stub**。**CI 默认**须使用 Stub 或 mock，避免无意触发外网（§十五 默认决议）。

> **Skill 路径**：经 **`skill_end`** 关闭的 scope **默认不调用**本 Summarizer LLM（§4.6.2）；Stub/HTTP 实现仍用于 **非 skill 的 `push_turn(done=True)`**、**abort(summarize=True)**、**Fallback** 等场景。

> **嵌套折叠**：`nested_fold_summarizer=llm` 时 **复用同一 `Summarizer` 实现** 与 **不同 instruction**（§4.6.8）；**合规与留存**须按 **两次用途**（⑤ finalize vs `nested_fold`）分别说明，日志/span **不得**混标为单一 `summarize`。

> 若产品要求「零参数即生产级摘要」，必须在文档中写明 **默认会访问的网络目标与凭证来源**，并承担 semver 与合规责任。

### 5.4 `Store`（默认）

- **默认**：进程内 `MemoryScopeStore`（LRU + 线程锁），与 v1 行为一致。
- **可选内置**：`SqliteScopeStore(path)`（WAL、批量写）；表结构含 `schema_version`；多租户须配合 §2.3。

---

## 六、高级覆盖（可选）

不破坏「四件套内置」叙事的前提下，构造参数仍允许：

- `summarizer=MySummarizer()`
- `counter=MyCounter()`
- `store=PostgresBackend()`
- `config=CompactConfig(...)`

用于单元测试、多租户、与 LLM Factory 的深度集成。**覆盖时 `engine_config_hash` 须反映自定义类或序列化策略**（或由宿主在 meta 中禁用跨版本恢复）。

---

## 七、错误处理与中止（决策矩阵）

| error | done | 行为 |
|-------|------|------|
| `None` | `False` | 正常推进 EXECUTE；④⑤⑥ 不执行。 |
| `None` | `True` | 先 Recall 补全（若启用）→ ④ POST → ⑤ SUMMARIZE → ⑥ RELOAD → `CLOSED`。 |
| 非空 | `False` | 将 `error` 记入 `scope.errors`；**仍停留在 EXECUTING**；是否要求下一 `push` 清错由实现约定（建议允许继续 turn）。 |
| 非空 | `True` | 记入 `scope.errors`；**仍执行** ④⑤⑥（摘要可含失败说明），然后 `CLOSED`。 |

**`abort(reason, summarize=False)`**：不经过 `push_turn`；`summarize=True` 时走简短 ⑤⑥；`False` 时跳过或极简落盘；最终 `CLOSED`。

**非法顺序**（含内部 `push_turn`）：在**无栈顶 scope** 时 `push_turn`、`done` 后再次 `push`、`CLOSED` 后 `pull`/`push` → **`RuntimeError`**。

---

## 八、可恢复性与 Worker 集成

### 8.1 持久化载荷（逻辑模型）

```json
{
  "version": 1,
  "engine_config_hash": "sha256:...",
  "scope_id": "...",
  "phase": "EXECUTING",
  "skill_name": "...",
  "message_start_idx": 42,
  "messages": [ ... ],
  "turn_count": 3,
  "last_idempotency_key": "...",
  "meta": { "task_id": "...", "correlation_id": "..." }
}
```

- **version**：blob 格式版本；与 **包 semver** 对应关系写在 CHANGELOG（例：blob v1 ↔ context-stack `2.x`）。
- **engine_config_hash**：对规范化配置的稳定序列（如按 key 排序的 JSON）做 **SHA-256**；恢复时 **不匹配则拒绝恢复** 并记指标（§十一）。
- **敏感**：消息体可能很大；**推荐拆分**（§8.4）。
- **§4.6.8 折叠态（可选，M3+）**：若启用 **`nested_skill_fold`** 且需 **跨 Worker 恢复**，blob（或并列表）须含 **`fold_frames`**（每父帧：`parent_scope_id`、`stash_ref` 或内联 `raw_segment` 哈希、`placeholder_message_id(s)`、`folded_until_child`）；**缺失则恢复后拒绝继续 EXECUTE 或降级为 §4.6.8.1 第 6 条**。**在 schema 未纳入前**，跨进程 **不保证** 折叠一致，见 §4.0 集成分层。

### 8.2 NovAIC 建议挂载点

- **Task Worker**：`pull_turn_context` → LLM/tool → `push_turn`；`done=True` 后将 **`LifecycleResult` 写入 RO context** 并 ack 队列；**finalize 失败**须可重试且幂等（见 8.3）。**引擎突变**（`skill_*` / `memory_*` / `prepare`）与 **RO `CONTEXT_APPEND`** 的 **提交顺序**须与 §4.6.9、§8.3 一致，避免「引擎已弹出栈、RO 仍含未闭合 tool」类漂移。  
- **Chat / 同步 Runtime**：以 **§4.6.9** 为主；`pull`/`push` 可选。  
- **超时**：宿主侧 `abort` 或 `done=True`+`error`；引擎不杀 LLM。

### 8.3 幂等与至少一次投递

- **问题**：队列可能 **至少一次** 投递同一工步；宿主可能在 `push_turn` 成功后崩溃未 ack。  
- **建议**：`TurnPayload.idempotency_key`（或 `(scope_id, turn_id, attempt)`）在引擎内 **去重**：相同 key 的第二次 `push_turn` **不重复推进** `turn_id`/消息，返回与首次相同结果或 `IdempotentReplay` 结果类型。  
- **恢复**：Worker 重启后从 blob 恢复 Session，**先读 `last_idempotency_key` 与 `turn_count`**，再决定重放 `push` 还是新 `pull`。  
- **部分失败**：LLM 已完成但 `push` 未执行 → 宿主应把 **模型输出暂存工步状态**，重试时同一 `idempotency_key` 提交，避免双写。  
- **与 RO 追加键对齐**：`idempotency_key`（或 `(scope_id, turn_id, attempt)`）建议 **写入** RO 消息 meta 或工步状态，使 **重放** 时引擎去重与 RO **去重/跳过** 使用 **同一键空间**；NovAIC 具体字段名以 runtime 契约为准，本文只要求 **可观测、可重放**。

### 8.4 载荷拆分与序列化

- **推荐**：blob 存 **元数据 + 消息哈希 + 可选压缩引用**；大 `messages` 放对象存储 / RO 大字段 / SQLite BLOB 表；引擎提供 **assemble(blob, fetch_body_fn)** 恢复。  
- **序列化**：大负载优先 **msgpack / protobuf + zstd**；若必须用 JSON，建议 **压缩后 Base64** 并设 **单 blob 大小上限**，超限拒绝或强制拆分。  
- **混沌测试**：损坏 blob、错误 version、篡改 messages、hash 不匹配 → **明确异常类型**，无未定义行为（§十二）。

---

## 九、与六步生命周期的对应关系

| 步骤 | v2 触发点 |
|------|-----------|
| ① CHECKPOINT | **内部** `_begin_scope` 内，**先于** PRE |
| ② PRE-HOOKS | **内部** `_begin_scope` 内，紧随 CHECKPOINT |
| ③ EXECUTE | `pull_turn_context` / `push_turn` 循环直到 `done=True` |
| Recall 补全 | **每次 `push_turn` 内**（`done` 前后均需闭合 memory_* **再**进入 POST） |
| ④ POST-HOOKS | `done=True` 的 `push_turn` 内，Recall 之后 |
| ⑤ SUMMARIZE | POST 之后；**若由 `skill_end` 关闭栈顶 scope**：**不调用 Summarizer LLM**，摘要正文 = **`skill_end` 工具提交**（§4.6.2）；**否则**（`push_turn(done=True)` 等）走内置 Summarizer |
| ⑥ RELOAD | 摘要正文就绪之后；更新 `messages`、写 store |

**Compaction（非 scope）**：仍仅在 **Engine** 上；**EXECUTING 内不隐式** scope 级 RELOAD（§4.4）。

### 9.1 ⑤ SUMMARIZE 执行逻辑梳理（订稿：`skill_end` report = skill 执行结果报告）

> **已定**：**Skill scope 的执行结果报告**由模型通过 **`skill_end` 工具**提交；Context Stack **不再**对该路径调用 **Summarizer LLM** 生成主摘要正文。下面按 **「谁触发 finalize」** 梳理 **⑤** 与 **⑥**。

#### 判定顺序（实现时可化为函数 `resolve_summary_source(scope, trigger)`）

1. **Finalize 触发源是否为 `skill_end`（栈顶出栈）？**  
   - **是** → 进入 **路径 A（Skill 摘要）**。  
   - **否** → 进入 **路径 B（引擎摘要）**；若再走 **abort 子路径**见下。

2. **路径 A — `skill_end` 关闭栈顶 scope**  

   | 子步骤 | 行为 |
   |--------|------|
   | ④ POST-HOOKS | 照常（校验、指标、post-hooks）。 |
   | **⑤ 主摘要正文** | **取自 `skill_end` 工具入参**（如 `user_visible_summary` / `report.summary`），校验、**最大长度裁剪**、禁止空（或走 Fallback）。**不调用 `Summarizer.summarize`（LLM）**。 |
   | ⑤ 附加（可选） | **仅规则**：从 scope 内 `messages` 抽取 `decisions` / `files_changed` / `tools_used` 等写入 `ScopeRecord`，**不**生成第二段 LLM 摘要覆盖正文。 |
   | ⑥ RELOAD | 用 **⑤ 主摘要正文** 组装 **单条折叠消息**，替换 scope 内 raw、写 store、更新 token 统计。 |
   | TOOL 返回 | 引擎组 **`skill_end` 的 JSON report**（可与入参 echo + 补 `scope_id`、`tokens_saved` 等），供 transcript 与 UI。 |

3. **路径 B — `push_turn(done=True)` / 程序化 finalize，且 **不是** `skill_end`**  
   适用于：**内部测试**、**Recall-only / Meta 等非 Skill 工具路径**（若保留内部 Session API）、或 **未使用 `skill_end` 的程序化 finalize**。**生产 Skill 路径以 `skill_end` 为准**。  

   | 子步骤 | 行为 |
   |--------|------|
   | ④ POST-HOOKS | 照常。 |
   | **⑤ 主摘要正文** | 调用内置 **`StructuredSummarizer` → `Summarizer`（Stub 或 HTTP/LLM）** 基于 scope 内消息生成（与 v1 同类逻辑）。 |
   | ⑥ RELOAD | 同上，用 LLM/Stub 产出作为折叠正文。 |

4. **路径 C — `abort(summarize=True)`**  
   - **⑤**：走 **简短**摘要——**默认 Stub** 或配置为 **一次 Summarizer LLM**（产品定）；**不因 skill 栈而自动改走 `skill_end` 报告**（abort 时通常无工具入参）。  
   - **⑥**：按配置是否写 store / 写多简。

5. **路径 D — `abort(summarize=False)`**  
   - **⑤⑥**：跳过或仅 tombstone；**不**要求 `skill_end` report。

#### `skill_end` 摘要缺失时的 Fallback（路径 A）

| 条件 | 建议行为 |
|------|----------|
| 未传或空 `user_visible_summary` / `summary` | **Stub 单行**（含 `scope_id`、错误码）或配置 **`skill_end_empty_fallback=engine_summarize`** **仅此分支**调用 Summarizer LLM。 |

#### 与「非 scope」压缩的边界

- **`prepare_messages_for_llm` 内部温和/激进路径**（原 maybe/emergency 语义）：处理 **将发给 LLM 的整条 `messages` 预算**，**不是** ⑥ 的「单 scope 折叠摘要」；与 ⑤ **无调用关系**。  
- **Runtime 侧 `simple_summary` / hot-cold**（NovAIC）：属于 **跨 runtime 记忆管线**，**不替代**本节的 **scope 级 ⑤**；并存时职责不混写。

#### 一文对照

| 触发 | ⑤ 正文来源 | Summarizer LLM（狭义） | 改权威 `messages`（⑥ 或等价） |
|------|------------|------------------------|-------------------------------|
| **`skill_end`（栈顶）** | **工具 report / `user_visible_summary`** | **不调**（除非 Fallback） | **是**（⑥ RELOAD） |
| **`push_turn(done=True)` 非 skill_end** | **StructuredSummarizer** | **调**（或 Stub） | **是** |
| **`abort(summarize=True)`** | Stub 或简短 LLM | **可选** | **按配置** |
| **`abort(summarize=False)`** | 无 | 无 | tombstone / 跳过 |
| **`prepare_messages_for_llm`（_maybe / _emergency）** | **不适用**（非 ⑤） | **不得**充当 ⑤；若用 LLM 压预算须独立配置 | **是**（须守 checkpoint / `skill_fold`） |
| **§4.6.8 折叠 / 展开** | **不适用**（非 finalize） | **`stub` 默认**；`llm` 时同协议 + `nested_fold` 标签 | **是**（占位 ↔ stash） |

**总表**：与 §2.4 对照阅读；实现评审以 **两表一致** 为验收。

---

## 十、并发与线程模型

- **ScopeSession**：同一实例上 **`pull_turn_context` 与 `push_turn` 不得并发**；也不得多个 `push_turn` 并发。  
- **ContextEngine**：不同 Session 可并行；`Store` 与全局统计用 `threading.Lock`。  
- **异步宿主**：状态机核心保持 **同步**；可在宿主侧用队列串行化对同一 Session 的调用。

---

## 十一、观测性

**日志（结构化字段）**：至少 `scope_id`、`phase`、`turn_count`、`skill_name`、`task_id`/`correlation_id`、`engine_config_hash`（恢复时）、`trace_id`/`span_id`（若接入 OTel）。

**Tracing**：

- Span：`context_stack.scope.begin`、`turn.pull`、`turn.push`、`summarize`（⑤ 狭义）、`reload`；可选 **`nested_fold_summarize`**、`auto_meta_open`、`skill_stack_snapshot_write`。  
- **传播**：`TurnContext.trace_context` 由宿主在 LLM 调用链中延续；或在 `hooks` 中注入。并行 `react_actions` **顺序化**后的子 span 须可链接到上述 span（§4.6.9）。

**指标（扩展）**：

- 计数：`scopes_opened`、`scopes_closed`、`aborts`、`push_validation_errors`、`recall_autofill_count`、`restore_success`/`restore_reject_hash`/`restore_reject_version`。  
- **Skill 栈 / 折叠**：`skill_stack_depth_current`、`skill_begin_rejected_max_depth`、`auto_meta_injected_total`、`nested_fold_started`/`nested_fold_expanded`、`nested_fold_stash_missing`（§4.6.8.1）。  
- 直方图：`pull_to_push_latency_ms`、`summarize_duration_ms`（⑤，狭义）、`nested_fold_summarize_duration_ms`（与 ⑤ 分列）、`checkpoint_blob_bytes`。  
- **finalize 失败**与 **幂等重放** 次数单独计数。

**默认**：不在 INFO 打印完整消息正文；DEBUG 需脱敏开关。

---

## 十二、测试策略

| 类型 | 内容 |
|------|------|
| **单元** | Phase 转移、非法顺序、`skill_prompt` 伪造拒绝、Recall 插入、`mode=full` vs `replace_from_checkpoint`、`allowed_tools` 交集、**skill 栈 push/pop、越权 skill_begin、skill_end report 字段** |
| **前缀校验** | `mode=full` + 哈希快速路径：正常 hash 命中通过、前缀被篡改时 `ValidationError`；`full_prefix_validation=True` 降级走逐条比较 |
| **Phase A/B 隔离** | Phase A（`_ensure_stack_ready`）失败时 Phase B 不执行且报错清晰；Phase B 压缩不影响 Phase A 的栈状态判断；两个 Phase 各自独立 mock 可测 |
| **Report Validator** | `SkillEndReportValidator` 启用时：report 合格 → 正常 finalize；report 不合格 → TOOL 返回 error + rejection_reason，模型可重试；超出 `max_skill_end_retries` → 走 Fallback；Validator 为 None 时不影响正常流程 |
| **会话级** | 多轮 `push` 后 `done`；最终仅 pre-scope + 一条 summary；**多轮 tool：assistant → tool → assistant**；**末轮未闭合 memory_* → push 后插入 TOOL**；**skill_begin → … → skill_end 收到含 summary 的 TOOL JSON** |
| **恢复** | `to_checkpoint_blob` → 恢复 → 继续 pull/push 与一次性跑通一致 |
| **幂等** | 相同 `idempotency_key` 双 `push` 不双推进 |
| **混沌** | 截断/篡改 blob、错误 version、hash 不匹配、超大 payload |
| **属性/不变式** | 合法转移-only、`done`/`abort` 终态、Recall 闭包、`message_start_idx` 与 PRE 次序 |
| **§4.6.8** | **金样**：下潜折叠 → 子层对话 → `skill_end` → 父展开后 **messages 与无折叠参考运行一致**（实现约定等价比较）；**混沌**：stash 损坏 / 占位被删 / 多级 LIFO 错序 → 须触发 §4.6.8.1 第 6 条或明确 `ValidationError` |
| **§4.6.8 stash 分级** | `raw_segment` 小于 `stash_threshold` → 内存 stash；大于等于 → 外存降级 + hash 校验；外存 stash 在展开/abort 后立即清理；`engine.close()` 清理所有残留 stash |
| **安全元数据** | 宿主伪造 `skill_stack_snapshot` / `skill_fold` / `auto_meta` → **剥离或拒绝**（§2.3） |
| **金样（checkpoint）** | 版本化 checkpoint fixture 纳入仓库，防序列化漂移；**M3+** 含可选 `fold_frames` 与恢复后展开一致 |
| **engine 生命周期** | `engine.close()` 后调用任何方法 → `RuntimeError`；`with` 上下文管理器正常退出和异常退出均调用 `close()`；`close()` 多次调用幂等无异常 |

**CI**：默认 Summarizer 为 Stub；网络测试单独 job。

---

## 十三、模块与文件布局（建议）

```
context_stack/
  engine.py              # ContextEngine v2
  session.py             # ScopeSession, TurnContext, TurnPayload, Phase enum, SkillStack
  skill_router.py        # SkillToolRouter（skill_begin/end + 可选与 Recall 合并为 ContextToolRouter）
  defaults/
    config.py
    counter.py
    summarizer.py
    store.py
  lifecycle.py
  ...
```

`protocols.py`：**删除 `AgentExecutor`**；保留 `Summarizer` / `TokenCounter` / `MemoryBackend` 为可选覆盖。

---

## 十四、实施里程碑（建议）

| 阶段 | 预估工时 | 交付 |
|------|----------|------|
| **M1** | **1.5 ~ 2 周** | **对外** `ContextEngine`（含 `close()` / 上下文管理器）+ `prepare_messages_for_llm`（Phase A/B 拆分，**无**对外 `maybe_compact` API）+ `skill_begin`/`skill_end` + 可选 `pull`/`push`；**内部** `_ScopeSession` / `_begin_scope` + **`mode=full` 定稿 + 前缀哈希校验** + Stub summarizer + 内置 counter/config/store |
| **M2** | **1 ~ 1.5 周** | Recall 补全 + **`skill_begin`/`skill_end` + SkillToolRouter + stack 镜像（`role=system`）+ end report + `SkillEndReportValidator` 可选 hook** + **§4.6.8 实现（默认 `nested_skill_fold=False`，含 stash 分级策略）** + 工具格式规范 + 单测覆盖 ≥ v1 等价场景；**开启折叠**的交叉测试延至 **M3** 与 checkpoint 字段（§8.1）对齐 |
| **M3** | **1 周** | `checkpoint_blob` + **恢复** + **幂等键** + Worker 文档示例 + 金样 fixture |
| **M4** | **0.5 ~ 1 周** | `SqliteScopeStore` + NovAIC runtime 接入 |

**预估说明**：基于 v1 代码量（~1500 行 + 199 单测）与六步语义不变的前提。M1 工时最长是因为核心骨架重写（去 executor、被动式翻转）；M2 可复用 v1 `RecallToolRouter` 逻辑；M3 实现量不大但需严格设计验证（混沌测试、金样 fixture）；M4 依赖 NovAIC runtime 侧配合，实际周期可能受集成协调影响。

---

## 十五、开放问题与默认决议

以下条目若评审沉默，**采用默认列**；**拍板阶段**指必须在此里程碑前写入实现与文档终稿。

| # | 问题 | 默认决议 | 拍板阶段 |
|---|------|----------|----------|
| 1 | `done` 由宿主声明 vs 引擎「无待处理 tool」自动 done | **M1 仅宿主声明**；自动 done 延至 v2.2+。若未来引入自动 done，**必须先于 finalize 跑一轮 Recall 扫描**，避免 memory_* 未闭合。 | M2 前复审 |
| 2 | M1 是否必须增量 `push` | **否**；M1 仅 `mode=full` 全量；v2.1 再做增量 API。 | 已决 |
| 3 | CI 是否强制 Stub Summarizer | **是**；默认 job 无密钥、无外链。 | M1 |
| 4 | Chat 会话 vs Scope：顺序与并行 | **推荐**同一对话线 **多个顺序 Session**；**默认禁止**同一 Engine 上并行两个未关闭 Session 共享同一 **可变消息列表**；并行多 Session 仅当消息列表隔离。 | M1 产品确认 |
| 5 | Skill 栈最大深度 / 是否允许嵌套 | **默认允许嵌套**，`max_skill_depth=4`；单层模式设 `max_skill_depth=1`。 | M2 |
| 6 | 栈空是否自动 Meta | **默认开启** `auto_meta_when_stack_empty=True`；显式 skill 与 auto Meta 叠放用 `stack_under` 或 `replace_when_only_auto`（§4.6.7）。 | M1 |
| 7 | §4.6.8 跨 Worker 与观测 | **默认关** `nested_skill_fold`；**blob `fold_frames`** 与 **指标 `nested_fold_*` / span `nested_fold_summarize`** 在 **M3** 与 §8.1 字段一并拍板；恢复失败行为以 §4.6.8.1 为准。 | M3 |
| 8 | `prepare` vs RO 顺序 | **默认** `prepare_messages_for_llm` → `expand_messages_for_llm`（§4.6.9）；若反转须在集成文档与 CI 中 **显式**覆盖。 | M2 前复审 |

---

## 十六、v1 API 映射与删除清单

| v1 | v2（对外） |
|----|-----|
| `ContextEngine(executor, summarizer, counter, store, config)` | `ContextEngine(summarizer=..., counter=..., store=..., config=...)`，**无 executor** |
| `AgentExecutor.execute(messages, extra_tools)` | 宿主：LLM + 工具；**`skill_*` / `memory_*` 走引擎 dispatch**；可选 `engine.pull_turn_context` / `push_turn`（栈顶） |
| `engine.run(skill, messages)` | 模型 **`skill_begin`(skill_name)** → … → **`skill_end`(report)**；**不**对外 `begin_scope` |
| `engine.run_meta(messages, task=...)` | 模型 **`skill_begin`**（Meta 或默认 skill）+ **`skill_end`**；或 **内部**保留 Meta Session（仅测试/特殊宿主） |
| `engine.run_recall(messages, query=...)` | 模型 **`skill_begin`**（Recall 类 skill）或 **内部** Recall 会话 + `memory_*` 工具 |
| `RecallToolRouter` 包装 executor | **内置**于工具 dispatch / `push_turn` 路径 |
| `engine.handle_recall_tool` | 内部模块；宿主经 **统一 tool 入口** |

**内部对照**（不承诺稳定）：旧 `begin_scope` → **`_begin_scope`**；旧 `ScopeSession` → **`_ScopeSession`**（或包内私有类名）。

---

## 十七、SkillRegistry 与数据来源

- **库内默认**：空注册表 + `MetaSkill` / `RecallSkill` 内置；`match()` 仅在 **已 register 的 NORMAL skill** 上匹配。  
- **NovAIC**：由 **runtime 或 gateway 同步层**在进程启动时 `registry.register_many(...)`，数据来源可为 DB skills + builtin；**单一真相源**应在产品层约定（例：Gateway Entity `skills` + 版本戳），避免与前端展示漂移。  
- **本文档不规定**具体同步协议，仅要求：**注册完成后再**允许模型通过 **`skill_begin`** 绑定到正确 skill 定义。

---

## 十八、性能与实现建议（实现者必读）

- **M1 O(n) push**：接受全量列表的拷贝/校验成本；v2.1 增量 API 优先。  
- **Recall 扫描**：维护「尾部未闭合 tool 指针」，避免每 push 全表扫描。  
- **`TurnContext.messages`**：默认只读视图；`snapshot_copy=True` 为调试/测试可选参数。  
- **checkpoint**：大会话必须 **拆分存储**（§8.4），避免队列/DB 爆量。  

---

## 十九、与现有文档的关系

- **`docs/unified_engine_architecture.md`**：六步语义与 Skill 类型仍以该文为概念权威；**时间线与 API** 以本文为准。  
- **`HANDOVER.md` §十八**：落地后改为指向 v2 Session API 与内置默认。

---

*文档结束。*
