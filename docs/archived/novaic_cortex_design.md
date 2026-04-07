# NovAIC Cortex — Complete Design Document

> **The cognitive infrastructure for AI agents — and their sole API gateway.**
> Memory, skills, workspace, shell — unified as files.
> **独立 HTTP 服务 (:19996)**，Agent 的唯一 API 入口：认知操作自己处理，业务/设备调用代理转发到 Gateway。

---

## 1. Design Philosophy

```
Everything is a file.  State is the filesystem.  The engine is a file operator.
```

**Three axioms:**
1. **File-native** — All state (scopes, skills, config, knowledge) is stored as files in S3
2. **Stateless execution** — Each shell command runs in an ephemeral sandbox; no process state survives
3. **Agent autonomy** — The engine provides tools (`read`, `write`, `shell`), the agent decides what to do

**Neuroscience mapping:**

| Brain Region | Cortex Component | Function |
|---|---|---|
| Prefrontal Cortex | Workspace `/rw` | Working memory, active tasks |
| Hippocampus | Memory `/ro/scopes/` | Long-term memory formation & retrieval |
| Cerebellum | Skills `/ro/skills/` | Procedural memory, learned skills |
| Motor Cortex | Sandbox `shell()` | Action execution |
| Sensory Cortex | FuzzyMemory | Environmental awareness, auto-injection |
| Basal Ganglia | Compaction Pipeline | Habit formation, information compression |

---

## 2. Architecture Overview

Cortex 是**独立 HTTP 服务** (:19996)，**Agent 的唯一 API 入口**。认知操作自己处理，业务/设备调用代理转发到 Gateway。

```
    Task Worker (3 tool handlers)    Sandbox CLI ($NOVAIC_TOKEN)
         │                                │
         │ shell / skill_begin / end      │ novaic chat/search/read/write/...
         │ HTTP + Capability JWT          │ HTTP + Capability JWT
         ▼                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      Cortex Service :19996                                   │
│                   "Agent 的唯一 API 入口 (操作系统)"                          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  HTTP API Layer                                                      │    │
│  │                                                                      │    │
│  │  ── Agent Tool API ──                                                │    │
│  │  /v1/shell              → Sandbox.exec()                             │    │
│  │  /v1/skill/begin        → 创建 scope + 加载 skill → instance_id     │    │
│  │  /v1/skill/end          → 归档 scope + 卸载 skill                   │    │
│  │                                                                      │    │
│  │  ── 认知操作（CLI 调用）──                                            │    │
│  │  /v1/read, write, ls    → Workspace                                  │    │
│  │  /v1/recall, tools      → Recall / Tool schemas                      │    │
│  │  GET /v1/skill/list     → list available skills                      │    │
│  │                                                                      │    │
│  │  ── 内部 API（Worker 自动调用，agent 不可见）──                       │    │
│  │  /v1/scope/create, end  → 根 scope 生命周期                          │    │
│  │  /v1/token              → JWT 签发                                   │    │
│  │                                                                      │    │
│  │  ── 业务代理（转发到 Gateway :19999）──                               │    │
│  │  /v1/proxy/chat         → Gateway /internal/.../chat                 │    │
│  │  /v1/proxy/search       → Gateway /internal/.../search               │    │
│  │  /v1/proxy/memory       → Gateway /internal/.../memory               │    │
│  │  /v1/proxy/notebook     → Gateway /internal/.../notebook             │    │
│  │  /v1/proxy/task         → Gateway /internal/.../tasks                │    │
│  │  /v1/proxy/browser      → Gateway → vmcontrol                        │    │
│  │  /v1/proxy/screenshot   → Gateway → vmcontrol                        │    │
│  │  /v1/proxy/mcp          → MCP Client                                 │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    Layer 1: Infrastructure                             │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐     │  │
│  │  │  CortexStore │  │  Workspace       │  │  Sandbox              │     │  │
│  │  │  (S3 KV)     │  │  (/ro + /rw ACL) │  │  (disposable shell)   │     │  │
│  │  │  put/get/    │  │  read/write/     │  │  exec(cmd)            │     │  │
│  │  │  list/move   │  │  archive_scope() │  │  $NOVAIC_TOKEN inject │     │  │
│  │  └──────┬───────┘  └───────┬──────────┘  └──────────┬────────────┘     │  │
│  │         └──────────────────┴─────────────────────────┘                  │  │
│  │                            │                                            │  │
│  │                      S3 Bucket / LocalFS                                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    Layer 2: Pipelines                                  │  │
│  │                                                                        │  │
│  │  ┌──────────────────────┐   ┌────────────────────────────────────┐    │  │
│  │  │  Compactor           │   │  Recall                            │    │  │
│  │  │  steps/_index.jsonl  │   │  /ro/scopes/_index.jsonl →        │    │  │
│  │  │    → summary.md      │   │    system prompt injection         │    │  │
│  │  │  mv /rw → /ro        │   │  + /ro/skills/* directory          │    │  │
│  │  │  gem fusion          │   │  + /ro/config/* preferences        │    │  │
│  │  └──────────────────────┘   └────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                    Layer 3: Auth + Proxy + Skill Lifecycle             │  │
│  │                                                                        │  │
│  │  Capability JWT 签发 + 验证 (HS256, 独立密钥, 自签自验)                │  │
│  │  claims: user_id, agent_id, scope_id, permissions, exp                │  │
│  │  业务代理：从 JWT claims 提取身份 → 构造 Gateway 内部请求              │  │
│  │  Skill 管理：skill_begin/end → 内部 scope 创建/归档/卸载              │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                              │                               │
│                                              ▼ 代理转发                      │
│                                       Gateway :19999                         │
│                                       /internal/* API                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. S3 Bucket Layout

**Key design decisions:**
- `/ro/` = **Cortex 维护的不可变层** — 只有系统操作可写（archive, skill install, gem fusion）
- `/rw/` = **Agent 的自由空间** — Agent 可任意读写
- **Scope is a step** — 子 scope 嵌套在父 scope 的 `steps/` 里，是一种特殊的 step（目录而非文件）
- **Scope 三要素** — `meta.json`（身份）、`summary.md`（结果）、`steps/`（过程）
- **Tool definitions as files** — tool schemas 存为文件，支持动态注册和技能携带

```
s3://novaic-cortex/
└── agents/
    └── {agent_id}/
        │
        ├── ro/                                  ══ Read-Only Zone (Cortex 维护) ══
        │   │
        │   ├── config/                          # Engine + Agent configuration
        │   │   ├── engine.json                  # compaction params, model prefs
        │   │   ├── personality.md               # agent persona description
        │   │   ├── constraints.md               # behavioral constraints
        │   │   └── tools/                       # Tool definitions (file-based)
        │   │       ├── _index.json              # active tool list (auto-generated)
        │   │       ├── read.json                # built-in: read file
        │   │       ├── write.json               # built-in: write file
        │   │       ├── shell.json               # built-in: sandbox exec
        │   │       └── scope_end.json           # built-in: archive scope
        │   │
        │   ├── skills/                          # Skill library
        │   │   ├── _index.md                    # Auto-generated skill directory (L1)
        │   │   ├── web-dev/
        │   │   │   ├── SKILL.md                 # Skill instructions (L2)
        │   │   │   ├── meta.json                # {name, desc, when_to_use, keywords}
        │   │   │   ├── tools/                   # Skill-specific tools (optional)
        │   │   │   │   └── browser.json
        │   │   │   └── examples/                # Reference files (L3)
        │   │   └── debugging/
        │   │       ├── SKILL.md
        │   │       └── meta.json
        │   │
        │   ├── scopes/                          # Archived scopes (long-term memory)
        │   │   ├── _index.jsonl                 # Flat index: scope_id → path + metadata
        │   │   ├── task-001/                    # Root scope (tree structure)
        │   │   │   ├── meta.json                # {name, skill, start_time, ended_at, phase}
        │   │   │   ├── summary.md               # Compacted summary (fuzzy memory source)
        │   │   │   └── steps/                   # Execution timeline (tool files + scope dirs)
        │   │   │       ├── _index.jsonl          # Step index (lightweight metadata)
        │   │   │       ├── 0001_tool_search.json # Tool step = file
        │   │   │       ├── 0002_scope_research/  # Scope step = directory (recursive)
        │   │   │       │   ├── meta.json
        │   │   │       │   ├── summary.md
        │   │   │       │   └── steps/
        │   │   │       │       ├── _index.jsonl
        │   │   │       │       ├── 0001_tool_fetch.json
        │   │   │       │       └── 0002_scope_deep/
        │   │   │       │           ├── meta.json
        │   │   │       │           ├── summary.md
        │   │   │       │           └── steps/
        │   │   │       └── 0003_tool_write.json
        │   │   │
        │   │   └── __fused__/                   # Gem Fusion products
        │   │       └── fuse_L1_001/
        │   │           ├── meta.json
        │   │           └── summary.md
        │   │
        │   └── knowledge/                       # Long-term learned knowledge
        │       ├── preferences.md
        │       └── learned_patterns.md
        │
        └── rw/                                  ══ Read-Write Zone (Agent 自由空间) ══
            │
            ├── active/                          # Currently executing scope tree
            │   └── task-001/                    # Root scope
            │       ├── meta.json                # {name, skill, start_time, phase: "executing"}
            │       └── steps/
            │           ├── _index.jsonl
            │           ├── 0001_tool_search.json
            │           └── 0002_scope_research/  # Child scope (LIFO — must close before parent)
            │               ├── meta.json         # phase: "executing" or "archived"
            │               └── steps/
            │
            └── scratch/                         # Global scratch (no scope)
                └── notes.md
