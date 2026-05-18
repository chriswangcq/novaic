# PR-05 T1 交付 Review — **打回返工**

> 被审对象：T1 阶段 5 个 commit（novaic-common / novaic-agent-runtime / novaic-gateway / novaic-device / main repo bump）
> 对照文件：
> - 你自己的 [调研 v2](PR-05-preflight-antigravity.md)
> - [上游 review](PR-05-preflight-review.md)
> - [批准函](PR-05-approval.md)
>
> **结论：**
> - ❌ 不能合并
> - ❌ 不能部署
> - ✅ 可以返工（见 §6 清单）
>
> **严重程度：** 5 条 Blocking + 3 条 Scope 缺失 + 3 条验收失效 = 11 项。你需要知道错在哪，所以我把每一项的证据都贴出来了——不是要打击你，是这些东西每一条都会让下一个 reviewer 直接拒绝合并。你自己先消化一遍。

---

## 0. 先说真相：你的"ALL GREEN"全是假象

你交付时说：

> 验收命令执行结果 (ALL GREEN ✅)

我逐条核验：

| # | 你的"绿" | 真相 |
| --- | --- | --- |
| 1 | 漏网之鱼 grep 无输出 | **Grep pattern 不覆盖 SDK 类**（`EntangledServiceClient` / `TaskQueueClient` / `SagaClient`）。你自己调研 v2 §2 表 23 行里有 14 行是 SDK 类，grep 根本看不见——自然报绿。 |
| 2 | `lint_httpx.sh` OK | **Allowlist 原封不动**（15 行一行没删）。lint 的本质是"allowlist 之外有违规才红"；allowlist 没清理等于给所有老代码免死金牌。绿 = "合规"是错觉。 |
| 3 | `pytest` 3 条 PASS | **三条单测只覆盖 `clients.py` 内部 factory**。对你调研 v2 §2 列的 3 个 SDK 类（`EntangledServiceClient`/`TaskQueueClient`/`SagaClient`）契约一个测都没写。pytest 绿 ≠ 迁移正确。 |

**三条绿的共同问题**：验收命令是"证明我做完了"，不是"找一个能过的理由"。你看到 green 就停下，没有反问"为什么我调研报告说要改 23 行但 grep 报 0 漏？"

这一刻你脑子里该响的警报是：**我的验收手段不完整**。结果警报没响。

---

## 1. 🔴 Blocking 问题（5 条）— 这些问题不解决，runtime 启不起来

### 1.1 `health_worker_sync.py` 两处 SyntaxError — 文件无法 import

```startLine:80:endLine:86:novaic-agent-runtime/task_queue/workers/health_worker_sync.py
        if self._client is None or self._client.is_closed:
            self._client = internal_client(service_name="runtime-health",
                base_url=self.queue_service_url,
                base_url=self.queue_service_url,
                timeout=httpx.Timeout(10.0, connect=3.0),
            )
        return self._client
```

```startLine:186:endLine:191:novaic-agent-runtime/task_queue/workers/health_worker_sync.py
            # Check active sessions so we only dispatch for truly orphaned messages
            queue_client = internal_client(service_name="runtime-health",
                base_url=self.queue_service_url,
                base_url=self.queue_service_url,
                timeout=httpx.Timeout(10.0, connect=3.0),
            )
```

**Line 83 和 188 各有一处 `base_url=self.queue_service_url` 重复**。

验证：

```bash
$ python -c "import py_compile; py_compile.compile('novaic-agent-runtime/task_queue/workers/health_worker_sync.py', doraise=True)"
SyntaxError: keyword argument repeated: base_url
```

**后果**：HealthWorker 连 import 都失败，runtime 启动即崩。这是 hihi bug 的兜底服务——你把它干废了。

**根因**：改代码时复制粘贴没核对，提交前没做最基本的 `python -m py_compile` smoke test，也没启动 runtime 跑一下。

### 1.2 `novaic-business` 完全没 commit — 11 处调用会 TypeError

你的提交列表里**没有 novaic-business**：

```
novaic-common / novaic-agent-runtime / novaic-gateway / novaic-device / main repo
```

但你自己的调研 v2 §2 表第 4–14 行：

> 11 行 `EntangledServiceClient` 在 `novaic-business/business/internal/entity.py`，应传 `"business"`

我核对现状：

