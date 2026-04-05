# OSS 与平台存储统一规划

> **核心决策：**
> 1. **Scope is a step** — 子 scope 嵌套在父 scope 的 `steps/` 里，是一种特殊的 step（目录而非文件）。
> 2. **Scope 三要素** — `meta.json`（身份）、`summary.md`（结果）、`steps/`（过程）。无 outcome/messages/scratch。
> 3. `attachments/` 是 user 下唯一与 `agents/` 并列的非 Cortex 目录。
> 4. **Tool definitions as files** — `/ro/config/tools/` 存放 tool schemas，技能可携带自己的 tools。

---

## 1. 设计原则

| # | 原则 | 推论 |
|---|------|------|
| 1 | **user 是隔离边界** | 所有数据在 `users/{user_id}/`；`user_id` 只从鉴权注入 |
| 2 | **scope 是执行单元** | 每次 tool/skill 调用在一个 scope 内 |
| 3 | **scope 是 step 的一种** | 子 scope 嵌套在父 scope 的 `steps/` 里，与 tool step 交织 |
| 4 | **时序 = 序号** | `steps/` 内用单调递增序号文件名记录，`ls` 排序即时间线 |
| 5 | **LIFO 保证原子归档** | 子 scope 先关闭；根 scope 关闭时 `move_prefix` 搬迁整棵树 |
| 6 | **Cortex 管认知态，File Service 管二进制** | 结构化 JSON → steps；大 blob → `attachments/` |

---

## 2. 目标目录树

### 2.1 完整布局（单桶 `novaic-s3-bucket`）

```text
users/{user_id}/
│
├── agents/{agent_id}/                           ← Cortex 工作区
│   │
│   ├── ro/                                      ← 不可变层（Cortex 维护）
│   │   ├── config/
│   │   │   ├── engine.json
│   │   │   ├── personality.md
│   │   │   ├── constraints.md
│   │   │   └── tools/                           ← tool definitions（文件化）
│   │   │       ├── _index.json                  ← 当前生效 tool 列表
│   │   │       ├── read.json
│   │   │       ├── write.json
│   │   │       ├── shell.json
│   │   │       └── scope_end.json
│   │   ├── skills/{skill_name}/
│   │   │   ├── SKILL.md
│   │   │   ├── meta.json
│   │   │   ├── tools/                           ← 技能携带的 tools
│   │   │   │   └── browser.json
│   │   │   └── examples/
│   │   ├── knowledge/
│   │   │   └── preferences.md
│   │   └── scopes/                              ← 归档 scope（树形结构）
│   │       ├── _index.jsonl                     ← ★ 平铺索引 (scope_id → path)
│   │       ├── __fused__/                       ← gem fusion 产物
│   │       │   └── fuse_L1_001/
│   │       │       ├── meta.json
│   │       │       └── summary.md
│   │       └── task-001/                        ← 根 scope
│   │           ├── meta.json                    ← 身份
│   │           ├── summary.md                   ← 结果
│   │           └── steps/                       ← 过程（tool 文件 + scope 目录 交织）
│   │               ├── _index.jsonl
│   │               ├── 0001_tool_search.json
│   │               ├── 0002_scope_research/     ← ★ 子 scope = step 目录
│   │               │   ├── meta.json
│   │               │   ├── summary.md
│   │               │   └── steps/
│   │               │       ├── _index.jsonl
│   │               │       ├── 0001_tool_fetch.json
│   │               │       └── 0002_scope_deep/ ← 继续嵌套
│   │               │           ├── meta.json
│   │               │           ├── summary.md
│   │               │           └── steps/
│   │               └── 0003_tool_write.json
│   │
│   └── rw/                                      ← 可变层（Agent 自由空间）
│       ├── scratch/                             ← 全局草稿
│       └── active/
│           └── task-001/                        ← 执行中根 scope
│               ├── meta.json
│               └── steps/                       ← 实时追加
│                   ├── _index.jsonl
│                   ├── 0001_tool_search.json
│                   └── 0002_scope_research/     ← 子 scope（可能已 archived）
│                       ├── meta.json
│                       ├── summary.md           ← 子 scope 关闭后写入
│                       └── steps/
│
└── attachments/                                 ← File Service（平台二进制）
    └── {category}/{ref_id}/...
```