```

---

## 4. Component Specifications

### 4.1 CortexStore (S3 Abstraction)

> Pure KV object storage. Knows nothing about workspaces or scopes.

```python
class CortexStore(ABC):
    """Backend-agnostic object storage interface."""

    # Core CRUD
    async def put(self, key: str, data: bytes, content_type: str = "") -> None: ...
    async def get(self, key: str) -> bytes: ...
    async def get_text(self, key: str, encoding: str = "utf-8") -> str: ...
    async def exists(self, key: str) -> bool: ...
    async def delete(self, key: str) -> None: ...

    # Listing
    async def list_objects(self, prefix: str, delimiter: str = "/") -> List[ObjectInfo]: ...
    async def list_recursive(self, prefix: str) -> List[str]: ...

    # Convenience
    async def put_json(self, key: str, obj: dict) -> None: ...
    async def get_json(self, key: str) -> dict: ...
    async def copy(self, src: str, dst: str) -> None: ...
    async def move(self, src: str, dst: str) -> None: ...
    async def move_prefix(self, src_prefix: str, dst_prefix: str) -> int: ...
```

**Backends:**

| Backend | Use Case | Implementation |
|---|---|---|
| `LocalFileStore` | Dev / testing | Local filesystem simulates S3 |
| `S3Store` | Production | AWS S3 / MinIO |
| `MemoryStore` | Unit tests | In-memory dict |

### 4.2 Workspace

> Dual-zone file manager with ACL enforcement and tree-structured scope management.

```python
class Workspace:
    def __init__(self, store: CortexStore, agent_id: str): ...

    # Read (both /ro and /rw)
    async def read(self, path: str) -> str: ...
    async def read_bytes(self, path: str) -> bytes: ...
    async def list_dir(self, path: str) -> List[FileEntry]: ...
    async def exists(self, path: str) -> bool: ...

    # Write (only /rw — raises PermissionError for /ro)
    async def write(self, path: str, content: str) -> None: ...
    async def write_bytes(self, path: str, data: bytes) -> None: ...
    async def write_json(self, path: str, obj: dict) -> None: ...
    async def append_line(self, path: str, line: str) -> None: ...

    # Scope lifecycle (system-level)
    async def create_scope(
        self, scope_id: str, name: str, skill: str = "",
        parent_path: str | None = None,  # e.g. "/rw/active/task-001"
    ) -> str: ...
    async def archive_root_scope(self, scope_id: str, summary: str) -> str: ...
    async def complete_child_scope(self, scope_path: str, summary: str) -> None: ...

    # Steps (unified timeline)
    async def write_step(self, scope_path: str, step: dict) -> str: ...
    async def list_steps(self, scope_path: str) -> List[str]: ...
    async def read_step_index(self, scope_path: str) -> List[dict]: ...

    # Initialization
    async def initialize(self) -> None: ...