```bash
$ rg "EntangledServiceClient\(" novaic-business/business/internal/entity.py | head -3
68:        with EntangledServiceClient() as client:
106:        with EntangledServiceClient() as client:
122:        with EntangledServiceClient() as client:
...（11 行全都是裸 EntangledServiceClient()，没有 service_name）
```

**实操验证（模拟一次调用）**：

```bash
$ python -c "from common.entangled_client import EntangledServiceClient; c = EntangledServiceClient()"
TypeError: EntangledServiceClient.__init__() missing 1 required positional argument: 'service_name'
```

**后果**：business 调用任何 entity 相关接口（创建 agent、列 agent、取 scope、...）全部 crash。这些接口是 Gateway→Business 的主链路，意味着**整个前端读写实体都会炸**。

**根因**：你调研报告 v2 §2 表里自己列了 11 行要改，但你只改了 runtime SDK（rows 1–3）和直调 call site（rows 15–23），**完全跳过 rows 4–14**。你没有 checklist 式执行你自己的报告。

### 1.3 `novaic-common/common/entangled_client.py` 有未提交改动

```bash
$ cd novaic-common && git status --short
 M common/entangled_client.py

$ git diff common/entangled_client.py
-            self._session = internal_sync_client(
-                self.service_name,
+            self._session = internal_sync_client(service_name=self.service_name,
                 timeout=httpx.Timeout(self.timeout, connect=10.0),
```

这是一个小的 positional → keyword 调整（合理），但**没 commit**。submodule 处于脏状态。

**后果**：主仓 `d806261` bump 的 submodule pointer 指向的是 `5a12b15`，它不含这个改动。别人 pull 之后拿到的代码和你本地不一样——典型的"本地能跑、远端崩"。

**根因**：`git status` 没扫，或者扫了没在意。

### 1.4 `health_worker_sync.py` line 203 另一处 SDK 调用漏传 `service_name`

```startLine:202:endLine:204:novaic-agent-runtime/task_queue/workers/health_worker_sync.py
            # Dispatch orphaned messages
            saga_client = SagaClient(self.queue_service_url, timeout=10.0)
            dispatched = 0
```

你调研 v2 §2 只列了 worker 文件里 2 处 SDK 实例化（task_worker 2 处、scheduler 1 处），**漏了 health_worker 里这 1 处**。

**验证**：你本来 grep 过 `TaskQueueClient(|SagaClient(`，如果认真看结果，这行应当被抓到。说明你 grep 了但没过全部匹配项。

**后果**：即使 §1.1 的 SyntaxError 修了、orphan 消息 fallback 分支走到这一行，照样 TypeError。

### 1.5 综合结论：runtime 启不起来，business 读不了实体

把 §1.1 + §1.2 + §1.4 合起来看：
- HealthWorker import 失败 → runtime 进程起不来
- business entity.py 11 处 → gateway 调 business 全 500
- health_worker 内 SagaClient → 即使前两条修了，orphan fallback 仍会崩

**三条都触发，整个平台动不了**。

---

## 2. 🟡 Scope 缺失（3 条）— 你自己调研里说要做的事没做

### 2.1 调研 v2 §4 的 10 个 "DELETE in PR-05" 一个都没迁移

你自己列的 10 个应在 PR-05 迁移的文件：

```
novaic-device/device/gateway_signaling.py
novaic-business/business/agent_actions.py
novaic-business/business/internal/factory_client.py
novaic-business/business/internal/message.py
novaic-business/business/internal/signaling.py
novaic-business/business/factory_admin_client.py
novaic-business/business/device_client.py
novaic-agent-runtime/task_queue/factory_client.py
novaic-agent-runtime/task_queue/utils/cortex_bridge.py
novaic-gateway/gateway/api/app_client.py
```

我核对现状：

```bash
$ for f in <上面 10 行>; do rg -c "httpx\.(Async)?Client\(" "$f"; done
STILL HAS: novaic-device/device/gateway_signaling.py (1)
STILL HAS: novaic-business/business/agent_actions.py (1)
STILL HAS: novaic-business/business/internal/factory_client.py (1)
STILL HAS: novaic-business/business/internal/message.py (1)
STILL HAS: novaic-business/business/internal/signaling.py (1)
STILL HAS: novaic-business/business/factory_admin_client.py (1)
STILL HAS: novaic-business/business/device_client.py (9)
STILL HAS: novaic-agent-runtime/task_queue/factory_client.py (1)
STILL HAS: novaic-agent-runtime/task_queue/utils/cortex_bridge.py (1)
STILL HAS: novaic-gateway/gateway/api/app_client.py (2)
```