### 2.2 `steps/` 时序保证

| 机制 | 说明 |
|------|------|
| **序号前缀** | 文件名 `{seq:04d}_tool_{id}.json` 或 `{seq:04d}_scope_{id}/`，seq 从 1 单调递增 |
| **自动分配** | `write_step()` / `create_scope()` 统计现有 step 数 + 1 得到下一个 seq |
| **顺序安全** | scope 内执行是串行的（一个 tool 完成才下一个）；不会并发写同一 scope |
| **type 区分** | 文件 = tool step，目录 = scope step |
| **归档不变** | `move_prefix` 整棵搬迁；排序顺序保持不变 |

### 2.3 step 文件格式

**Tool step (`0001_tool_search.json` — 文件):**

```json
{
  "seq": 1,
  "type": "tool",
  "call_id": "tc_001",
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

**Scope step (`0002_scope_research/` — 目录):**

```
0002_scope_research/
├── meta.json      ← {name, skill, start_time, ended_at, phase}
├── summary.md     ← 子 scope 关闭时写入
└── steps/
    ├── _index.jsonl
    └── ...         ← 递归同样结构
```

**`_index.jsonl` (统一记录 tool + scope):**

```jsonl
{"seq":1,"type":"tool","id":"tc_001","tool":"web_search","status":"success","ts":1712345678,"file":"0001_tool_tc_001.json"}
{"seq":2,"type":"scope","id":"research","name":"Research sub-task","status":"completed","ts":1712345700,"file":"0002_scope_research/"}
{"seq":3,"type":"tool","id":"tc_002","tool":"code_write","status":"success","ts":1712345800,"file":"0003_tool_tc_002.json"}
```

| 字段 | 说明 |
|------|------|
| `seq` | 自动分配的序号，即该事件在 scope 内的执行位置 |
| `type` | `"tool"` 或 `"scope"` |
| `file` | 文件名（tool → `.json`，scope → `目录/`） |
| `result` | (仅 tool) 结构化小输出（通常 < 64 KB），内联在 step JSON 中 |
| `artifacts` | (仅 tool) 大二进制引用 → `attachments/` 的 File Service URL |
| `name` | (仅 scope) 子 scope 的名称 |

---

## 3. Scope 三要素

每个 scope（无论根/子）结构完全一致，只有三样东西：

```
scope/
├── meta.json      ← 身份 (who)
├── summary.md     ← 结果 (what)
└── steps/         ← 过程 (how)
```

**去掉的东西及原因：**

| 去掉 | 原因 |
|------|------|
| `outcome.json` | 从 `steps/_index.jsonl` 派生，完全冗余 |
| `messages.jsonl` | 对话消息在 Gateway `chat_messages` 表，Cortex 不再冗余存储 |
| `scratch/` | Agent 有全局 `/rw/scratch/`，per-scope scratch 增加复杂度无收益 |

---

## 4. 树形 Scope 归档流程

### 4.1 LIFO 约束

子 scope 必须先于父 scope 关闭。这保证了：
- 关闭子 scope 时：就地写 `summary.md`，标记 `meta.phase="archived"`，**不 move**
- 关闭根 scope 时：一次 `move_prefix` 搬整棵树，所有子 scope 跟着走

### 4.2 归档步骤

```
complete_child_scope(scope_path, summary):
  1. Write summary.md → scope_path/summary.md
  2. Update meta.json → phase: "archived", ended_at: now()
  — 留在原地（/rw/ 下父 scope 的 steps/ 里）

archive_root_scope(scope_id, summary):
  1. Write summary.md → /rw/active/{id}/summary.md
  2. Update meta.json → phase: "archived", ended_at: now()
  3. move_prefix /rw/active/{id}/ → /ro/scopes/{id}/
  4. Walk tree, append ALL scope entries to /ro/scopes/_index.jsonl
  5. Gem fusion check (root scopes only)
