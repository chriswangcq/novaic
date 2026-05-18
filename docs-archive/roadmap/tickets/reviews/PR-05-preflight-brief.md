# PR-05 作业前置调研简报 — 给小弟

> 收件人：负责下一张工单 PR-05 的同学
> 作者：Reviewer
> 日期：见 commit
>
> **不要读完就开干。先交调研报告再动手。**

---

## 0. 背景（你得先知道你在做什么）

PR-01..PR-04 都是**新建骨架 + CI 规则**，不改现有业务代码，所以"按 ticket 勾 checklist"就能完成。

PR-05 不一样：**这是你第一次改现有代码**。而且要改的是**所有服务都在调的底层 HTTP 客户端**。改错一行，4 个仓、9 个文件可能全崩。

所以规则变了：**在你写一行代码之前，先交一份调研报告**。

---

## 1. Pre-flight 调研报告（交付前必读）

### 1.1 任务格式

在开 PR 前，先发一段消息（或写一个 `docs/roadmap/tickets/reviews/PR-05-preflight-<你的名字>.md`），包含以下四个部分。**每一项都要有具体证据（文件路径 + 行号 + 命令）**，不要空谈。

### 1.2 四个必答问题

#### 问题 1：`internal_client` 真实 surface 长什么样？

**Ticket 里的措辞是**：
> `clients.py` 中 `internal_client(...)` 新增 `service_name: str` 必填参数

**实际情况**：`novaic-common/common/http/clients.py` 里**不止一个** `internal_client`。请你列出：

- 有几个 factory 函数？（提示：sync / async / internal / external 的组合）
- `internal_client` 这个名字是**独立函数**还是**alias**？
- 如果是 alias，修改底层函数 vs 修改 alias 会有什么差别？
- 现有签名是 `**kwargs: Any` 还是有明确参数列表？新参 `service_name` 要放哪？是否破坏现有 call site？

**调研命令**：

```bash
cat novaic-common/common/http/clients.py
rg -n "^def (internal|external|create_internal|create_external)" novaic-common/common/http/clients.py
```

**你的回答里要有一张"函数 → 是否需要加 service_name"的表**。

#### 问题 2：所有 call site 在哪？分别该传什么 `service_name`？

**调研命令**（抄 ticket 里的）：

```bash
rg -n "internal_(sync_|async_)?client\(" novaic-*/ --type py > /tmp/callsites.txt
cat /tmp/callsites.txt
```

**要求你给出一张表**，每行一个 call site：

| 文件 | 行号 | 当前调用 | 应传 `service_name` | 备注 |
| --- | --- | --- | --- | --- |
| `novaic-agent-runtime/task_queue/client.py` | ??? | `internal_sync_client(base_url=...)` | `"runtime"` 或 `"queue"`？ | 同一进程混用? |
| ... | ... | ... | ... | ... |

**关键点**：`service_name` 是个**强契约**字段，以后所有日志和监控都要 join 它。用错名字比没传更坏。参考 ticket 备注第 99 行建议的 8 个名字：`business / cortex / runtime / gateway / device / scheduler / health / subscriber`。  
如果一个进程内**出现了多个名字都合理**（比如 runtime 同时干 task_queue 和 queue_service），说明你得想清楚命名边界——这个问题要在报告里单独说明你的选择和理由。

#### 问题 3：现有"手工注入 X-Internal-Key" 的代码在哪？PR-05 要不要一起收敛？

**调研命令**：

```bash
rg -n "X-Internal-Key|X_INTERNAL_KEY|NOVAIC_INTERNAL_KEY" novaic-*/ --type py
```

**要求你回答**：
- 哪些文件目前是**手动写** `headers={"X-Internal-Key": ...}` 的？
- 如果 PR-05 让 `internal_client` 自动注入，那这些手工注入点该不该**同一个 PR 里**删掉？
- 如果不该删（比如这些点本身就不是通过 `internal_client` 走的），理由是什么？
- 是否存在"**既用 internal_client 又手工注入**"的双重注入点？这种要怎么处理？

**这个问题故意没有标准答案。我想看你怎么思考。**

#### 问题 4：PR-05 合并后，PR-04 的 allowlist 能删哪几行？

PR-04 的 `scripts/ci/lint_httpx.sh` 里有一个 TRANSITIONAL allowlist，15 个文件。

**要求你**：
- 列出哪些文件在 PR-05 里会被改造成"走 `internal_client`"，因此可以从 allowlist 里删除
- 列出哪些**不是内部调用**（比如调 LLM provider、调外部云服务），该**永久留在 allowlist** 里（因为外部调用本来就不该走 `internal_client`）
- 列出哪些是"**属于其他 PR 的范围**"，PR-05 不要动

**输出形式**：在你的调研报告里，直接把 `lint_httpx.sh` 的 allowlist 块贴一份，每一行后面加注释：

