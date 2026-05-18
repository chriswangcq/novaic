# PR-05 调研报告 Review（给执行同学的批示）

> 被审对象：[`PR-05-preflight-antigravity.md`](PR-05-preflight-antigravity.md)
> 作者：Reviewer
> 日期：见 commit
>
> **结论先给：有条件批准。不能直接进 T1，需要补一版 v2 调研。下面所有"要改的地方"都列得很细，照着做就行。**

---

## 0. 先说你做得好的地方

不是套话。你这份报告有两处真实价值：

1. **Q1 surface 表**把"一个 `internal_client` 其实是 4 个 factory + 1 个 alias"讲清楚了，而且提出"不能只改 alias，要改包装层"——这是对的。
2. **"存疑点"那段是全篇最值钱的**。你独立发现了 ticket 里写的 `NOVAIC_INTERNAL_KEY` 这个环境变量**在现实代码里根本不存在**，并且主动在交付前提出来问，而不是硬写完代码再爆 401。这就是 reviewer 设计 "Pre-flight 调研"这一关的全部意义。后面我会告诉你这个问题的裁决答案。

**这两件事说明你的调研能力合格了。** 剩下的问题都是"范围意识"和"证据完整度"的问题，可以改。

---

## 1. 我核对你每一条结论的方式

你的报告不是"交完就完"——reviewer 会**逐条回到代码里验证**。我把这次的验证过程也贴给你，让你知道 reviewer 下次会怎么看你的报告。

### 1.1 核验 Q1（surface）— ✅ 你是对的

```bash
cat novaic-common/common/http/clients.py
# 看到 4 个 create_*、4 个 *_client 包装、1 行 alias —— 和你的表一致
```

### 1.2 核验 Q2（call site）— ⚠️ 方向对，但**范围漏了**

你列了 9 处 `internal_*client(` 的命中点。但 reviewer 会再问一步："这 9 处里，有几处是**直接命令式调用**？有几处是**写在类里**、需要类实例化的？"

```bash
grep -rn "^class " novaic-agent-runtime/task_queue/client.py
# 输出：TaskQueueClient / SagaClient / _BaseInternalApiClient / BusinessClient
# 说明 task_queue/client.py 里那 4 行 internal_client 调用，背后是 4 个"SDK 类"
# 它们真正起作用，要看"谁实例化这些类"

grep -rn "TaskQueueClient(\|SagaClient(" --type py
# novaic-agent-runtime/task_queue/workers/task_worker_sync.py:85-86
# novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py:78

grep -rn "EntangledServiceClient(" --type py
# novaic-business/business/internal/entity.py:68,106,122,149,171,192,210,228,249,268,287
# —— 11 处！全在 business
```

**所以 PR-05 的真实改动量不是 9 处，是 9 + 13 = 22 处**：
- 9 处是在 `clients.py` factory 直接调用的地方
- 13 处是实例化 SDK 类的地方（那些类的 `__init__` 如果新增 `service_name` 必填，调用方必须跟着传）

**你 v2 必须新增一张表**，格式如下：

| # | 文件 | 行号 | SDK 类 | 实例化代码 | 应传 `service_name` |
| --- | --- | --- | --- | --- | --- |
| 1 | `novaic-agent-runtime/task_queue/workers/task_worker_sync.py` | 85 | `TaskQueueClient` | `TaskQueueClient(self.queue_service_url, timeout=timeout)` | `"runtime-task"` |
| 2 | `novaic-agent-runtime/task_queue/workers/task_worker_sync.py` | 86 | `SagaClient` | `SagaClient(self.queue_service_url, timeout=timeout)` | `"runtime-task"` |
| 3 | `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` | 78 | `SagaClient` | `SagaClient(self.queue_service_url, timeout=self.timeout)` | `"runtime-scheduler"` |
| 4–14 | `novaic-business/business/internal/entity.py` | 68/106/122/149/171/192/210/228/249/268/287 | `EntangledServiceClient` | `EntangledServiceClient()` | `"business"` |

**你报告里还有一个微小的误判**：你在 Q2 的描述里说

> `task_queue/client.py` 里面 `TaskQueueClient`、`SagaClient` 等通用 SDK...

实际上它们**不是"跨服务通用 SDK"**——只有 runtime 自己内部实例化它们。所以 `service_name` 不是"依赖调用方传入"的未知数，就是 runtime 内部的两个确定值（`runtime-task` / `runtime-scheduler`）。

**唯一真正"跨服务"的 SDK 是 `EntangledServiceClient`**，它在 common 包里、被 business 实例化 11 次，那里才需要让调用方显式传 `service_name`。

这个区分很重要，关系到 `__init__` 参数的默认值策略：
- `TaskQueueClient.__init__(self, ..., service_name: str)` — 必填，没有默认值
- `SagaClient.__init__(self, ..., service_name: str)` — 必填，没有默认值
- `EntangledServiceClient.__init__(self, ..., service_name: str)` — 必填，没有默认值
- **三者都不要给默认值 `"unknown"` 这种兜底**。