```

### 4.3 平铺索引 (`/ro/scopes/_index.jsonl`)

归档时遍历整棵树，将所有 scope（根 + 子）追加到平铺索引：

```jsonl
{"scope_id":"task-001","path":"/ro/scopes/task-001/","name":"Deploy fix","depth":0,"ts":1712345678}
{"scope_id":"research","path":"/ro/scopes/task-001/steps/0002_scope_research/","name":"Research","depth":1,"parent":"task-001","ts":1712345700}
{"scope_id":"deep","path":"/ro/scopes/task-001/steps/0002_scope_research/steps/0002_scope_deep/","name":"Deep dive","depth":2,"parent":"research","ts":1712345750}
```

用途：
- **Recall** 扫描索引注入 fuzzy memory（不需遍历树）
- **按 ID 查找** 任意深度的 scope
- **Gem fusion** 只选 `depth=0` 的根 scope

---

## 5. Tool Definitions 文件化

### 5.1 内置 tools

```
/ro/config/tools/
├── _index.json         ← ["read", "write", "shell", "scope_end"]
├── read.json
├── write.json
├── shell.json
└── scope_end.json
```

### 5.2 技能携带 tools

```
/ro/skills/web-dev/
├── SKILL.md
├── meta.json
└── tools/
    └── browser.json    ← 加载 web-dev 技能时自动注册
```

### 5.3 加载流程

```python
schemas = []
# 1. 扫描 /ro/config/tools/*.json
# 2. 扫描所有 active skill 的 tools/*.json
# 3. 合并去重 → 传给 LLM
```

---

## 6. attachments 为什么不在 scope 内

- 平台级资源：用户上传的图片/文档，不属于某次 tool 调用
- 独立 URL 体系（`fs://`）、CDN、与 Cortex 无关的生命周期
- 多个 scope/agent 可能引用同一附件
- **结论：** `attachments/` 在 `users/{user_id}/` 下与 `agents/` 并列

---

## 7. 与现有仓库的映射

| 组件 | 仓库路径 | 角色 |
|------|-----------|------|
| Cortex workspace | `novaic-cortex/novaic_cortex/workspace.py` | 树形 scope 管理 + `write_step` |
| Cortex sandbox | `novaic-cortex/novaic_cortex/sandbox.py` | 一次性执行环境 + JWT 注入 |
| Cortex HTTP 服务 | `novaic-cortex/main_cortex.py` + `novaic_cortex/api.py`（待建） | 独立 HTTP :19996，Agent 唯一入口 |
| Cortex Proxy | `novaic-cortex/novaic_cortex/proxy.py`（待建） | 业务代理转发到 Gateway |
| Cortex Auth | `novaic-cortex/novaic_cortex/auth.py`（待建） | Capability JWT 自签自验 |
| Cortex CLI | `novaic-cortex/novaic_cortex/cli.py`（待建） | 完整 CLI：认知+业务+设备+MCP |
| Cortex S3Store | `novaic-cortex/novaic_cortex/s3_store.py` | 管理 `users/{uid}/agents/` |
| OSS 工厂 | `novaic-cortex/novaic_cortex/aliyun_oss_s3.py` | 构建 S3Store |
| CortexBridge | `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` | Runtime ↔ Cortex 集成 |
| ~~Tool Router~~ | ~~`novaic-agent-runtime/.../tool_router.py`~~ | ~~不再需要，Worker 只有 4 个 tool handler~~ |
| ~~Gateway Cortex API~~ | ~~`novaic-gateway/gateway/api/cortex.py`~~ | ~~Cortex 已独立，Gateway 不含 Cortex 逻辑~~ |
| File Service | `novaic-storage-a/file_service/` | 管理 `attachments/` |
| TenantLayout（待建） | Gateway 或共享库 | `user_id` → prefix |
| ~~Tools Server~~ | ~~`novaic-tools-server/`~~ | ~~退役：Cortex 代理 + CLI 替代~~ |

---

## 8. 不建议的做法