**10/10 原封不动。**

### 2.2 `scripts/ci/lint_httpx.sh` allowlist 一行没删

```bash
$ wc -l scripts/ci/lint_httpx.sh
35

$ grep -c "DELETE in PR-05" scripts/ci/lint_httpx.sh
0
```

Review §7（提交顺序约定）明确写的是：

> 1. 改代码（`httpx.Client()` → `internal_client(service_name=..., ...)`）
> 2. **同一 commit** 里把 `scripts/ci/lint_httpx.sh` 的 allowlist 对应行删掉
> 3. 本地跑 `bash scripts/ci/lint_httpx.sh` 确认 green
> 4. 才能 push

你跳过了第 1 步（对 10 个文件），于是第 2 步也没地方删，第 3 步 green 变成了"因为老代码被 allowlist 兜着所以绿"。

### 2.3 根本问题：你没把调研 v2 当成 checklist 执行

调研 v2 共 23 行 §2 call site + 10 行 §4 DELETE = **33 条行动项**。

实际完成：
- §2 rows 1–3（runtime SDK）：✅ 完成（但 1.4 漏了第 4 处）
- §2 rows 4–14（business EntangledServiceClient）：❌ **0/11**
- §2 rows 15–23（直调 call site）：✅ 完成
- §4 10 行迁移：❌ **0/10**

**33 项里漏了 21 项**。你交付时却说 "按计划完成了...符合 PR-05 preflight review 的所有 T1 阶段要求"——这种描述在专业团队里等同于造假陈述，会严重损失 reviewer 信任。下次请**先对照自己的调研报告逐条打勾**再说"完成"。

---

## 3. 🟠 验收命令为什么会"假绿"（对你有教学价值）

### 3.1 "漏网之鱼 grep" pattern 不完整

Review approval §"验收时我会看什么" 给的是：

```bash
rg "internal_client\(|internal_(sync_|async_)?client\(" novaic-*/ --type py | rg -v "service_name="
```

这个 pattern **只查 `internal_*client(` 入口**，不查：
- `EntangledServiceClient(...)` ← 你调研 §2 rows 4–14 的全部
- `TaskQueueClient(...)` ← 你调研 §2 rows 1, 2
- `SagaClient(...)` ← 你调研 §2 rows 2, 3（还漏了 health_worker line 203）

**这个 pattern 是我给你的，本身不全——这是我的责任的一部分**。但是：

你作为执行人，应当在 T1 阶段对照**自己**的调研 v2 §2 表 23 行逐条验证，**发现 pattern 不覆盖 SDK 类后主动补一条**：

```bash
# 应补的检查
rg "(EntangledServiceClient|TaskQueueClient|SagaClient)\(" --type py \
  | rg -v "service_name=" \
  | rg -v "^docs/|/tests/|__init__\.py|# "
```

如果你跑了这条，business 那 11 行立刻爆出来。

**教训**：reviewer 给的验收命令是"底线"，不是"天花板"。你自己知道改了什么，就该自己补足证明。

### 3.2 `lint_httpx.sh` green 的本质

Lint 的逻辑：

```bash
if 文件在 allowlist 中: pass
else: if 文件包含违规 pattern: fail
```

你**既没改代码、也没删 allowlist**：
- 老代码没改，因为他们还被 allowlist 保护着
- 新改的 9 个文件原来用 `internal_client` 就在豁免外，改完后还用 `internal_client`，当然绿

这个绿**完全不能证明迁移进度**。

**真正能证明迁移的做法**：每迁移一个文件，同 commit 删对应 allowlist 行；此时 lint 若还是 green，才说明那个文件真的没残留违规。

### 3.3 pytest 只测了 `clients.py` 内部

你写的 3 条单测：

```startLine:1:endLine:24:novaic-common/tests/test_internal_client.py
# test_internal_client_requires_service_name → 测 internal_client 直接调用无 service_name raise
# test_internal_client_injects_header → 测 X-Internal-Service 头注入
# test_internal_client_warns_if_key_not_set → 测 NOVAIC_INTERNAL_KEY 未设置 WARN
```

**这是 clients.py 本体的契约**，不测 SDK 类封装。

**该补的测**（至少 3 条）：

```python
def test_entangled_client_requires_service_name():
    with pytest.raises(TypeError):
        EntangledServiceClient()  # 无参数

def test_task_queue_client_requires_service_name():
    with pytest.raises(TypeError):
        TaskQueueClient("http://localhost:8716")  # 少 service_name

def test_saga_client_requires_service_name():
    with pytest.raises(TypeError):
        SagaClient("http://localhost:8716")
```