```

**ACL Rules:**

| Path Pattern | Agent Read | Agent Write | System Write |
|---|---|---|---|
| `/ro/**` | ✅ | ❌ | ✅ (archive, skill install) |
| `/rw/**` | ✅ | ✅ | ✅ |

**Scope creation — tree nesting:**

```python
# Root scope — created at /rw/active/{id}/
create_scope("task-001", "Deploy fix", parent_path=None)
  → /rw/active/task-001/
  → /rw/active/task-001/meta.json
  → /rw/active/task-001/steps/_index.jsonl

# Child scope — created as a step in parent's steps/
create_scope("research", "Research sub-task", parent_path="/rw/active/task-001")
  → allocates next seq in parent's steps/ (e.g. 0002)
  → /rw/active/task-001/steps/0002_scope_research/
  → /rw/active/task-001/steps/0002_scope_research/meta.json
  → /rw/active/task-001/steps/0002_scope_research/steps/_index.jsonl
  → appends index entry to parent's steps/_index.jsonl
```

**Scope archival (LIFO):**

```
Children close first (LIFO stack):

  complete_child_scope(scope_path, summary):
    1. Write summary.md to scope_path/
    2. Update meta.json (phase → "archived", ended_at)
    — NO move needed — child stays nested under parent

  archive_root_scope(scope_id, summary):
    1. Write summary.md to /rw/active/{id}/
    2. Update meta.json (phase → "archived", ended_at)
    3. move_prefix /rw/active/{id}/ → /ro/scopes/{id}/
       (entire tree moves atomically — all children included)
    4. Append entries to /ro/scopes/_index.jsonl
```

### 4.3 Sandbox

> **一次性 (Disposable)**、无状态、短暂的命令执行环境。每次 `exec()` 创建全新环境，执行完立即销毁，不保留任何跨调用状态。

```python
@dataclass
class ShellResult:
    stdout: str
    stderr: str
    exit_code: int
    files_changed: list[str]

class Sandbox:
    def __init__(self, workspace: Workspace, *, max_sync_bytes: int | None = None): ...

    async def exec(
        self,
        command: str,
        timeout: int = 30,
        cwd: str | None = None,
    ) -> ShellResult: ...
```

**核心原则：一次性执行 (Disposable Execution)**

```
每次 exec() 是一个完全独立的生命周期：
  ① 创建 → ② 物化 → ③ 执行 → ④ 回写 → ⑤ 销毁
没有跨 exec() 的缓存、连接、进程池。
这保证了：
  - 安全性：前一次执行不可能泄漏给下一次
  - 可靠性：不依赖缓存一致性
  - 简单性：无需 GC 或缓存失效策略
```

**执行周期 (每次 exec):**

```
1. Create temp directory      ← 全新临时目录
2. Sync /ro + /rw from S3     ← 从 Store 全量拉取（无缓存）
3. Snapshot /rw (mtime + size) ← 执行前快照
4. Inject $NOVAIC_TOKEN        ← 短期 JWT（见 §4.3.1）
5. Execute command             ← subprocess 隔离
6. Diff /rw snapshot           ← 检测文件变更
7. Sync changed files → S3     ← 只回写变更部分
8. Destroy temp directory      ← 完全清理，无残留
```

**Environment variables injected:**

| Variable | Value | Purpose |
|---|---|---|
| `$RO` | `/tmp/novaic-xxx/ro` | Read-only workspace |
| `$RW` | `/tmp/novaic-xxx/rw` | Read-write workspace |
| `$HOME` | `$RW` | Agent working directory |
| `$NOVAIC_TOKEN` | `eyJhbGci...` | Capability Token (JWT) for CLI tool auth |
| `$NOVAIC_API` | `http://cortex:19996` | Cortex API endpoint (CLI 直达) |

**分阶段隔离 (Progressive Isolation):**

| Phase | 技术 | 隔离级别 | 开销 | 适用场景 |
|---|---|---|---|---|
| **Phase 1 (当前)** | `tempfile` + `subprocess` | 进程级 | ~10ms | 单用户 / 开发 |
| **Phase 2** | nsjail (Linux namespaces + seccomp) | 命名空间 | ~50ms | 多用户生产 |
| **Phase 3** | Firecracker microVM / gVisor | 内核级 | ~125ms | 强隔离生产 |

Phase 1 → Phase 2 切换对上层透明：`Sandbox` 接口不变，仅 `_execute()` 内部从 `subprocess` 换成 `nsjail --config ...`。

#### 4.3.1 Sandbox-first 执行模型

**核心决策：除认知控制工具 (skill_begin, skill_end, scope_end) 外，所有工具在 Sandbox 内作为 CLI 执行。**

```
┌──────────────────────────────────────────────────────────────┐
│                      LLM → tool_call                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  shell("novaic chat 'hello'")                         │    │
│  │  shell("novaic search 'JWT best practices'")          │    │
│  │  shell("novaic read /ro/scopes/_index.jsonl | jq .") │    │
│  │  shell("grep -r JWT $RO/scopes/ | head -5")          │    │
│  │  shell("python3 $RW/analyze.py")                      │    │
│  │                                                        │    │
│  │  Worker → Cortex /v1/shell → Sandbox.exec()           │    │
│  │                                                        │    │
│  │  Sandbox 内:                                           │    │
│  │    novaic * → HTTP → Cortex /v1/* (快, ~100ms)         │    │
│  │    认知操作 → Cortex 自己处理                           │    │
│  │    业务操作 → Cortex /v1/proxy/* → Gateway              │    │
│  │    原生 shell → 操作本地 $RO/$RW (需 S3 同步, ~1-5s)   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────┐                          │
│  │  skill_begin("web-dev")        │ 技能控制：Worker 直接    │
│  │    → 返回 instance_id          │ 调 Cortex，不经 Sandbox  │
│  │  skill_end("sk_xxx", "done")  │ (改变 agent 运行状态)    │
│  └────────────────────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

**为什么 shell-first？**
- Agent 本质上在"操作一台电脑"，shell 是最自然的接口
- CLI 可组合（管道、循环、与 grep/python/curl 混用），结构化 tool call 不能
- LLM tool list 极简（3 个），减少 LLM 选择负担
- 所有工具统一通过 Cortex API，Sandbox 只需认一个地址

**为什么 skill_begin/end 不进 Sandbox？**
它们改变 agent 的运行状态（system prompt、tool 列表），Worker 需要在下一轮 LLM 调用前感知变化。

**为什么没有 scope_end？**
Scope 是 Cortex 内部概念，agent 不需要知道。根 scope 由 Worker 自动管理，技能 scope 由 skill_begin/end 隐式管理。

#### 4.3.2 Capability Token (JWT) 鉴权

沙箱内 CLI 工具通过短期 JWT 与 **Cortex** 通信（Cortex 是 agent 唯一 API 入口），无需硬编码密钥。

```
Scope 开始时:
  Worker 调 Cortex /v1/token → Cortex 签发 JWT
    ┌──────────────────────────────┐
    │ Header: { alg: HS256 }       │
    │ Payload:                     │
    │   user_id:  "u_xxx"          │
    │   agent_id: "a_yyy"          │
    │   scope_id: "task-001"       │
    │   permissions: ["chat",      │
    │     "search", "memory",      │
    │     "browser", "storage"]    │
    │   exp: now + 30min           │
    │   iss: "novaic-cortex"       │
    │ Signature: HMAC(CORTEX_JWT_SECRET) │
    └──────────────────────────────┘
    ↓
  注入为 $NOVAIC_TOKEN 环境变量
    ↓
  CLI 工具使用:
    novaic chat "hello"
      → POST $NOVAIC_API/v1/proxy/chat          ← Cortex (不是 Gateway)
      → Authorization: Bearer $NOVAIC_TOKEN
      → Cortex 验证 JWT → 提取 user_id/agent_id
      → Cortex 转发到 Gateway /internal/.../chat ← 服务间信任
```

**安全属性:**

| 属性 | 保证 |
|---|---|
| **短期有效** | `exp` = scope 开始 + 30min（可配置） |
| **最小权限** | `permissions` 数组限定可调用的 Cortex API |
| **Scope 绑定** | `scope_id` 确保 token 只在指定 scope 内有效 |
| **多用户安全** | `user_id` + `agent_id` 确保资源隔离 |
| **不可伪造** | HMAC 签名，agent 拿不到签名密钥 |
| **沙箱不持有密钥** | 密钥仅在 Cortex 服务进程，沙箱内只有 JWT 本身 |
| **Sandbox 只认 Cortex** | `$NOVAIC_API` 指向 Cortex，不暴露 Gateway 地址 |

**Cortex 自签自验:**

```python
# novaic_cortex/auth.py — Cortex 自签自验，密钥独立于 Gateway
async def verify_capability_token(token: str) -> TokenClaims:
    payload = jwt.decode(token, CORTEX_JWT_SECRET, algorithms=["HS256"])
    if payload["exp"] < time.time():
        raise ExpiredTokenError()
    return TokenClaims(
        user_id=payload["user_id"],
        agent_id=payload["agent_id"],
        scope_id=payload["scope_id"],
        permissions=payload["permissions"],
    )

async def issue_capability_token(user_id, agent_id, scope_id, permissions, ttl=1800) -> str:
    payload = {
        "user_id": user_id, "agent_id": agent_id,
        "scope_id": scope_id, "permissions": permissions,
        "exp": time.time() + ttl, "iss": "novaic-cortex",
    }
    return jwt.encode(payload, CORTEX_JWT_SECRET, algorithm="HS256")
```

**Cortex 代理转发到 Gateway 时**，使用服务间信任（内部 API key 或 mTLS），不传递 Capability JWT 给 Gateway。Gateway 视 Cortex 为可信内部调用方。

**JWT 双轨制：** Gateway 签用户 JWT（`JWT_SECRET`），Cortex 签 capability JWT（`CORTEX_JWT_SECRET`）。密钥独立，职责隔离。

**多用户就绪:** JWT 天然支持多租户——不同用户的 agent 拿到不同的 `user_id` claim，Cortex 据此做资源隔离，无需额外机制。

### 4.4 Compactor (CompactionPipeline)

> Scope archival pipeline. Reads `steps/_index.jsonl` to build summary context.

```python
@dataclass
class CompactResult:
    scope_id: str
    summary: str
    archive_path: str

class Compactor:
    def __init__(
        self,
        workspace: Workspace,
        summarizer: Summarizer | None = None,
        fusion_factor: int = 5,
    ): ...

    async def compact(self, scope_id: str, report: str | None = None) -> CompactResult: ...
```

**Pipeline steps:**

```
scope_end(id, report)
  │
  ├─ 1. Read steps/_index.jsonl from the scope tree
  ├─ 2. Generate summary:
  │      ├─ report provided → use as-is (cheapest)
  │      ├─ summarizer available → LLM call (with step index as context)
  │      └─ neither → fallback template from index stats
  ├─ 3. For child scopes: complete_child_scope(path, summary)
  │      For root scope: archive_root_scope(id, summary)
  ├─ 4. Check gem fusion threshold (root scopes only)
  └─ 5. Update Recall (fuzzy memory)
```

### 4.5 Gem Fusion (N-ary Carry)

> Progressive scope summarization. Operates on **root-level** scopes in `/ro/scopes/`. Each root scope's summary already incorporates its subtree.

```
L0: [scope-0] [scope-1] [scope-2] [scope-3] [scope-4]  ← 5 root scopes
         ↓         ↓         ↓         ↓         ↓
L1:              [★ fused-0]                              ← 1 meta-summary

...after 25 root scopes total:
L1: [★ f-0] [★ f-1] [★ f-2] [★ f-3] [★ f-4]           ← 5 L1 fusions!
         ↓         ↓         ↓         ↓         ↓
L2:              [★★ mega-0]                              ← CASCADE!
```

**Storage:** Fused scopes live in `/ro/scopes/__fused__/fuse_L{level}_{seq}/`.

### 4.6 Recall (FuzzyMemoryGenerator)

> Pre-LLM system prompt injection.

```python
class Recall:
    def __init__(self, workspace: Workspace, token_budget: int = 4000): ...

    async def generate(self) -> str:
        """Generate system prompt injection content."""
        sections = []
        sections.append(await self._build_memory_section())     # /ro/scopes/_index.jsonl
        sections.append(await self._build_skill_directory())    # /ro/skills/_index.md
        sections.append(await self._build_config_section())     # /ro/config/*
        return "\n\n---\n\n".join(filter(None, sections))
```

**Recall reads from `/ro/scopes/_index.jsonl`** — a flat index of all scopes (including nested ones) with their full paths:

```jsonl
{"scope_id":"task-001","path":"/ro/scopes/task-001/","name":"部署修复","depth":0,"ts":1712345678}
{"scope_id":"research","path":"/ro/scopes/task-001/steps/0002_scope_research/","name":"调研","depth":1,"parent":"task-001","ts":1712345700}
```

**Progressive recall (agent-driven):**

```python
# Level 0: Browse flat index
read("/ro/scopes/_index.jsonl")

# Level 1: Read specific scope summary
read("/ro/scopes/task-001/summary.md")

# Level 2: Drill into child scope
read("/ro/scopes/task-001/steps/0002_scope_research/summary.md")

# Level 3: Read specific tool step
read("/ro/scopes/task-001/steps/0001_tool_search.json")

# Cross-scope search (includes entire subtree)
shell("grep -ril 'JWT' $RO/scopes/task-001/")
```

---

## 5. Cortex Runtime (HTTP Service + Façade + Proxy)

> 独立 HTTP 服务 (:19996)，Agent 的唯一 API 入口。认知操作自己处理，业务/设备调用代理转发到 Gateway。

```python
class Cortex:
    """NovAIC Cortex — the agent's operating system."""

    def __init__(
        self,
        store: CortexStore,
        agent_id: str,
        summarizer: Summarizer | None = None,
        gateway_internal_url: str = "http://gateway:19999",
    ):
        self.store = store
        self.workspace = Workspace(store, agent_id)
        self.sandbox = Sandbox(self.workspace)
        self.compactor = Compactor(self.workspace, summarizer)
        self.recall = Recall(self.workspace)
        self._gateway_url = gateway_internal_url

    async def initialize(self) -> None:
        await self.workspace.initialize()

    # ── 认知操作（Cortex 自处理）──

    async def tool_read(self, path: str) -> str:
        return await self.workspace.read(path)

    async def tool_write(self, path: str, content: str) -> str:
        await self.workspace.write(path, content)
        return f"Written to {path}"

    async def tool_shell(self, command: str, timeout: int = 30) -> ShellResult:
        return await self.sandbox.exec(command, timeout)

    # ── Skill 生命周期（Agent 使用）──

    async def skill_begin(self, name: str, parent_scope_path: str | None = None) -> dict:
        """开始技能 → 内部创建 scope + 加载 SKILL.md + 注册工具 → 返回 instance_id"""
        scope_path = await self.workspace.create_scope(
            scope_id=f"skill_{name}_{uuid4().hex[:8]}",
            name=name, skill=name, parent_path=parent_scope_path,
        )
        skill_md = await self.workspace.read(f"/ro/skills/{name}/SKILL.md")
        tools = await self._load_skill_tools(name)
        instance_id = f"sk_{scope_path.split('/')[-2]}"
        self._active_skills[instance_id] = SkillInstance(
            instance_id=instance_id, name=name,
            scope_path=scope_path, skill_md=skill_md, tools=tools,
        )
        self._skill_stack.append(instance_id)
        return {"instance_id": instance_id, "name": name, "tools": [t["name"] for t in tools]}

    async def skill_end(self, instance_id: str, report: str) -> dict:
        """结束技能。校验通过 → 归档 + 压缩；校验失败 → 返回 warning。"""
        if instance_id not in self._active_skills:
            return {"ok": False, "warning": f"Unknown skill instance: {instance_id}"}

        if self._skill_stack[-1] != instance_id:
            top = self._active_skills[self._skill_stack[-1]]
            current = self._active_skills[instance_id]
            return {
                "ok": False,
                "warning": f"Cannot end {instance_id} ({current.name}): "
                           f"active child skill {top.instance_id} ({top.name}) "
                           f"must be ended first.",
            }

        skill = self._active_skills.pop(instance_id)
        self._skill_stack.pop()
        await self.workspace.complete_child_scope(skill.scope_path, summary=report)
        result = await self.compactor.compact_scope(skill.scope_path, report)
        return {"ok": True, "instance_id": instance_id, "archive_path": result.archive_path}

    # ── 内部 Scope 管理（Worker 自动调用，agent 不可见）──

    async def scope_create(self, scope_id: str, name: str) -> str:
        return await self.workspace.create_scope(scope_id, name)

    async def scope_end(self, scope_id: str, report: str) -> dict:
        result = await self.compactor.compact(scope_id, report)
        return {"ok": True, "scope_id": scope_id, "archive_path": result.archive_path}

    # ── 业务代理（转发到 Gateway）──

    async def proxy_to_gateway(self, endpoint: str, payload: dict, claims: TokenClaims) -> dict:
        """Forward business calls to Gateway /internal/* using service trust."""
        url = f"{self._gateway_url}/internal/{endpoint}"
        headers = {
            "X-Internal-Key": CORTEX_INTERNAL_KEY,
            "X-User-Id": claims.user_id,
            "X-Agent-Id": claims.agent_id,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.json()

    # ── Pre-LLM Hook ──

    async def prepare_system_prompt(self) -> str:
        return await self.recall.generate()

    # ── Tool Schema Loading ──

    async def load_tool_schemas(self) -> list[dict]:
        """Load tool definitions from /ro/config/tools/ + skill tools."""
        schemas = []
        tools_dir = "/ro/config/tools/"
        for entry in await self.workspace.list_dir(tools_dir):
            if entry.name.endswith(".json") and not entry.name.startswith("_"):
                schema = json.loads(await self.workspace.read(entry.path))
                schemas.append(schema)
        for skill in await self.workspace.list_dir("/ro/skills/"):
            if skill.is_dir:
                skill_tools = f"/ro/skills/{skill.name}/tools/"
                if await self.workspace.exists(skill_tools):
                    for entry in await self.workspace.list_dir(skill_tools):
                        if entry.name.endswith(".json"):
                            schema = json.loads(await self.workspace.read(entry.path))
                            schemas.append(schema)
        return schemas

    # ── Skill Management ──

    async def install_skill(self, name: str, skill_md: str, meta: dict) -> str:
        base = f"agents/{self.workspace.agent_id}/ro/skills/{name}/"
        await self.store.put(base + "SKILL.md", skill_md.encode())
        await self.store.put_json(base + "meta.json", meta)
        await self._rebuild_skill_index()
        return f"/ro/skills/{name}/"
```

---

## 6. Tool Definitions (File-based)

Tool schemas are stored as JSON files in `/ro/config/tools/`. 在极简 tool 模型下，LLM 只看到 4 个结构化 tool，但 Sandbox 内 `novaic` CLI 的可用命令（认知 + 业务 + 设备 + MCP）也以文件形式声明。

**`/ro/config/tools/shell.json`** (LLM 的主要工具):

```json
{
  "name": "shell",
  "description": "Execute a command in the sandbox. Use 'novaic' CLI for all operations: novaic read, novaic chat, novaic search, novaic browser, etc. Use native commands (grep, python, curl) for local file operations.",
  "parameters": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "Shell command to execute"
      }
    },
    "required": ["command"]
  }
}
```

**`/ro/config/tools/skill_begin.json`:**

```json
{
  "name": "skill_begin",
  "description": "Start a skill. Returns instance_id for use with skill_end.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": { "type": "string", "description": "Skill name (e.g. web-dev, debugging)" }
    },
    "required": ["name"]
  }
}
```

**`/ro/config/tools/skill_end.json`:**

```json
{
  "name": "skill_end",
  "description": "End a skill and submit report. Triggers memory archival.",
  "parameters": {
    "type": "object",
    "properties": {
      "instance_id": { "type": "string", "description": "Instance ID from skill_begin" },
      "report": { "type": "string", "description": "Summary of what was accomplished" }
    },
    "required": ["instance_id", "report"]
  }
}
```

**Skills can carry their own CLI extensions:**

```
/ro/skills/web-dev/
├── SKILL.md
├── meta.json
└── tools/                    ← skill-specific tool definitions
    └── browser.json          ← 描述 novaic browser 子命令的 schema（供 LLM 参考）
```

**`_index.json`** is auto-generated:

```json
["shell", "skill_begin", "skill_end"]
```

**Advantages:**
- Dynamic tool registration — add/remove tools without code changes
- Skills can declare their own CLI commands (loaded as `novaic` subcommands)
- Agent can `novaic tools` to understand its current capabilities
- Consistent with "everything is a file" philosophy

---

## 6.1 极简 Tool 模型 (Sandbox-first, 3 Tool)

**核心决策：LLM 只看到 3 个结构化 tool。Scope 对 agent 完全不可见。**

### LLM Tool List

```json
[
  {
    "name": "shell",
    "description": "在 Sandbox 中执行命令。所有操作通过 novaic CLI 完成。",
    "parameters": { "command": { "type": "string" } }
  },
  {
    "name": "skill_begin",
    "description": "开始一个技能。返回 instance_id，用于 skill_end。",
    "parameters": { "name": { "type": "string" } }
  },
  {
    "name": "skill_end",
    "description": "结束技能并提交报告。触发记忆归档。",
    "parameters": { "instance_id": { "type": "string" }, "report": { "type": "string" } }
  }
]
```

### Skill 生命周期（Agent 视角）

```
skill_begin("web-dev")
  → 返回 instance_id: "sk_abc123"
  → 注入 agent context（下轮 LLM 可见）
  → Agent 可以嵌套开始更多技能

skill_end("sk_abc123", "JWT 问题已解决")
  → 校验通过 → 归档成功，返回 { ok: true, instance_id, archived: true }
  → 校验失败 → 技能保持活跃，返回 warning（作为正常工具结果）
```

### skill_end 校验规则

`skill_end` 不是无条件成功的。Cortex 会校验该技能是否可被关闭：

```
skill_end("sk_abc123", report):
  ① instance_id 存在？
     否 → 返回 { ok: false, warning: "Unknown skill instance: sk_abc123" }

  ② LIFO 校验：该技能是否是栈顶（无活跃子技能）？
     否 → 返回 { ok: false, warning: "Cannot end sk_abc123 (web-dev): 
           active child skill sk_def456 (debugging) must be ended first." }

  ③ 校验通过 → 执行关闭：
     → 归档 scope + 记忆压缩 + 卸载 SKILL.md
     → 返回 { ok: true, instance_id: "sk_abc123", archived: true }
```

**失败时的行为：**
- **不抛异常**，作为正常的工具调用结果返回 warning
- **技能保持活跃**，agent 可以根据 warning 信息修正行为
- LLM 看到 warning 后通常会先关闭子技能，再重试

**典型交互：**

```
Agent: skill_end("sk_001", "done")
Cortex: { ok: false, warning: "Cannot end sk_001 (web-dev): active child skill sk_002 (debugging) must be ended first." }
Agent: skill_end("sk_002", "bug found")    ← 先关子技能
Cortex: { ok: true, instance_id: "sk_002" }
Agent: skill_end("sk_001", "done")          ← 再关父技能
Cortex: { ok: true, instance_id: "sk_001" }
```

### Skill 生命周期（Cortex 内部）

```
skill_begin("web-dev"):
  → 创建 scope (嵌入当前活跃 scope 的 steps/)
  → 加载 /ro/skills/web-dev/SKILL.md → 注入 system prompt
  → 注册技能工具 (/ro/skills/web-dev/tools/*.json)
  → 生成 instance_id = f"sk_{scope_id}"
  → 推入 skill_stack (维护 LIFO 顺序)
  → 返回 { instance_id, skill_name, active_tools }

skill_end("sk_abc123", report):
  → 解析 scope_id from instance_id
  → 校验 instance_id 存在 + LIFO 栈顶
  → 校验失败 → 返回 { ok: false, warning: "..." }
  → 校验成功 →
      → complete_child_scope(scope_path, summary=report)
      → 卸载 SKILL.md + 反注册技能工具
      → 从 skill_stack 弹出
      → 触发 Compactor (记忆压缩)
      → 如果是根 scope 下的最后一个技能 → gem fusion 检查
      → 返回 { ok: true, instance_id, archived: true }
```

**Scope 对 agent 完全不可见：**
- 根 scope 由 Worker 在任务开始/结束时自动管理
- 技能 scope 由 skill_begin/end 隐式创建/关闭
- Agent 只知道 "我有一个技能 sk_abc123 在运行"

### 嵌套示例

```
Worker 自动: scope_create("root-task")     ← agent 不知道

skill_begin("web-dev")         → sk_001    ← agent 看到 instance_id
  skill_begin("debugging")     → sk_002    ← 内部: 子 scope 嵌入 sk_001
  skill_end("sk_002", "found") ← LIFO
skill_end("sk_001", "fixed")

Worker 自动: scope_end("root-task")         ← agent 不知道
```

### Agent 典型操作

```bash
# 认知操作（novaic CLI → Cortex 直接处理）
novaic read /ro/scopes/task-001/summary.md
novaic write /rw/scratch/notes.md "my findings"
novaic recall

# 业务操作（novaic CLI → Cortex → 代理转发 Gateway）
novaic chat "我找到了问题所在"
novaic search "JWT refresh token best practices"
novaic memory save auth_pattern "use short-lived JWT"

# 设备操作（novaic CLI → Cortex → 代理转发 Gateway → vmcontrol）
novaic browser navigate https://docs.example.com
novaic screenshot

# 原生 shell（操作本地 $RO/$RW）
grep -rl "JWT" $RO/scopes/ | head -5
python3 $RW/analyze.py

# 组合
novaic search "error handling" | jq -r '.results[0].url' | xargs novaic browser navigate
```

### 执行路径

```
LLM → tool_call: skill_begin("web-dev")
  → Worker → Cortex /v1/skill/begin
  → 内部创建 scope + 加载 skill → 返回 instance_id

LLM → tool_call: shell("novaic chat 'hello'")
  → Worker → Cortex /v1/shell → Sandbox.exec()
    → novaic chat → Cortex /v1/proxy/chat → Gateway

LLM → tool_call: skill_end("sk_abc123", "done")
  → Worker → Cortex /v1/skill/end
  → 内部归档 scope + 记忆压缩 + 卸载 skill
```

---

## 6.2 Cortex CLI — Agent 的完整命令行 (Sandbox 内预装)

Sandbox 内预装 `novaic` CLI，`$NOVAIC_API` 指向 **Cortex :19996**（Agent 的唯一 API 入口）。所有操作——认知、业务、设备、MCP——统一通过此 CLI 完成。

### 完整命令表

```
── 认知操作（Cortex 自己处理）──
novaic read <path>                           读取工作区文件
novaic write <path> [content | -]            写入文件（- 表示 stdin）
novaic ls <path>                             列出目录
novaic recall                                获取 fuzzy memory
novaic tools                                 列出当前可用工具

── 业务操作（Cortex 代理到 Gateway）──
novaic chat <message>                        回复用户
novaic search <query> [--limit N]            搜索网页
novaic memory save <key> <value>             保存记忆
novaic memory recall <key>                   检索记忆
novaic memory delete <key>                   删除记忆
novaic memory list                           列出记忆命名空间
novaic notebook write <title> <content>      写笔记
novaic notebook read <id>                    读笔记
novaic notebook list                         列出笔记
novaic task create <title>                   创建任务
novaic task complete <id>                    完成任务

── 设备操作（Cortex 代理到 Gateway → vmcontrol）──
novaic browser navigate <url>                打开网页
novaic browser content                       获取页面内容
novaic screenshot                            截图
novaic keyboard type <text>                  键盘输入
novaic mouse click <x> <y>                   鼠标点击

── MCP 外部工具 ──
novaic mcp <tool_name> [args_json]           调用 MCP 工具
```

### 组合使用

```bash
# 搜索 + 浏览 + 回复 (管道组合)
novaic search "JWT refresh token" | jq -r '.results[0].url' | xargs novaic browser navigate
novaic browser content | jq -r '.text[:500]'
novaic chat "找到了相关文档，JWT 应该使用 refresh token 机制"

# 批量检查归档 scope
for scope in $(novaic ls /ro/scopes/ | head -5); do
    echo "=== $scope ==="
    novaic read /ro/scopes/$scope/summary.md
done

# 混合 novaic + 原生 shell
grep -rl "JWT" $RO/scopes/ | while read f; do head -5 "$f"; done
novaic write /rw/scratch/findings.md "$(grep -c 'JWT' $RO/scopes/*/summary.md)"