```
'novaic-business/business/provider_client.py'    # KEEP - external LLM provider, not internal
'novaic-agent-runtime/task_queue/workers/health_worker_sync.py'  # DELETE in PR-05 (migrate to internal_client)
'novaic-gateway/gateway/api/app_client.py'       # DEFER to PR-?? (out of PR-05 scope)
```

---

## 2. 实施前的几个硬约束

等你的调研报告通过之后才能动手。动手时注意：

### 2.1 `service_name` 必填 + fail-fast
Ticket 已经写清楚："为空串或 None → `raise ValueError`"。  
**不要做"默认 service_name='unknown'"这种好心妥协**——那会让未来所有日志 join 都变垃圾。

### 2.2 `NOVAIC_INTERNAL_KEY` 未设置不硬拒
Ticket 明确说"log WARN 后继续"。理由：
- 硬拒会让本地开发无法启动
- 服务端的 auth middleware 本来就会 401，有独立的防线
- 但本地 log 里要**看得见**"我没带 key"这件事

### 2.3 一次到位，不搞灰度 overload
Ticket 第 56 行明确："**不**保留 `service_name` 可选 overload"。  
不要写成 `def internal_client(service_name: str = None)` 然后 `if service_name is None: warn(...)`——那叫拖延，不叫灰度。一次性都改完。

### 2.4 PR 粒度
**本 PR 只做**：
1. 升级 `clients.py` 的 factory
2. 迁移**内部调用**的 call site（内部指调 business/cortex/queue/entangled/gateway 这些自己家服务）
3. 从 `lint_httpx.sh` allowlist 里删对应行

**本 PR 不做**：
- 服务端消费 `X-Internal-Service` header（那是 PR-06）
- `HealthWorkerSync` 的业务逻辑重构（那是 PR-12）
- 任何外部 provider 客户端（LLM/OSS/Redis 不改）

如果你发现某个 call site "顺手改一下更干净"——**忍住，开另一张 PR**。

### 2.5 单测必须有
Ticket §测试 Checklist 三条，一条都不能少：
- [ ] 无 `service_name` → `ValueError`
- [ ] 注入 `X-Internal-Service` 头
- [ ] `NOVAIC_INTERNAL_KEY` 未设置 → WARN 但不 raise

**不会写的话**，在调研报告里说你打算用什么 mock 方式（`httpx.MockTransport` vs monkey patch vs ...），我提前反馈。

### 2.6 提交粒度建议
- 一个 commit: `refactor(common): internal_client requires service_name (PR-05)` —— 只改 `clients.py` + tests
- 每个仓单独一个 commit: `refactor(<service>): adopt internal_client(service_name=...) (PR-05)`
- **不要**把 5 个仓的改动合成一个巨型 commit，那样 revert 不了

然后每个 submodule bump 一个主仓 commit。

---

## 3. 交付物（你交来的时候我会对着这个看）

### 3.1 调研报告（写代码前）

一份文件或消息，包含：
1. 问题 1 的答案（真实 surface 表）
2. 问题 2 的答案（9 行 call site 的迁移表）
3. 问题 3 的答案（手工注入收敛方案）
4. 问题 4 的答案（allowlist 去留标注）
5. **你不确定的地方**列一节 `## 存疑`——这一节我会重点看

### 3.2 代码（调研通过后）

按 ticket §实施 Checklist 做，加我上面的硬约束。

### 3.3 验收（PR 描述里）

贴 ticket §验收命令的输出：

```bash
rg "internal_client\(" novaic-*/ | rg -v "service_name="
# 预期：空（除了 clients.py 本体定义 / tests）
```

和 `pytest tests/test_internal_client.py` 输出。

---

## 4. 我期望的工作节奏

| 阶段 | 你需要做 | 我会做 |
| --- | --- | --- |
| T0 | 交调研报告 | review 调研、提问、批准或打回 |
| T1 | 按批准方案写代码 + 单测 | — |
| T2 | 本地跑验收命令 + push | — |
| T3 | 提 PR（描述粘 ticket 路径 + 验收输出） | review 代码、合并 |
| T4 | bump 主仓 submodule pointer + push | final check |

**预估时间**：ticket 写 0.5 d，但**对你**这是第一次跨仓改现有代码，**加上调研，1.5 d 完成算合格**。3 天以上请主动吱声。

---

## 5. 最后一句

PR-01 你犯过"ticket 说 `novaic_common` 我就照着建 `novaic_common/` 目录"的错，之后改正了。PR-05 ticket 里**同样有类似的简化表达**（比如 §实施 第 1 条写"`internal_client(...)` 新增 `service_name` 必填参数"——好像只有一个函数一样）。

**不要再照搬 ticket 的字面描述**。Ticket 是方向，调研才是真相。  
发现 ticket 和代码对不上 → **在调研报告里明确指出**，这算加分不算给我找麻烦。

开干前三遍：**先调研 → 写报告 → 等批准**。