- ~~独立 `scopes/` 和 `steps/` 目录~~ — 子 scope 是 step 的一种，不应分离
- ~~per-scope `messages.jsonl`~~ — Gateway 已有对话记录，冗余
- ~~per-scope `outcome.json`~~ — 从 `_index.jsonl` 派生，冗余
- ~~per-scope `scratch/`~~ — 全局 `/rw/scratch/` 足够
- ~~平铺 scope + parent_id 元数据链接~~ — 树形目录更直观，LIFO 保证原子归档
- ~~时间戳文件名~~ — 长、丑、潜在碰撞
- ~~大 blob 内联 step JSON~~ — 保持 scope 轻量
- ~~Agent 自拼 `user_id`~~ — 必须服务端鉴权注入
- ~~硬编码 tool schemas~~ — 应文件化，支持动态注册和技能携带
- ~~Sandbox blob cache 跨 exec 复用~~ — 已改为一次性执行，无跨调用状态

---

## 9. Sandbox 执行模型

### 9.1 一次性执行（Disposable Execution）

每次 `Sandbox.exec()` 是完全独立的生命周期：

```
① 创建全新 temp dir
② 从 Store 全量拉取 /ro + /rw（无缓存）
③ 注入 $NOVAIC_TOKEN (JWT)
④ 执行命令
⑤ Diff /rw → 回写变更
⑥ 销毁 temp dir — 无残留
```

**无跨调用状态：** 没有 blob cache、连接池、进程池。前一次执行不会泄漏给下一次。

### 9.2 极简 Tool 模型（Sandbox-first, 3 Tool）

**核心决策：LLM 只看到 3 个结构化 tool。Scope 对 agent 不可见。**

| 结构化 Tool | 用途 | 为什么不进 Sandbox |
|-------------|------|-------------------|
| `shell` | Sandbox 执行入口 | 它就是 Sandbox 的接口 |
| `skill_begin` | 开始技能 → 返回 instance_id | 改变 agent 运行状态 (prompt/tool list) |
| `skill_end` | 结束技能（凭 instance_id） | 触发记忆归档，改变运行状态 |

**Scope 对 agent 完全不可见：** 根 scope 由 Worker 自动管理，技能 scope 由 skill_begin/end 隐式管理。

**Skill 生命周期：**

```
skill_begin("web-dev")                    → 返回 instance_id: "sk_abc123"
  内部: 创建 scope + 加载 SKILL.md + 注册工具 + 推入 skill_stack

skill_end("sk_abc123", "JWT 问题已解决")
  → 校验: instance_id 存在 + LIFO 栈顶
  → 通过: 归档 scope + 记忆压缩 + 卸载 → { ok: true }
  → 失败: 技能保持活跃 → { ok: false, warning: "child skill must end first" }
```

**skill_end 校验失败不是异常**，而是正常工具结果返回 warning，LLM 据此修正行为。

其他所有操作在 `shell()` 内通过 `novaic` CLI 执行：

```bash
novaic chat "我找到了"              # 业务 → Cortex 代理 → Gateway
novaic search "JWT best practices"  # 业务 → Cortex 代理 → Gateway
novaic memory save key value        # 业务 → Cortex 代理 → Gateway
novaic browser navigate url         # 设备 → Cortex 代理 → Gateway → vmcontrol
novaic read /ro/scopes/task-001/... # 认知 → Cortex 直接处理
grep -rl "JWT" $RO/scopes/          # 原生 shell → 操作本地 $RO/$RW
```

### 9.3 Cortex CLI — Agent 的完整命令行

Sandbox 内预装 `novaic` CLI，`$NOVAIC_API` 指向 **Cortex :19996**（Agent 唯一 API 入口）。

**完整命令表：**

```
── 认知操作（Cortex 自处理）──
novaic read <path>                    novaic write <path> [content]
novaic ls <path>                      novaic recall
novaic tools

── 业务操作（Cortex → Gateway）──
novaic chat <message>                 novaic search <query>
novaic memory save/recall/delete/list novaic notebook write/read/list
novaic task create/complete

── 设备操作（Cortex → Gateway → vmcontrol）──
novaic browser navigate/content       novaic screenshot
novaic keyboard type                  novaic mouse click

── MCP ──
novaic mcp <tool_name> [args_json]
```