# 记忆工作流
novaic memory save auth_insight "short-lived JWT + refresh token is best"
novaic memory recall auth
```

### 实现

单个 Python 脚本（零外部依赖），`$NOVAIC_API` → Cortex :19996，预装在 Sandbox `$PATH`：

```python
#!/usr/bin/env python3
"""novaic — Agent CLI. All calls go to Cortex :19996 (the sole API gateway for agents)."""
import sys, os, json, urllib.request

API = os.environ["NOVAIC_API"]   # http://cortex:19996
TOKEN = os.environ.get("NOVAIC_TOKEN", "")

def _req(method, path, body=None):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    else:
        data = None
    req = urllib.request.Request(f"{API}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode()

ROUTES = {
    # Cognitive (Cortex handles directly)
    "read":       lambda a: print(_req("GET",  f"/v1/read?path={a[0]}")),
    "write":      lambda a: _req("POST", "/v1/write", {"path": a[0], "content": _content(a)}),
    "ls":         lambda a: print(_req("GET",  f"/v1/ls?path={a[0]}")),
    "recall":     lambda a: print(_req("GET",  "/v1/recall")),
    "tools":      lambda a: print(_req("GET",  "/v1/tools")),
    # Business (Cortex proxies to Gateway)
    "chat":       lambda a: _req("POST", "/v1/proxy/chat",    {"message": a[0]}),
    "search":     lambda a: print(_req("POST", "/v1/proxy/search", {"query": a[0]})),
    "memory":     lambda a: _memory(a),
    "notebook":   lambda a: _notebook(a),
    "task":       lambda a: _task(a),
    # Device (Cortex proxies to Gateway → vmcontrol)
    "browser":    lambda a: _browser(a),
    "screenshot": lambda a: print(_req("POST", "/v1/proxy/screenshot", {})),
    "keyboard":   lambda a: _req("POST", "/v1/proxy/keyboard", {"action": a[0], "text": a[1]}),
    "mouse":      lambda a: _req("POST", "/v1/proxy/mouse", {"action": a[0], "x": a[1], "y": a[2]}),
    # MCP
    "mcp":        lambda a: print(_req("POST", "/v1/proxy/mcp", {"tool": a[0], "args": json.loads(a[1]) if len(a)>1 else {}})),
}

def _content(a):
    return sys.stdin.read() if len(a) < 2 or a[1] == "-" else a[1]

if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    ROUTES[cmd](args)
```

### 关键约束

- **novaic CLI → Cortex :19996 → 所有操作**：认知操作 Cortex 自处理，业务/设备操作 Cortex 代理转发
- **novaic CLI 调用不触发 S3 同步**（快，~100ms），原生 shell 操作 `$RO/$RW` 需要 S3 同步（慢，~1-5s）
- CLI 不持有签名密钥，只持有 Capability JWT → 沙箱内无法伪造凭证
- `$NOVAIC_API` 只指向 Cortex → Sandbox 不知道 Gateway 地址 → 安全隔离

---

## 7. Skill System

```
/ro/skills/
├── _index.md      ← auto-generated skill directory
├── web-dev/
│   ├── meta.json  ← Layer 1 (name, desc, when_to_use, keywords)
│   ├── SKILL.md   ← Layer 2 (prompt + workflow)
│   ├── tools/     ← skill-specific tool definitions
│   │   └── browser.json
│   └── examples/  ← Layer 3 (reference files)
└── code-review/
    ├── meta.json
    └── SKILL.md
```

**Progressive loading:**

```
1. System prompt: auto-includes _index.md → "你有 web-dev, code-review 技能"
2. Agent needs skill: read("/ro/skills/web-dev/SKILL.md") → loads full instructions
3. Agent needs reference: read("/ro/skills/web-dev/examples/react-component.tsx")
4. Skill tools auto-registered → browser tool available when web-dev is active
```

---

## 8. Scope Lifecycle

### 8.1 Core Principle: Scope IS a Step

A scope is both a container (holds its own steps) and a step (lives inside its parent's `steps/`).

```
scope/                     ← 三要素
├── meta.json              ← 身份 (who): name, skill, phase, timestamps
├── summary.md             ← 结果 (what): compacted summary, written on close
└── steps/                 ← 过程 (how): chronological execution timeline
    ├── _index.jsonl       ← lightweight step metadata
    ├── 0001_tool_*.json   ← tool step = file
    ├── 0002_scope_*/      ← scope step = directory (recursive same structure)
    └── 0003_tool_*.json
```

**Two step forms (same `_index.jsonl`):**

| Form | Filename | Contents |
|------|----------|----------|
| Tool step | `{seq:04d}_tool_{call_id}.json` | Single JSON file with call_id, tool, status, result, artifacts |
| Scope step | `{seq:04d}_scope_{scope_id}/` | Directory with meta.json + summary.md + steps/ (recursive) |

### 8.2 Lifecycle Flow

Scope 是 Cortex 的**内部概念**，agent 不可见。Agent 通过 `skill_begin/end` 间接驱动 scope 生命周期。

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   ① CREATE ROOT SCOPE (Worker 自动，agent 不可见)            │
│   │  Worker.on_task_start → scope_create("task-001")         │
│   │  → /rw/active/task-001/meta.json                        │
│   │  → /rw/active/task-001/steps/_index.jsonl               │
│   ▼                                                          │
│   ② SKILL BEGIN (agent 调用 skill_begin)                     │
│   │  skill_begin("web-dev")                                  │
│   │  → 内部: create_scope(skill=web-dev, parent=task-001)    │
│   │  → /rw/active/task-001/steps/0002_scope_web-dev/        │
│   │  → 返回 instance_id: "sk_xxx" (agent 可见)               │
│   ▼                                                          │
│   ③ EXECUTE                                                 │
│   │  Agent works via shell (novaic CLI + native commands)    │
│   │  Tool results → write_step → steps/NNNN_tool_*.json    │
│   │  Deeper skills → skill_begin with nested scope           │
│   ▼                                                          │
│   ④ SKILL END (agent 调用 skill_end, LIFO)                  │
│   │  skill_end("sk_xxx", report)                             │
│   │  → 内部: complete_child_scope(path, summary)             │
│   │  → write summary.md + update meta.json                   │
│   │  → 卸载 SKILL.md + 反注册工具                            │
│   │  → 记忆压缩 (Compactor)                                  │
│   ▼                                                          │
│   ⑤ CLOSE ROOT (Worker 自动，agent 不可见)                   │
│   │  Worker.on_task_end → scope_end("task-001")              │
│   │  → archive_root_scope: /rw/active/ → /ro/scopes/        │
│   │  → entire tree moves atomically                          │
│   │  → gem fusion check                                      │
│   └──────────────────────────────────────────────────────────│
│                                                              │
│   Agent 视角:                                                │
│     skill_begin → (工作) → skill_end                          │
│   Cortex 内部:                                               │
│     scope_create → (steps) → scope_end                       │
│     子 scope 嵌套，LIFO 关闭，原子归档                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.3 Step Index (`_index.jsonl`)

Each scope maintains a `steps/_index.jsonl` — lightweight metadata for every step:

```jsonl
{"seq":1,"type":"tool","id":"tc_search","tool":"web_search","status":"success","ts":1712345678,"file":"0001_tool_tc_search.json"}
{"seq":2,"type":"scope","id":"research","name":"Research sub-task","status":"completed","ts":1712345700,"file":"0002_scope_research/"}
{"seq":3,"type":"tool","id":"tc_write","tool":"code_write","status":"success","ts":1712345800,"file":"0003_tool_tc_write.json"}
```

**Tool step file (JSON):**

```json
{
  "seq": 1,
  "type": "tool",
  "call_id": "tc_search",
  "tool": "web_search",
  "status": "success",
  "started_at": 1712345678.0,
  "duration_ms": 1420,
  "result": { "hits": 3, "items": ["..."] },
  "artifacts": [
    { "type": "screenshot", "ref": "fs://users/{uid}/attachments/...", "size_bytes": 245000 }
  ]
}
```

**Large binary outputs** are NOT inlined. The step JSON holds a reference URL pointing to `attachments/` (managed by File Service).

### 8.4 Flat Scope Index (`/ro/scopes/_index.jsonl`)

When a root scope archives, ALL scopes in the tree get appended to the flat index for quick lookup:

```jsonl
{"scope_id":"task-001","path":"/ro/scopes/task-001/","name":"Deploy fix","depth":0,"ts":1712345678,"children":["research"]}
{"scope_id":"research","path":"/ro/scopes/task-001/steps/0002_scope_research/","name":"Research","depth":1,"parent":"task-001","ts":1712345700}
```

This index enables:
- **Recall**: scan all scopes for fuzzy memory injection without tree traversal
- **Direct lookup**: find any scope by ID regardless of nesting depth
- **Gem fusion**: count and select root-level scopes (depth=0)

---

## 9. Configuration Schema

```json
// /ro/config/engine.json
{
  "context_window": 200000,
  "compact_threshold": 0.70,
  "emergency_threshold": 0.95,

  "micro_max_tool_output_chars": 500,
  "micro_preserve_recent": 3,

  "auto_summary_max_tokens": 20000,

  "gem_fusion_enabled": true,
  "gem_fusion_merge_factor": 5,
  "gem_fusion_max_level": 10,

  "fuzzy_memory_token_budget": 4000,
  "max_skill_depth": 4,
  "max_scope_depth": 4,

  "sandbox_timeout_default": 30,
  "sandbox_timeout_max": 300,
  "sandbox_disposable": true,
  "sandbox_isolation": "process",

  "capability_token_ttl_seconds": 1800,
  "capability_token_algorithm": "HS256",
  "cortex_api_url": "http://cortex:19996"
}
```

---

## 10. Integration Points

### 10.1 Cortex 作为 Agent 唯一 API 入口

Cortex 独立部署在 :19996，是 **Agent 与外部世界交互的唯一入口**。Sandbox CLI 只认 Cortex，Cortex 根据请求类型自处理或代理转发。

**调用方：**

| 调用方 | 用途 | 认证方式 |
|--------|------|---------|
| **Task Worker** | 3 个 agent tool: shell, skill_begin, skill_end | Capability JWT |
| **Task Worker (内部)** | scope 自动管理 + JWT 签发: `/v1/scope/*`, `/v1/token` | 服务间信任 |
| **Sandbox CLI** | `novaic *` — 认知/业务/设备/MCP 全部命令 | `$NOVAIC_TOKEN` (Capability JWT) |

### 10.2 Task Worker → Cortex（3 tool handler + 自动 scope）

Worker 只处理 3 个 agent tool call，scope 由 Worker 自动管理：

```python
# Agent 的 3 个 tool
async def handle_tool_execute(tool_name, args, ctx):
    token = ctx["capability_token"]
    headers = {"Authorization": f"Bearer {token}"}

    if tool_name == "shell":
        resp = await httpx.post(f"{CORTEX_URL}/v1/shell", json=args, headers=headers)
    elif tool_name == "skill_begin":
        resp = await httpx.post(f"{CORTEX_URL}/v1/skill/begin", json=args, headers=headers)
        # resp.instance_id 注入 agent context
    elif tool_name == "skill_end":
        resp = await httpx.post(f"{CORTEX_URL}/v1/skill/end", json=args, headers=headers)
    else:
        raise UnknownToolError(tool_name)
    return resp.json()

# Scope 自动管理（agent 不可见）
async def on_task_start(ctx):
    scope = await cortex_internal.scope_create("root", ctx["token"])
    ctx["root_scope_id"] = scope.id

async def on_task_end(ctx):
    await cortex_internal.scope_end(ctx["root_scope_id"], "task completed", ctx["token"])
```

### 10.3 Sandbox CLI → Cortex → (自处理 | 代理 Gateway)

```bash
# 认知操作: novaic CLI → Cortex → 直接处理
novaic read /ro/scopes/task-001/summary.md
  → GET http://cortex:19996/v1/read?path=...
  → Cortex: Workspace.read() → 返回

# 业务操作: novaic CLI → Cortex → 代理转发到 Gateway
novaic chat "找到了问题"
  → POST http://cortex:19996/v1/proxy/chat
  → Cortex: 验证 JWT → 提取 user_id/agent_id
  → Cortex: POST http://gateway:19999/internal/.../chat (服务间信任)
  → Gateway: 创建 AGENT_REPLY → Entangled → 推送前端

# 设备操作: novaic CLI → Cortex → 代理转发到 Gateway → vmcontrol
novaic browser navigate https://example.com
  → POST http://cortex:19996/v1/proxy/browser
  → Cortex → Gateway /internal/.../vm/browser → vmcontrol
```

### 10.4 JWT 双轨制

```
Gateway (:19999)                    Cortex (:19996)
  签发: 用户 JWT                      签发: Capability JWT
  密钥: JWT_SECRET                   密钥: CORTEX_JWT_SECRET (独立)
  claims: user_id, role              claims: user_id, agent_id,
  exp: 7 天                                  scope_id, permissions
  用途: /api/* 用户请求               exp: 30 分钟
  验证方: Gateway                    用途: /v1/* 全部 Cortex API
                                     验证方: Cortex

Cortex → Gateway 代理转发: 服务间信任 (内部 API key / mTLS)，不传递 Capability JWT
```

### 10.5 Protocols (Host provides)

```python
@runtime_checkable
class Summarizer(Protocol):
    async def summarize(self, text: str, max_tokens: int = 2000) -> str: ...

@runtime_checkable
class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...
    def count_messages(self, messages: list) -> int: ...
```

### 10.6 Event Hooks (Optional)

```python
class CortexHooks:
    on_scope_created:  list[Callable]  = []  # (scope_id, meta)
    on_scope_archived: list[Callable]  = []  # (scope_id, summary, archive_path)
    on_fusion:         list[Callable]  = []  # (fused_scope_id, children_ids)
    on_skill_loaded:   list[Callable]  = []  # (skill_name)
```

---

## 11. Security Model

| Rule | Enforcement | Layer |
|---|---|---|
| Agent cannot write `/ro/` | `Workspace._validate_write()` raises `PermissionError` | Workspace |
| Agent cannot escape workspace | S3 key prefix scoped to `agents/{agent_id}/` | CortexStore |
| Sandbox 一次性执行 | 每次 `exec()` 创建全新 temp dir，无跨调用缓存，执行完立即 `rm -rf` | Sandbox |
| Sandbox 无密钥 | 签名密钥仅在 Cortex Runtime 进程，沙箱内只有短期 JWT | Sandbox + JWT |
| Capability Token 短期有效 | JWT `exp` = scope 开始 + 30min，过期自动失效 | JWT |
| Capability Token 最小权限 | JWT `permissions` 数组限定可调用的 Cortex API (含代理) | JWT + Cortex |
| Capability Token 多用户隔离 | JWT `user_id` + `agent_id` 确保资源隔离 | JWT + Cortex |
| Sandbox 只认 Cortex | `$NOVAIC_API` 仅指向 Cortex，不暴露 Gateway/vmcontrol 地址 | Sandbox 网络隔离 |
| Shell timeout enforced | `asyncio.wait_for(timeout)` + `proc.kill()` | Sandbox |
| Scope archive & fusion | `archive_root_scope()` moves to `/ro/`. Gem fusion writes `/ro/scopes/__fused__/` via store | Workspace + Compactor |
| Config immutable to agent | Lives in `/ro/config/`, not writable by agent tools | ACL |
| Tool definitions immutable | Lives in `/ro/config/tools/`, system-managed | ACL |

**Sandbox 安全边界演进:**

```
Phase 1 (当前):  process isolation — subprocess + temp dir + env vars
Phase 2:         namespace isolation — nsjail (Linux namespaces + seccomp filter)
Phase 3:         kernel isolation — Firecracker microVM / gVisor
```

---

## 12. Observability

### Metrics

```python
@dataclass
class CortexMetrics:
    scopes_created: int = 0
    scopes_archived: int = 0
    total_fusions: int = 0
    max_fusion_level: int = 0
    shell_executions: int = 0
    shell_timeouts: int = 0
    total_files_read: int = 0
    total_files_written: int = 0
    recall_generations: int = 0
    total_tokens_saved: int = 0
```

### Structured Logging

```
[CORTEX] scope.created    scope_id=abc123 skill=web-dev parent=task-001
[CORTEX] scope.archived   scope_id=abc123 summary_len=… steps=… duration_s=…
[CORTEX] fusion.triggered level=1 children=5
[CORTEX] sandbox.exec     cmd="grep -r JWT" exit_code=0 duration_ms=…
[CORTEX] recall.generated sources=3 tokens=2450
[CORTEX] tools.loaded     count=5 skills=["web-dev"]
```

---

## 13. V2 → Cortex Migration Map

| # | V2 Component | V2 LOC | Cortex Replacement | Cortex LOC |
|---|---|---|---|---|
| 1 | ContextEngine (engine.py) | 542 | `Cortex` (runtime.py) | ~80 |
| 2 | ScopeRecord (types.py) | 270 | `meta.json` files | 0 |
| 3 | `ScopeSession` (scope_session.py) | 405 | Directory lifecycle | 0 |
| 4 | `SkillStack` (stack.py) | ~200 | Tree-nested scopes | 0 |
| 5 | `CheckpointManager` (checkpoint.py) | ~200 | Deleted (files = checkpoints) | 0 |
| 6 | `ScopeFuser` (fuser.py) | 447 | Part of `Compactor` | ~50 |
| 7 | `RecallSkill` (recall.py) | 511 | `read()` + `shell(grep)` | 0 |
| 8 | `SkillToolRouter` (tool_router.py) | 431 | File-based tool schemas | ~30 |
| 9 | HookRegistry (hooks.py) | ~100 | Optional `CortexHooks` | ~20 |
| 10 | CompactConfig (config.py) | ~80 | `engine.json` file | 0 |
| 11 | `SQLiteStore` (sqlite_store.py) | ~500 | `CortexStore` | ~150 |
| 12 | `InMemoryScopeStore` (defaults.py) | ~300 | `LocalFileStore` | ~40 |
| 13 | `SkillRegistry` (registry.py) | 203 | `_index.md` auto-gen | ~20 |
| 14 | `FileSystemSkillStore` (fs_store.py) | 429 | S3 + `/ro/skills/` | 0 |
| 15 | `SkillPromptBuilder` (prompt.py) | 210 | Part of `Recall` | 0 |
| 16 | prepare_messages (prepare.py) | ~300 | `Recall.generate()` | ~80 |
| 17 | `Blob/Checkpoint` (blob.py) | 400 | S3 is the checkpoint | 0 |
| | **TOTAL** | **~5,643** | | **~700** |

> **88% code reduction.** 18 files → 6 files.

---

## 14. Package Structure

```
novaic-cortex/
├── pyproject.toml
├── main_cortex.py               # ★ HTTP 服务入口 (FastAPI, :19996)
├── novaic_cortex/
│   ├── __init__.py              # exports: Cortex, CortexStore, LocalFileStore
│   ├── store.py                 # CortexStore (ABC) + LocalFileStore + MemoryStore
│   ├── workspace.py             # Workspace (/ro + /rw ACL, tree scopes)
│   ├── sandbox.py               # Sandbox (disposable shell execution)
│   ├── compactor.py             # Compactor (archival pipeline + gem fusion)
│   ├── recall.py                # Recall (fuzzy memory + skill directory injection)
│   ├── runtime.py               # Cortex (façade + proxy + tool schema loading)
│   ├── api.py                   # ★ FastAPI routes (/v1/read, write, shell, proxy/*, ...)
│   ├── proxy.py                 # ★ 业务代理 (Gateway 转发 + 设备 + MCP)
│   ├── auth.py                  # ★ Capability JWT 签发 + 验证
│   └── cli.py                   # ★ novaic CLI 脚本 (认知+业务+设备+MCP, 预装 Sandbox)
│
├── tests/
│   ├── test_store.py
│   ├── test_workspace.py
│   ├── test_sandbox.py
│   ├── test_compactor.py
│   ├── test_recall.py
│   ├── test_runtime.py
│   ├── test_proxy.py            # ★ 代理转发测试
│   └── test_api.py              # ★ HTTP API 集成测试
│
└── README.md
```

---

## 15. Design Decisions FAQ

### Why "everything is a file"?

```
Cortex: State IS the filesystem
    → ls /ro/scopes/task-001/steps/ tells you the execution timeline
    → The tree structure IS the scope hierarchy
    → Tool definitions ARE files — add a JSON, agent gains a capability
    → No code needed to understand state — just browse files
```

### Why scope is a step?

```
Before: steps/ has tool results, scopes/ has child scopes — two concepts
After:  steps/ is the ONLY timeline — tools are files, scopes are directories

Why? Because a child scope IS an execution step. It occupies a position
in the parent's timeline: "at step 2, I delegated research to a child scope".

ls steps/ sorted = complete chronological execution history.
```

### Why 3 files per scope (meta + summary + steps)?

```
meta.json   = 身份 (who): name, skill, phase, timestamps
summary.md  = 结果 (what): compacted summary for memory
steps/      = 过程 (how): chronological execution timeline

Removed:
  outcome.json   → derived from steps/_index.jsonl (redundant)
  messages.jsonl  → conversation lives in Gateway DB (redundant)
  scratch/        → use /rw/scratch/ for global notes (unnecessary per-scope)
```

### Why tool definitions as files?

```
Before: tool_schemas.py hardcodes JSON schemas
After:  /ro/config/tools/*.json — one file per tool

Why?
  1. Skills can bring their own tools (tools/ inside skill dir)
  2. Dynamic registration — add/remove tools without code deploy
  3. Agent can read its own capabilities (self-awareness)
  4. Consistent with "everything is a file"
```

### Why LIFO for scope nesting?

```
LIFO (last-in, first-out) means children close before parents.
This enables atomic archival:
  1. All children are already "archived" (summary.md written)
  2. One move_prefix on the root moves the ENTIRE tree to /ro/
  3. No dangling references, no partial archives
```

---

## 16. Competitive Analysis

| Capability | Claude Code | Cursor | NovAIC Cortex |
|---|---|---|---|
| Context compression | Single LLM summary | Token truncation | **3-level**: micro → scope → gem fusion |
| Memory granularity | Per-session | Per-session | **Per-scope** (fine-grained) |
| Memory persistence | ❌ | ❌ | ✅ S3 cross-session |
| Memory search | ❌ | ❌ | ✅ `shell(grep)` over tree |
| Progressive recall | ❌ | ❌ | ✅ Index → summary → steps → raw |
| Nested scopes | ❌ | ❌ | ✅ Tree in steps/, LIFO, depth=4 |
| Gem Fusion | ❌ | ❌ | ✅ N-ary carry cascade |
| Skill discovery | ✅ SKILL.md scan | ✅ Rules | ✅ `/ro/skills/` + auto-index |
| Skill progressive load | ✅ Compact → full | ❌ | ✅ 3-layer (meta → body → refs) |
| Skill-carried tools | ❌ | ❌ | ✅ `/ro/skills/{name}/tools/` |
| Dynamic tool registration | ❌ | ❌ | ✅ File-based tool definitions |
| Checkpoint/restore | ❌ | ❌ | ✅ S3 = checkpoint |
| Multi-agent | ❌ | ❌ | ✅ Per-agent S3 prefix |

---

> **Summary**: NovAIC Cortex replaces 18 files (~5,643 LOC) with 6 files (~700 LOC) — an **88% code reduction**. The core insight is **"filesystem is the API"**: state machines become directories, data structures become files, scope hierarchy IS the directory tree. A scope is three things: identity (meta.json), result (summary.md), and process (steps/). Tools and child scopes interleave naturally in a single chronological timeline. Tool definitions are files, enabling dynamic capability management and skill-carried tools.