**没这些测的话，就是 SDK 类契约裸奔**——契约被改了但没 CI 守门。

---

## 4. 对照你 self-claim 的每一条

| 你说的 | 真相 |
| --- | --- |
| "按计划完成了 `internal_client` 的身份改造" | `internal_client` 本身 ✅；但调用侧只完成 1/3 |
| "通过强制 `service_name` 参数规范了内部服务间调用的身份声明" | clients.py 里强制了 ✅；但 business 11 处调用方没改，实际运行会崩 |
| "已完成对 runtime、gateway、device 等主调方的第一波改造" | runtime 部分完成（遗留 SyntaxError + 1 处 SagaClient 漏）；gateway/device 直调 call site ✅；**business 完全没动** |
| "符合 PR-05 preflight review 的所有 T1 阶段要求" | ❌ 违反了"每仓一个 commit"（business 没 commit）、违反了"提交顺序约定"（allowlist 没清） |

---

## 5. 对你这次返工能力评估的下调

PR-01 时你是"字面化理解 ticket"的错（建了 `novaic_common/` 而不是 `common/`）。我当时给的反馈是：**Code 前先 Read**。

这次 T1 犯的是**更严重**的一档错误：**自己写的调研报告不按 checklist 执行，却宣称完成**。

区别：
- PR-01 是理解偏差 → 可教
- PR-05 T1 是对自己承诺的执行不闭环 → 可教但必须补**一道机械纪律**

**必须补的纪律**：T1 开工时，把调研 v2 §2 + §4 的所有行项复制到本地一个 checklist 文件（比如 `pr05-todos.md`），**每做完一条勾一个 `[x]`**。交付前**对照 checklist 逐项核**。23+10=33 项，少一条都不能说"完成"。

这不是羞辱性的要求——大多数高水平工程师都这样做，只是不说。

---

## 6. 返工 Checklist（满足后我再 review，不满足不看）

请直接在这个文档下方或新开 `PR-05-t1-rework-notes.md` 写"完成情况"，每行勾起来再来找我。

### 6.1 立刻修 Blocking（必做，不做连本地 smoke test 都过不了）

- [ ] 修 `health_worker_sync.py` line 83 重复的 `base_url`
- [ ] 修 `health_worker_sync.py` line 188 重复的 `base_url`
- [ ] 修 `health_worker_sync.py` line 203 `SagaClient(...)` 补 `service_name="runtime-health"`
- [ ] 修 `business/internal/entity.py` 11 处 `EntangledServiceClient()` → `EntangledServiceClient(service_name="business")`
- [ ] `novaic-common/common/entangled_client.py` 的未提交改动 commit 进 PR-05 的 common commit（amend 或新开一个跟 common 同类的 commit）

### 6.2 完成调研 v2 §4 的 10 个 DELETE（现在必须做完，否则 PR-05 不叫"主调方第一波改造"）

对以下 10 个文件，每个都要：
- 把裸 `httpx.Client()` / `httpx.AsyncClient()` → `internal_client(service_name=..., ...)` / `internal_async_client(service_name=..., ...)`
- 保留原有的手工 `X-Internal-Key` 注入（review §2 裁决）
- **同 commit** 从 `scripts/ci/lint_httpx.sh` allowlist 里删对应行
- 本地跑 `bash scripts/ci/lint_httpx.sh` 确认 green

**service_name 分配对应表**（照用）：

| 文件 | service_name |
| --- | --- |
| `novaic-device/device/gateway_signaling.py` | `"device"` |
| `novaic-business/business/agent_actions.py` | `"business"` |
| `novaic-business/business/internal/factory_client.py` | `"business"` |
| `novaic-business/business/internal/message.py` | `"business"` |
| `novaic-business/business/internal/signaling.py` | `"business"` |
| `novaic-business/business/factory_admin_client.py` | `"business"` |
| `novaic-business/business/device_client.py` | `"business"` |
| `novaic-agent-runtime/task_queue/factory_client.py` | `"runtime-task"` |
| `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` | `"runtime-task"` |
| `novaic-gateway/gateway/api/app_client.py` | `"gateway"` |

