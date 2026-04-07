# Context Stack: 统一引擎架构

> 核心主张：Skill 执行生命周期 = 上下文管理生命周期 = Memory 管理生命周期
> 它们不是三个独立模块，是同一个东西的三个视角

---

## 一、Skill 执行生命周期（唯一的核心循环）

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ① CHECKPOINT                                          │
│   │  保存当前上下文快照 (message_start_idx, tokens)       │
│   │  标记 scope 边界                                     │
│   ▼                                                      │
│   ② PRE-HOOKS                                           │
│   │  注入 skill prompt / workflow                       │
│   │  设置工具白名单 / 约束                               │
│   │  Recall Skill: 搜索历史 scope → 注入相关上下文       │
│   │  Meta Skill:   无操作（Agent 自由模式）              │
│   ▼                                                      │
│   ③ EXECUTE                                             │
│   │  Agent 实际工作（调用 LLM、使用工具）                │
│   │  可能多轮 query loop                                │
│   │  引擎只观察，不干预                                 │
│   ▼                                                      │
│   ④ POST-HOOKS                                          │
│   │  校验执行结果                                       │
│   │  收集元数据（file changes, tool usage, errors）     │
│   │  触发后续动作（通知、日志...）                      │
│   ▼                                                      │
│   ⑤ SUMMARIZE                                           │
│   │  将 ③ 中的所有消息压缩为结构化摘要                  │
│   │  提取：决策、文件变更、错误修复、关键产出           │
│   │  丢弃：冗长 tool 输出、中间探索                     │
│   ▼                                                      │
│   ⑥ RELOAD                                              │
│   │  用 summary 替换 scope 内的原始消息                 │
│   │  保存 raw messages 到 MemoryStore（供 Recall 用）   │
│   │  更新 token 预算                                    │
│   └──────────────────────────────────────────────────────│
│                                                          │
│   这 6 步对所有 Skill 类型完全一致                       │
│   区别只在 pre_hooks 做什么 和 skill 有没有 prompt       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 二、三种 Skill 类型

### 1. 普通 Skill（有具体指令和 workflow）

```
pre_hooks:
  - 从 SkillStore 加载 skill prompt + workflow
  - 注入到系统消息中
  - 可选：设置工具约束（只允许某些工具）

execute:
  - Agent 按照 prompt/workflow 工作
  - 可能调用 N 个工具、多轮对话

summarize:
  - "完成了用户注册功能，使用 bcrypt 哈希，创建了 3 个文件..."
```

### 2. Meta Skill（无匹配 skill 时的默认包装器）

```
触发条件：
  - 没有匹配到任何 skill
  - 用户发了一个新请求，Agent 自己决定怎么做

pre_hooks:
  - 无额外 prompt 注入
  - scope name = 用户请求的前 N 个字 / Agent 自己起名

execute:
  - Agent 自由执行

summarize:
  - 同样压缩为结构化摘要
  
意义：
  即使没有 skill，上下文管理仍然生效
  每个用户请求都被一个 scope 包裹
  → 不再有"无主消息"在上下文中漂浮
```

### 3. Recall Skill（基于历史回忆的工作）

```
触发条件：
  - 用户说"之前那个 xxx 怎么做的？"
  - Agent 判断需要回忆过去

pre_hooks:
  - 搜索 MemoryStore，找到相关 scope records
  - 将 scope summaries（或 focused details）注入上下文
  - Agent 现在能"看到"过去的工作

execute:
  - Agent 基于回忆内容继续工作
  - 可能只是回答问题
  - 可能重新打开文件验证
  - 可能在旧方案基础上修改

summarize:
  - "回忆了'用户注册'和'数据库设计'两个 scope"
  - "确认了 bcrypt 仍在使用，新增了 rate limiting"
  
关键：
  Recall 不止是"查询历史"
  它是一次完整的 Skill 执行 → 回忆只是 pre_hook
  回忆之后做的事 也被 checkpoint/summarize 管理
```

---

## 三、统一引擎结构

```
context-stack/
├── engine.py              ← 🎯 ContextEngine（唯一入口）
│                             .run(skill, messages) → 驱动完整生命周期
│                             .run_meta(name, messages) → Meta Skill
│                             .run_recall(query, messages) → Recall Skill
│
├── lifecycle.py           ← 6 步生命周期执行器
│                             checkpoint → pre_hooks → execute → 
│                             post_hooks → summarize → reload
│
├── skill/
│   ├── types.py           ← Skill, SkillMetadata, SkillBody
│   ├── registry.py        ← 注册 / 匹配 / 按需加载
│   ├── matcher.py         ← keyword / path / assigned 匹配
│   └── builtins/
│       ├── meta.py        ← MetaSkill（空 prompt 包装器）
│       └── recall.py      ← RecallSkill（搜索 + 注入历史）
│
├── context/
│   ├── types.py           ← Message, ScopeRecord, CompactConfig
│   ├── checkpoint.py      ← 快照管理
│   ├── summarizer.py      ← 结构化摘要生成
│   └── compact/           ← MicroCompact + AutoCompact
│
├── memory/
│   ├── store.py           ← MemoryStore（scope 持久化）
│   └── search.py          ← 搜索 + 相关性排序
│
├── protocols.py           ← 集成接口
│                             AgentExecutor（宿主提供的 Agent loop）
│                             Summarizer（LLM 摘要）
│                             TokenCounter
│                             MemoryBackend（持久化后端）
│
└── hooks.py               ← Hook 注册表
                              pre_hooks / post_hooks 扩展点
```

