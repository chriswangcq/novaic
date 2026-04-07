# Context Stack Engine

**Context Stack** 是 NovAIC 架构下一代的核心上下文、记忆与大模型任务运行时基石模块。它是一个**零外部业务依赖**、通过严格协议层解耦的独立引擎库，负责统管所有 AI 会话。

## 🌟 核心理念与痛点解决

在传统的 Agent 执行循环中，经常面临以下问题：
1. **上下文冗余与坍塌**：连续多次工具调用或对话会导致 `messages` 数组无限制增长。常见的做法是生硬截断，导致模型瞬间遗忘前期重要决策。
2. **记忆系统不可逆**：当 LLM 回忆长期记忆（RAG 或历史数据）时，需要引入新工具提取信息。旧方案容易导致这些为了回溯而发送的检索 prompt 污染接下来的会话流。
3. **元数据丢失**：如果截断消息，大模型在执行过程中做出的 "chose X over Y" 或者 "遇到报错 A 然后尝试 B" 的关键微观思维路径也将丢失。

**Context Stack 提出了“事务化生命周期（Transactional Scope）”的思想来解决以上痛点。** 
每一次 Agent 处理任务，不再是对着一串裸 `messages` 操作，而是把整个任务拉起一个**独立沙箱（Context Scope）**。

---

## 🛠 严格的 6 步生命周期与引擎门面（Facade）

核心类 `ContextEngine` 是对接引擎的唯一门面（Facade）。宿主进程每次让大模型干活，无论是回答一个问题，还是要调用一个宏大的流程编排任务，都会经历引擎内严格写死的 **6 个执行层级**：

1. **① CHECKPOINT（建立快照）**：保存系统在任务前的数据（Token、消息体游标）。
2. **② PRE-HOOKS（挂载准备）**：往 Agent 流投喂定制 Prompt（即当前 Skill）、开启必要的重入锁并注入受限工具。
3. **③ EXECUTE（移交沙盒代理）**：Context Stack 引擎**完全不干涉大语言模型如何轮询和调用工具**。引擎通过宿主提供的 `AgentExecutor` 协议接口把沙箱上下文丢给宿主循环执行。
4. **④ POST-HOOKS（收尾与拦截）**：宿主执行完工具流后返回这批 messages，触发后置检查（工具调用耗时、是否宕机出轨等）。
5. **⑤ SUMMARIZE（规约与抽取）**：提取这段长长的原始交互，利用 `StructuredSummarizer` 自主抽取出 `Scope` 元数据：比如调用了什么工具？做了什么妥协与决策？碰到了什么错误？
6. **⑥ RELOAD（坍缩折叠）**：引擎无情地砍去这个阶段激增的原始 messages（将其封存入后端的长期记忆中备查），并在上下文中塞入一段极其紧凑的摘要化 `Message`，释放大批可用 Token。

通过这六步，系统在宏观视角下看到的仅仅是非常简短的“系统阶段性任务摘要”，从而实现理论上无限回合的常驻记忆。

---

## 🧭 三大并行架构机制 (Skill Types)

所有的任务都被归为引擎定义的三大 Skill：

### 1. Normal Skill (领域规范动作)
常规的业务处理，通常绑定了一个特定的 Workflow、系统级 Prompt 以及允许的一套工具箱。大模型的行为受高度管控。

### 2. Meta Skill (兜底安全网)
这是极其重要的兜底层引擎。当用户闲聊或没有命中任何技能规则时，请求将被迫进入 Meta Skill 沙箱。这确保了：**系统中不存在没有任何生命周期管理的孤岛消息。** 没有被追踪的记录就是对上下文的潜在危害。

### 3. Recall Skill (自主深潜回忆机制)
引擎自带的自我疗愈与上下文回溯机制。当大模型的即时上下文无法回答某个长尾历史时：
- 宿主触发 `run_recall(messages)`。
- Recall Skill 自动强绑定 `memory_search` 和 `memory_expand` 两个探索工具，允许模型逐级（L0概要 -> L1快照 -> L2片段 -> L3原始对话）对历史的 Scope 对象进行动态下钻调阅。
- **透明路由闭环**：引擎内封装了 `RecallToolRouter`，自动阻截和投喂记忆查询结果，不需要宿主写任何关于如何响应历史记忆的分法代码。

---

## 🔌 宿主机接入指南 (Protocol 依赖隔离)

Context Stack 被设计成完全不可见依赖项内部状态的“鸭子类型接口（Duck Typing Protocols）”。业务接入方需要实现 `context_stack/protocols.py` 给出的四个接口：