### 1.3 核验 Q3（手工 Key 注入）— ✅ 一半对，但论证要重写

你说：

> `proxy.py` 使用 `urllib.request`，不在 PR-05 范围

```bash
head -20 novaic-cortex/novaic_cortex/proxy.py
# import urllib.request —— 你是对的
```

✅ 这个决策正确，理由也成立。

但是你紧接着说：

> **`task_queue/client.py` 和 `cortex_bridge.py`**：...PR-05 要求 `internal_client` 自动从环境变量 `NOVAIC_INTERNAL_KEY` 中读取并注入该 header...因此**强烈建议在同一个 PR 里删掉这些文件中的手工 header 注入代码**

**这个结论的前提是错的**。见 §2 的裁决。

### 1.4 核验 Q4（allowlist）— ✅ 正确

你的 10 DELETE / 4 KEEP 分类我 spot-check 了几个，都对：

```bash
head -5 novaic-cortex/novaic_cortex/file_resolver.py    # 下载外部 URL，非内部调用 → KEEP 对
head -5 novaic-llm-factory/factory/providers.py          # 调 OpenAI/Anthropic → KEEP 对
head -5 novaic-business/business/device_client.py        # 调 novaic-device，是内部 → DELETE 对
```

**小改进**：每个 KEEP 条目后面再多加一句"永久保留的理由"（让后续 reviewer 不用每次都 spot-check）。

---

## 2. 关于你那个"存疑"——我的裁决

你问：
> 如果我们删除手工注入，发出去的 header 值会变成 `NOVAIC_INTERNAL_KEY` 的值；但服务端目前是用 `QUEUE_SERVICE_INTERNAL_KEY` 和 `CORTEX_INTERNAL_KEY` 校验的——会不会 401？

### 会，而且一定会 401。

我查过服务端当前的校验代码：

```python
# novaic-agent-runtime/queue_service/main.py:107
_QUEUE_INTERNAL_KEY = ServiceConfig.QUEUE_SERVICE_INTERNAL_KEY or ""
# ↑ 只认 QUEUE_SERVICE_INTERNAL_KEY 的值

# novaic-cortex/novaic_cortex/api.py:113, 137–139
_INTERNAL_KEY: str = ""
# install_internal_key(cortex_key) 注入，来源是 ServiceConfig.CORTEX_INTERNAL_KEY
# ↑ 只认 CORTEX_INTERNAL_KEY 的值
```

**现实是：**
- 没有任何环境变量叫 `NOVAIC_INTERNAL_KEY`
- Queue Service 和 Cortex 各用各的 Key，两边 Key 值可能不同
- 如果我们在 client 层自动读 `NOVAIC_INTERNAL_KEY`（空），或者强制用单一值替代，两边服务端都会 401

### 这是 PR-05 ticket 本身的 bug — 我的锅

Ticket `§实施 第 35 行` 写的 `X-Internal-Key: <env NOVAIC_INTERNAL_KEY>` 是**我起草时凭空造的变量名**，没核对现实。**这不是你的错**——你在 T0 阶段就逮到了，做得非常对。

### 裁决：**PR-05 不动 Key，只动 Service 身份**

PR-05 范围**收窄**为：

| 任务项 | 原 ticket 意图 | 新裁决 | 你要做什么 |
| --- | --- | --- | --- |
| `X-Internal-Service: <service_name>` 自动注入 | 做 | **做** | 按原计划实现 |
| `service_name` 必填 | 做 | **做** | 按原计划实现 |
| `X-Internal-Key` 自动注入 | 做 | **不做** | 不要碰这块，保持现状由 caller 自己传 headers |
| 统一 `NOVAIC_INTERNAL_KEY` | 做 | **不做** | 另开 PR，先记技术债 |
| 删 `task_queue/client.py` 里的手工 Key 注入 | 做 | **不删** | 保留现有 `QUEUE_SERVICE_INTERNAL_KEY` 注入逻辑 |
| 删 `cortex_bridge.py` 里的手工 Key 注入 | 做 | **不删** | 保留现有 `CORTEX_INTERNAL_KEY` 注入逻辑 |

### 为什么这样裁决？

统一 Key 不是 client 一家能搞定的——**要同时改**：
1. Queue Service 的 auth middleware（新旧两套 Key 兼容）
2. Cortex 的 auth middleware（新旧两套 Key 兼容）
3. 8 个服务的 `config.ini` / 启动脚本
4. 生产环境的 secret rotation

这个是独立工单，不属于 PR-05 的范围。把它塞进 PR-05 会让爆炸半径失控，也会让你这第一次"改现有代码"的 PR 变成不可控的大混战。

### 你 v2 调研里要补这一条