---

## 四、核心 API

```python
from context_stack import ContextEngine, Skill

# 初始化
engine = ContextEngine(
    executor=my_agent_loop,     # 宿主提供：怎么跑 Agent
    summarizer=my_llm,          # 宿主提供：怎么调 LLM
    counter=my_counter,         # 宿主提供：怎么数 token
    memory=my_store,            # 可选：持久化后端
)

# ─── 1. 普通 Skill ─────────────────────────────
result = engine.run(
    skill=skill,                # 从 registry 匹配到的 skill
    messages=messages,          # 当前上下文
    task="implement user auth", # 用户请求
)
# → checkpoint → inject prompt → agent works → summarize → reload
# → result.messages = 压缩后的消息列表

# ─── 2. Meta Skill ─────────────────────────────
result = engine.run_meta(
    name="用户的问题前 50 字...",
    messages=messages,
    task="帮我重构这个函数",
)
# → checkpoint → (无 prompt) → agent works → summarize → reload

# ─── 3. Recall Skill ──────────────────────────
result = engine.run_recall(
    query="之前用户注册那块密码用的什么方案？",
    messages=messages,
)
# → checkpoint → 搜索历史 + 注入 → agent works → summarize → reload

# ─── 4. Status ─────────────────────────────────
status = engine.status(messages)
# → { used_tokens, budget, scopes, recall_available }
```

---

## 五、与宿主（NovAIC）的集成边界

```
┌─────────────────────────────────────────────────────────┐
│                    NovAIC Runtime                        │
│                                                          │
│  task_queue/worker.py:                                   │
│    task arrives → match skill → engine.run(skill, msgs)  │
│                                                          │
│  宿主只需提供 3 个东西:                                  │
│    1. AgentExecutor: 怎么跑一轮 query loop               │
│    2. Summarizer: 怎么调 LLM                             │
│    3. MemoryBackend: 怎么存数据（可选）                   │
│                                                          │
│  引擎负责:                                               │
│    - 生命周期管理（checkpoint → reload 全流程）           │
│    - Skill 匹配、加载、注入                              │
│    - Memory 存储、搜索、Recall                           │
│    - 上下文预算控制                                      │
└─────────────────────────────────────────────────────────┘
```

宿主的 worker 代码变成：

```python
# Before: 手动管一切
messages = build_system_prompt(...)  # 手动注入 skills
result = query_loop(messages)        # Agent 干活
messages = auto_compact(messages)    # 手动压缩

# After: 引擎管一切
skill = engine.match(task, agent_id)  # 引擎匹配
result = engine.run(skill, messages, task)  # 引擎驱动全流程
messages = result.messages            # 已压缩
```

---

## 六、设计决策

### 为什么 Recall 是 Skill 而不是 API？

```
如果 Recall 是 API:
  details = stack.recall("user auth")  # 拿到数据
  # 然后呢？Agent 拿到数据后做的事谁来管？
  # → 没人管。回忆后的工作变成"无主消息"

如果 Recall 是 Skill:
  result = engine.run_recall("user auth", messages)
  # 回忆是 pre_hook
  # 回忆后 Agent 的工作 = execute 阶段
  # 回忆 + 后续工作 全部被 summarize 和 reload 管理
  # → 没有无主消息
```

### 为什么 Meta Skill 必须存在？

```
没有 Meta Skill 时:
  用户: "帮我修个 bug"
  → 没匹配到任何 skill
  → Agent 直接干活
  → 这些消息没有 scope 包裹
  → 压缩时只能用盲目截断

有 Meta Skill 时:
  用户: "帮我修个 bug"
  → 没匹配到任何 skill → 触发 MetaSkill
  → checkpoint → Agent 干活 → summarize → reload
  → 即使没有 skill prompt，上下文管理仍然生效
  → 每一条消息都被某个 scope 覆盖
```

### 为什么用 AgentExecutor 协议？

引擎**不应该知道怎么跑 Agent**。原因：
- NovAIC 的 Agent 是 worker → gateway → provider 多跳
- OpenCode 的 Agent 是直接 API 调用
- 测试时可以用 MockExecutor

```python
class AgentExecutor(Protocol):
    def execute(
        self,
        messages: List[Message],
        tools: List[str] | None = None,
    ) -> List[Message]:
        """运行一轮或多轮 Agent loop，返回产生的新消息"""
        ...
```