### 1. AgentExecutor
定义 `execute(messages, extra_tools)`，即外部真实的 LLM 轮询引擎应该长什么样，把生成的数据塞回来就行。
*(对于 NovAIC，这就是套一层 `AgentLoop` 或者后续的 OpenClaw Agent runner )*

### 2. TokenCounter
实现 `count(text)`，为引擎的断崖式 Compaction 兜底内存预算检查提供计数器。

### 3. Summarizer
提供 `summarize(scope, messages, instructions, max_tokens)`。由于业务通常自带各种 LLM 服务池，框架拒绝自己造轮子引入 OpenAI/Anthropic SDK，让上层业务把自己的大模型请求封进来用于抽取摘要决策。

### 4. MemoryBackend
实现 `save_scope`, `search_scopes`, `get_scope`。引擎不在本地硬编码写入 SQLite；提供这个接口，你想写入 Postgres, 游标甚至云端 VectorDB 都行。

### 🚀 示例初始化与调用

```python
from context_stack.engine import ContextEngine, ContextEngineConfig
from context_stack.context.types import CompactConfig

# 1. 注入你实现好的宿主基础设置
executor = MyHostAgentExecutor()
counter = MyTokenCounter()
summarizer = MyLLMSummarizer()
memory_db = MySqliteMemoryBackend()

# 2. 组装配置，启动心脏
config = ContextEngineConfig(
    compact=CompactConfig(
        context_window=100000, 
        compact_threshold=0.8,
        raw_max_chars_per_scope=50000  # 内存安全硬截断兜底
    )
)

engine = ContextEngine(
    backend=memory_db,
    executor=executor,
    summarizer=summarizer,
    counter=counter,
    config=config
)

# ======== 业务调用姿势 ========
# 遇到普通会话：
result = engine.run_meta(current_messages)
new_history = result.compact.messages  # 拿到的是经过合并、精简、决策分析过的浓缩数组

# 需要执行特定功能：
skill = matcher.match("帮我重启网关")
result = engine.run(skill, current_messages)

# 大模型说：“我不记得之前怎么写的接口了”：
recall_result = engine.run_recall(current_messages) 
```

---

## 🛡️ 已包含的七层工业级健壮性防护 (2026-04 落地标准)

在研发过程中，我们处理了许多实际生产系统才遇到的大语言模型不可预测的故障态。当前堆栈已经做到了全面防御：

1. **防重入锁 / 套娃级宕机规避 (`_active` Guard)**：当 LLM 在 `EXECUTE` 循环中自行尝试触发全新的 Recall 或 Meta 层级时，引擎的防重入机制会立即返回原子拒绝，避免死锁；外加 `finally` 关键字确保沙箱被摧毁必然归还互斥状态。
2. **多线程安全 (`threading.Lock`)**：在并行的 Web 服务架构下（比如 Gateway 处理多个前端并行的 Task），引擎的统计算法与 `MemoryScopeStore` 会加锁保证不打架或出现重复累加的脏数据。
3. **原始记忆限额逃生（Budget Enforcement）**：遇到极端工具乱吐（如 shell `cat` 大本子）的情况，不再被长串字符阻塞数据库；引擎使用 `raw_max_chars_per_scope` 进行头尾抽取截断保存，既不丢失头部的请求理由也不丢失末尾的出错原因。
4. **决策提取挂环 (`Structural Metadata Extraction`)**：基于微观 `regex` 与 LLM 协同从执行文本中提取带有强语义意图的子串 `"decided to"`, `"chose X over Y"`，挂载在 `scope.decisions`，这是跨世代会话复盘的核心依赖。
5. **Prompt 不越界污染**：执行 Skill 时的特殊限定 prompt 打上了 `metadata={"skill_prompt": True}`。它在最后 `RELOAD` 时不仅被从当前上下文中摘除，而且在存入持久化记忆库时也会被清空。避免将来的 Recall 提取结果再次带回这种环境指令而二次中毒。
6. **黑盒化记忆拦截 (`RecallToolRouter`)**：为了不增加宿主机对特定工具鉴别的恶心耦合，引擎强行套壳 `MemoryAgentExecutor`，内部解决掉了 `memory_expand` 等响应，完全阻断了该过程逃逸到上游主系统导致的死循环。
7. **三层无死角熔断 (Micro/Auto/Emergency Compaction) **：无情兜底。Micro 做局部字段截断（旧工具留骨骸）；Auto 基于 Token 比例强制发起微型总结；Emergency 在 Auto 崩溃（如底层模型API宕机）按行粗暴裁剪，这三个保证了 Context 永远活在限额红线之下。