在报告末尾新增一节 `## 范围收窄决议`，抄一遍我上面那张表。目的是：以后任何人（包括你自己半年后回来看）都清楚 "PR-05 为什么没做 Key 统一"——理由是刻意延后，不是遗漏。

**同时在 `docs/roadmap/technical-debt.md` 加一笔新技术债**（一两句话即可）：

```markdown
- **内部 Key 未统一**：`QUEUE_SERVICE_INTERNAL_KEY` / `CORTEX_INTERNAL_KEY` / 其他服务 Key 各自独立。
  后续 PR 统一为 `NOVAIC_INTERNAL_KEY` + 服务端 auth 兼容灰度。
  （PR-05 调研期发现，刻意延后。见 reviews/PR-05-preflight-review.md §2。）
```

这一笔你在 v2 合并的时候一起提交。

---

## 3. `service_name` 命名定稿

你原来的建议：`runtime-worker` / `runtime-health`。我同意"runtime 需要细分"的判断（原 ticket §99 建议的单词短名 `runtime` 太粗），但对具体名字做个微调：

**最终命名表（以此为准）**：

| service_name | 进程 | 备注 |
| --- | --- | --- |
| `business` | novaic-business | — |
| `cortex` | novaic-cortex | — |
| `gateway` | novaic-gateway | — |
| `device` | novaic-device | — |
| `runtime-task` | task_worker_sync | 原计划叫 `runtime-worker`，改 `-task` 更准确（与其他 worker 区分） |
| `runtime-scheduler` | scheduler_worker_sync | — |
| `runtime-health` | health_worker_sync | ✅ 你原来的选择 |

PR-05 里只会用到上面 7 个。将来 PR-15/16 会再加 `runtime-subscriber`，不属于本 PR 范围。

---

## 4. 你漏说的一件"合 PR 时必须做"的事

你的 Q4 回答了"allowlist 哪些能删"，但**没明说"这 10 行必须和 PR-05 代码在同一个 commit 里删掉"**。

背景：PR-04 的 CI lint (`scripts/ci/lint_httpx.sh`) 一旦看到某个 allowlist 文件里的 `httpx.Client(...)` **消失**了（因为你改成 `internal_client`），而 allowlist 里**还留着这一行**——lint 会通过（没命中），没问题。但反过来，如果你漏改某个文件里的 `httpx.Client`，allowlist 已经删了那一行——lint **会红**。

所以顺序是：
1. 改代码（`httpx.Client()` → `internal_client(service_name=..., ...)`）
2. **同一 commit** 里把 `lint_httpx.sh` 的 allowlist 对应行删掉
3. 本地跑 `bash scripts/ci/lint_httpx.sh` 确认 green
4. 才能 push

**v2 调研报告里你要明确写这一条操作顺序**，表明你心里清楚 allowlist 是"一起动的"。

---

## 5. v2 调研报告验收清单

你更新调研报告时，请在原文件或新开 `PR-05-preflight-antigravity-v2.md` 里补齐下列 6 项。**全部满足我才批准 T1。**

- [ ] **新增表**：SDK 实例化方迁移表（13 行，见 §1.2）
- [ ] **修正 Q2 描述**：删掉"`TaskQueueClient` / `SagaClient` 是跨服务通用 SDK"的说法，改为"runtime 内部类，`service_name` 由两个 worker 各自传 `runtime-task` / `runtime-scheduler`"
- [ ] **新增章节 `## 范围收窄决议`**：抄 §2 的裁决表
- [ ] **采纳命名表**：§3 的 7 行 `service_name` 列表直接粘进来
- [ ] **新增 `## 提交顺序约定`**：allowlist 与代码同 commit，本地 lint green 才 push（§4）
- [ ] **Q4 每个 KEEP 条目加一行永久保留理由**（§1.4 小改进）

---

## 6. v2 批准后，T1 阶段的再提醒

调研批准后才进 T1。动手时，我再强调三条原 brief 里的硬约束：

1. **`service_name=None` 直接 raise**，不要搞 `default="unknown"`
2. **不搞 `service_name` 可选 overload + warn-then-raise 的两版灰度**——一次到位
3. **每仓一个 commit**，便于 revert
4. （新加）**提交前本地跑一遍 `bash scripts/ci/lint_httpx.sh`**，green 才 push

---

## 7. 收尾

你这次调研的质量整体是合格的，我甚至要说——**比一般能独立干活的工程师高一档**。原因不是你做对了多少（那只是基本功），而是你**发现了 ticket 本身的错误并主动提出来问**。这个行为模式保持下去，你独立接手更复杂的 PR 只是时间问题。

要改的 6 条不是"你哪里不行"，是"reviewer 要求你的报告具备什么样的完整度"——**把这 6 条当成模板**，PR-06 起你自己就知道该交什么样的调研。

**补完 v2 直接回我"已更新"。我看一眼就批，不会再拉长流程。**

— Reviewer