- [ ] device/gateway_signaling.py 迁移 + allowlist 删行
- [ ] business/agent_actions.py ... allowlist 删行
- [ ] business/internal/factory_client.py ... allowlist 删行
- [ ] business/internal/message.py ... allowlist 删行
- [ ] business/internal/signaling.py ... allowlist 删行
- [ ] business/factory_admin_client.py ... allowlist 删行
- [ ] business/device_client.py ... allowlist 删行（这个有 9 处命中，逐个改）
- [ ] runtime/task_queue/factory_client.py ... allowlist 删行
- [ ] runtime/task_queue/utils/cortex_bridge.py ... allowlist 删行
- [ ] gateway/api/app_client.py ... allowlist 删行

### 6.3 补单测（对 3 个 SDK 类各一条）

- [ ] `test_entangled_client_requires_service_name` → `EntangledServiceClient()` 必须 TypeError
- [ ] `test_task_queue_client_requires_service_name` → `TaskQueueClient("http://...")` 必须 TypeError
- [ ] `test_saga_client_requires_service_name` → `SagaClient("http://...")` 必须 TypeError

放到：
- EntangledServiceClient 测可放 `novaic-common/tests/test_entangled_client.py`
- TaskQueueClient / SagaClient 测可放 `novaic-agent-runtime/tests/test_client_contract.py`

### 6.4 补一次诚实的验收

```bash
# 1. 本次必加的 SDK 类 grep
rg "(EntangledServiceClient|TaskQueueClient|SagaClient)\(" --type py \
  | rg -v "service_name=" \
  | rg -v "^docs/|/tests/|__init__\.py|# |class "
# 预期：空

# 2. 老 pattern
rg "internal_client\(|internal_(sync_|async_)?client\(" novaic-*/ --type py \
  | rg -v "service_name=" \
  | rg -v "novaic-common/common/http/clients.py"
# 预期：空

# 3. 所有触及文件 compile 过
for f in $(git diff --name-only HEAD~5 HEAD | grep '\.py$'); do
  python -c "import py_compile; py_compile.compile('$f', doraise=True)" && echo "OK $f"
done
# 预期：每一行 OK

# 4. lint
bash scripts/ci/lint_httpx.sh && bash scripts/ci/lint_dispatch.sh
# 预期：两条 OK（此时 allowlist 已删 10 行，绿才是真绿）

# 5. smoke import
python -c "from novaic_agent_runtime.task_queue.workers.health_worker_sync import HealthWorkerSync; print('OK')"
python -c "from common.entangled_client import EntangledServiceClient; c = EntangledServiceClient(service_name='test'); print('OK')"
# 预期：OK

# 6. pytest 覆盖 SDK 类契约（新测）
pytest novaic-common/tests/test_internal_client.py novaic-common/tests/test_entangled_client.py novaic-agent-runtime/tests/test_client_contract.py -v
# 预期：≥ 6 passed（原 3 + 新 3）
```

### 6.5 Commit 顺序（重开）

**别在原来 5 个 commit 上 amend**（已经 push 了 `d806261`），新开 commits：

```
# 每个 submodule 一个 fix commit：
novaic-common:         fix(common): commit missing entangled_client kwarg change (PR-05 rework)
                       或直接并入下方 business SDK commit 一起
novaic-agent-runtime:  fix(runtime): health_worker syntax + saga_client service_name (PR-05 rework)
novaic-agent-runtime:  refactor(runtime): migrate factory_client + cortex_bridge to internal_client (PR-05 rework)
novaic-business:       refactor(business): adopt internal_client(service_name="business") across entity + 6 more files (PR-05 rework)
novaic-device:         refactor(device): migrate gateway_signaling.py to internal_client (PR-05 rework)
novaic-gateway:        refactor(gateway): migrate app_client.py to internal_client (PR-05 rework)
main repo:             chore: bump submodules + clear 10 entries from lint_httpx allowlist (PR-05 rework)
```

### 6.6 交付时

发一段消息或 `PR-05-t1-rework-notes.md`，把 §6.1–§6.4 每条状态贴出来（`[x] ...`），**不要只说 "已修复"**。让 reviewer 一眼能扫完。

---

## 7. 最后一句

这次不是能力问题——你的 surface 分析、Key 冲突发现都做得好。**这次是交付纪律问题**：对自己写的调研报告不闭环、对自己给出的"ALL GREEN"不存疑。

一次这种错是成本，下一次就是信任折损。按 §6 走完返工，然后告诉我"6.1–6.4 全部 [x] 完成"。我会再验一遍再决定是否批准。

**不要只说"已完成"——我下次看到这四个字会先不信任地核一遍。**

— Reviewer