**关键约束：**
- `novaic *` → Cortex HTTP → 不触发 S3 同步（快，~100ms）
- 原生 shell 命令操作 `$RO/$RW` → 需要 S3 同步（慢，~1-5s）
- CLI 不持有签名密钥，只持有 JWT → 沙箱内无法伪造
- `$NOVAIC_API` 只指向 Cortex → Sandbox 不知道 Gateway 地址

### 9.4 Worker 极简化（3 tool handler + 自动 scope）

Worker 只处理 3 个 agent tool call，scope 由 Worker 自动管理：

```
Agent 的 3 个 tool:
  shell(command)                    → POST Cortex /v1/shell
  skill_begin(name)                 → POST Cortex /v1/skill/begin → 返回 instance_id
  skill_end(instance_id, report)    → POST Cortex /v1/skill/end

Worker 自动（agent 不可见）:
  on_task_start → POST Cortex /v1/scope/create (根 scope)
  on_task_end   → POST Cortex /v1/scope/end   (关闭根 scope)
```

**Tools Server 退役：** 路由不再需要（只有 3 个 tool），业务逻辑通过 Cortex 代理到 Gateway，MCP 通过 novaic mcp 调用。

### 9.5 Cortex HTTP API（独立服务 :19996 — Agent 唯一入口）

```
── Agent Tool API (Worker 调用) ──
POST /v1/shell                   → Sandbox.exec()
POST /v1/skill/begin             → 创建 scope + 加载 skill → 返回 instance_id
POST /v1/skill/end               → 归档 scope + 记忆压缩 + 卸载 skill

── 认知操作 (CLI 调用) ──
GET  /v1/read?path=              → Workspace.read()
POST /v1/write                   → Workspace.write()
GET  /v1/ls?path=                → Workspace.list_dir()
GET  /v1/skill/list              → list skills
GET  /v1/recall                  → Recall.generate()
GET  /v1/tools                   → load_tool_schemas()

── 内部 API (Worker 自动, agent 不可见) ──
POST /v1/scope/create            → 创建根 scope (任务开始)
POST /v1/scope/end               → 关闭根 scope (任务结束)
POST /v1/token                   → 签发 Capability JWT

── 业务代理（转发到 Gateway :19999）──
POST /v1/proxy/chat              → Gateway /internal/.../chat
POST /v1/proxy/search            → Gateway /internal/.../search
POST /v1/proxy/memory            → Gateway /internal/.../memory
POST /v1/proxy/notebook          → Gateway /internal/.../notebook
POST /v1/proxy/task              → Gateway /internal/.../tasks
POST /v1/proxy/browser           → Gateway → vmcontrol
POST /v1/proxy/screenshot        → Gateway → vmcontrol
POST /v1/proxy/keyboard          → Gateway → vmcontrol
POST /v1/proxy/mouse             → Gateway → vmcontrol
POST /v1/proxy/mcp               → MCP Client
```

所有端点 Capability JWT 鉴权。Scope 管理 API 仅限 Worker 内部调用（agent 不可见）。代理端点从 JWT claims 提取身份构造 Gateway 请求。

### 9.6 Capability Token (JWT)

```
签发时机: Scope 开始时，Worker 调 Cortex /v1/token
注入方式: $NOVAIC_TOKEN 环境变量
验证方: Cortex 自己（自签自验）

Claims:
  user_id     → 资源隔离
  agent_id    → agent 绑定
  scope_id    → scope 绑定
  permissions → 最小权限（可调用的 API 列表）
  exp         → scope 开始 + 30min（可配）

Cortex → Gateway 代理转发: 服务间信任 (内部 API key)，不传递 JWT
```

**多用户就绪：** JWT `user_id` claim 天然隔离不同用户的 agent。

### 9.7 分阶段隔离

| Phase | 技术 | 隔离级别 | 开销 | 适用 |
|------|------|---------|------|------|
| **1 (当前)** | tempfile + subprocess | 进程级 | ~10ms | 单用户/开发 |
| **2** | nsjail (namespaces + seccomp) | 命名空间 | ~50ms | 多用户生产 |
| **3** | Firecracker / gVisor | 内核级 | ~125ms | 强隔离生产 |

Phase 切换对上层透明：`Sandbox` 接口不变，仅内部 `_execute()` 实现替换。
