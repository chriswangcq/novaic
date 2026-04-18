# PR-05 T1 返工 Review — **90% 通过，但 novaic-common 重蹈覆辙**

> 被审对象：6 个 rework commits + [`PR-05-t1-rework-notes.md`](PR-05-t1-rework-notes.md)
> 对照：[上一轮打回函](PR-05-t1-rejection.md) §6
>
> **结论：**
> - ✅ 10 DELETE 迁移、entity.py 11 处、3 个 SDK 契约测、SyntaxError 修复、lint 清理 — 全部到位
> - ❌ 但 `novaic-common` 又有未提交改动 — **这是我上轮 §1.3 专门警告过的同一个错误**
> - ⏸ 不能合并，但返工量极小（一个 commit + bump）

---

## 1. 先说真 green 的部分（这次是真的）

逐条我都核验过：

| 项 | 核验命令 | 结果 |
| --- | --- | --- |
| 所有 touched 文件 compile 过 | `py_compile` on 7 files | ✅ 全 OK（SyntaxError 已修） |
| 10 个 DELETE 文件的 `httpx.Client()` 已消除 | `rg "httpx\.(Async)?Client\(" <10 files>` | ✅ 10/10 MIGRATED |
| `lint_httpx.sh` allowlist 清理 | `wc -l scripts/ci/lint_httpx.sh` | 35 → 25 行，entries 15 → 6 ✅ |
| SDK 类无漏网 | `grep "(Entangled\|TaskQueue\|Saga)Client\("` 过滤 test | ✅ 生产代码 call site 全部带 service_name |
| 6 条单测 PASS | pytest（common 4 + runtime 2） | ✅ 6 passed |
| 双 lint green（真 green） | `lint_httpx.sh && lint_dispatch.sh` | ✅ OK |
| 5 submodule rework commit + 1 main bump | `git log` | ✅ 存在 |

**加分项（你自己找出来的）**：

Q2 调研表里没列的 4 处 SDK 实例化漏网——
- `common/auth.py:69` — `EntangledServiceClient()`
- `business/entity_store.py:28` — `EntangledServiceClient()`
- `task_queue/workers/saga_worker_sync.py:82` — `SagaClient(...)`
- `task_queue/workers/saga_worker_sync.py:83` — `TaskQueueClient(...)`

这 4 处你是跑自己补的 SDK grep 扫出来的——这就是上轮 review §3.1 我要求的"自己补足验收 pattern"。你做到了。

也因此这轮整体评价是：**技术执行水平比上轮明显提升**。你的纪律回来了，能力本来就在。

---

## 2. 🔴 但是，Blocking 问题——**上轮同款错误**

### 2.1 证据

```bash
$ cd novaic-common && git status --short
 M common/auth.py
?? tests/test_entangled_client.py

$ git log --oneline -3
48716d7 refactor(common): internal_client requires service_name (PR-05)   ← T1 commit (amend 后)
ac10425 feat(common): common.agents.ownership skeleton (PR-02)
fac6c64 feat(common): common.wake package skeleton (PR-01)

$ cd .. && git submodule status novaic-common
 48716d7d6ff3169fbb1696a9a73225312921d375 novaic-common (heads/main)
```

**novaic-common HEAD 仍是 T1 时的 `48716d7`（amend 过一次），之后所有"bonus 修复 + 新测文件"都没 commit。**

具体有两个文件处于未提交状态：

1. **`common/auth.py`** — 你 bonus fix 把 `EntangledServiceClient()` 改成了 `EntangledServiceClient(service_name="common-auth")`，但没 commit
2. **`tests/test_entangled_client.py`** — 你在 §6.3 打勾的那个 SDK 契约测，**根本没被 git 跟踪**

### 2.2 这不是"重复小错"，有实际爆炸半径

`common/auth.py::check_agent_access` **是 device 进程 VM 操作的守门函数**：

```
novaic-device/device/vm_routes.py 里调用了 10 次 check_agent_access：
  line 162, 179, 240, 289, 356, 478, 535, 578, 626, 648
```

这些覆盖 VM start / stop / exec / input / screenshot 等几乎全部 VM 操作。

**后果（fresh clone 场景）**：
- 新拉代码的机器上 `common/auth.py` 还是裸 `EntangledServiceClient()`
- `EntangledServiceClient.__init__` 现在必填 `service_name`
- 所以 `check_agent_access()` 一次就 TypeError
- **device 服务的 VM 操作全部崩**

本地"看起来没事"只是因为你本地的 working tree 有改动——**merge / push / deploy 到任何其他环境都会暴雷**。

**这就是上轮打回函 §1.3 原话**：

> 后果：主仓 `d806261` bump 的 submodule pointer 指向的是 `5a12b15`，它不含这个改动。别人 pull 之后拿到的代码和你本地不一样——典型的"本地能跑、远端崩"。
> 根因：`git status` 没扫，或者扫了没在意。

**你这轮又栽在完全同一个地方，只是换了文件名**（上轮是 `entangled_client.py`，这轮是 `auth.py` + 新测文件）。

### 2.3 顺便再次提醒：`test_entangled_client.py` 从没被 git 跟踪过

这个比 `auth.py` 更严重。`auth.py` 至少是个 modified（git 知道它变了），而这个测文件 **git 从头到尾没看见过**——`?? tests/test_entangled_client.py` 就是"untracked"。

意味着你 rework-notes §6.3 `[x]` 的那条：

> [x] `test_entangled_client_requires_service_name` → `EntangledServiceClient()` 必须 TypeError (添加在 `novaic-common/tests/test_entangled_client.py`)

**在远端代码里根本不存在这个测**。CI 上 common 的 pytest 是 3 条不是 4 条。

---

## 3. 🟠 次要但要一起处理：`service_name="common-auth"` 语义可疑

这是次级问题，不阻塞合并，但请在返工时一起修正。

### 问题

`common/auth.py::check_agent_access` 是一个**库函数**，被**多个进程**导入：

```
novaic-device/device/vm_routes.py:15   from common.auth import check_agent_access
novaic-business/business/agent_actions.py  间接走 business.auth → common.auth
```

它自己不是一个进程。当 device 进程调它时，发出去的 HTTP 的"caller 身份"应当是 `"device"`；当 business 间接走它时应当是 `"business"`。硬编码成 `"common-auth"` 就是告诉远端"我是一个叫做 common-auth 的神秘东西"——日志里 join 不到任何真实调用方，Q2 §6 定稿的 7 个 service_name 也没这个。

### 怎么改

三选一（你拍板，但我倾向 B）：

- **A**（最简）：让 `check_agent_access(agent_id, user_id, db=None, *, service_name: str)` 多一个必填参数，调用方 device/vm_routes.py 传 `service_name="device"`。改动量 = 10 行调用点 + 1 行函数签名。
- **B**（折中）：在 `common/auth.py` 里定义一个 module-level `_CALLER_SERVICE_NAME` contextvar 或 env 读取，进程启动时（比如 `main_device.py`、`business` 启动入口）set 一次。调用点不变，签名不变。
- **C**（最复杂）：在 `common.http.clients` 层搞 contextvar，让所有 `internal_client` 使用 "ambient service_name"。但这就超出 PR-05 范围了。

如果你选 A/B，**直接在本次返工一并 commit 就行**。不是新 PR。

---

## 4. 返工清单（这次真的只剩一点）

**必做**：

- [ ] `cd novaic-common && git add common/auth.py tests/test_entangled_client.py`
- [ ] `git commit -m "fix(common): commit bonus EntangledServiceClient call site + SDK contract test (PR-05 rework cont.)"`（因为已经 push 过 `48716d7` 了，**不要再 amend**）
- [ ] 决定 `service_name="common-auth"` 怎么改（§3 A/B/C 选一个，建议 B）。改完同 commit 提交。
- [ ] `cd .. && git add novaic-common && git commit -m "chore: re-bump novaic-common for auth.py + contract test (PR-05 rework cont.)"`
- [ ] Push all

**验收**（这次我只看 2 条）：

```bash
# 1. novaic-common 干净
cd novaic-common && git status --short
# 预期：空行

# 2. fresh clone 模拟
cd /tmp && git clone <repo-url> fresh-test && cd fresh-test/novaic-common
python -c "from common.auth import check_agent_access; print('import OK')"
ls tests/test_entangled_client.py
pytest tests/ -q
# 预期：import OK / 文件存在 / 4 passed
```

---

## 5. 能力评估（这轮 vs 上轮）

| 维度 | 上轮 T1 | 本轮返工 |
| --- | --- | --- |
| 核心改造执行 | ❌ 只做 12/33 还谎称全完成 | ✅ 33 + 4 bonus 都做了 |
| 自我验收纪律 | ❌ 三条绿都是假象 | ✅ 真 green，而且自己补了 SDK grep 发现漏网 |
| SyntaxError smoke | ❌ 整个 HealthWorker 起不来 | ✅ 全部 compile 过 |
| submodule 提交闭环 | ❌ entangled_client.py 未提交 | ❌ **auth.py + 测文件未提交**（同款） |

**3/4 维度从错到对；但 submodule 提交闭环这一条连续两轮栽在同一处。**

这是一个非常具体的肌肉记忆问题，不是能力问题。解法也就一个：

> **每次 declare done 之前，在每个 submodule 和主仓都跑 `git status`，确认空行。**
>
> 如果 `git status` 有任何输出，要么 commit 进去、要么解释为什么故意留着（比如实验性代码）。**"忘了 commit"不是借口**。

请把这条写到你自己的工作卡片/IDE 启动脚本/任何你能每次看到的地方。下轮我再看到同样错误，就是"工程习惯"级别的问题，不是单次失误了。

---

## 6. 最后一句

主体工作**这轮质量接近 senior 水平**——尤其是自己补 SDK grep 扫出 4 处漏网那段，能看出你消化了上轮的 §3 教训。别被 §2 打击到。

补完 common 那一个 commit + pointer bump + `service_name="common-auth"` 的决定，**告诉我你选了哪档 A/B/C**，我看完直接批准合并。

— Reviewer
