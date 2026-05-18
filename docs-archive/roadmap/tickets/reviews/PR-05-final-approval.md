# PR-05 最终批准

> 被审对象：PR-05 完整交付链（T1 + 2 轮返工 = 共 8 个 rework commit + 3 个 main bump）
> 历史：
> - [调研 v2](PR-05-preflight-antigravity.md) → [调研批准](PR-05-approval.md) → [T1 打回](PR-05-t1-rejection.md) → [T1 返工笔记](PR-05-t1-rework-notes.md) → [返工 review](PR-05-t1-rework-review.md) → **本文**
>
> **状态：✅ 批准合并**

---

## 最终核验

### novaic-common 干净

```
$ cd novaic-common && git status --short
(空)

$ git log --oneline -3
0eeafb3 fix(common): commit bonus EntangledServiceClient call site + SDK contract test (PR-05 rework cont.)
48716d7 refactor(common): internal_client requires service_name (PR-05)
ac10425 feat(common): common.agents.ownership skeleton (PR-02)
```

### 新 commit 内容正确

```
$ git show --stat 0eeafb3
 common/auth.py                 | 4 +++-
 tests/test_entangled_client.py | 6 ++++++
 2 files changed, 9 insertions(+), 1 deletion(-)
```

### Option B 落地干净

```startLine:64:endLine:78:novaic-common/common/auth.py
def check_agent_access(agent_id: str, user_id: str, db=None) -> dict:
    """Verify agent exists and belongs to user via Entangled HTTP.

    Returns the agent dict. Raises 404 if not found, 403 if not owner.
    The ``db`` parameter is accepted for backward compatibility but ignored.
    """
    from common.entangled_client import EntangledServiceClient
    caller_service = os.environ.get("NOVAIC_SERVICE_NAME", "common-auth")
    with EntangledServiceClient(service_name=caller_service) as client:
        agent = client.get("agents", agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return agent
```

- 函数签名不变，所有现有 10 处调用点零改动
- `NOVAIC_SERVICE_NAME` 默认 `"common-auth"`，但在 `main_device.py` / `main_business.py` 启动脚本里设置 env var 后就自动注入真实 caller 身份
- Fallback 到 `"common-auth"` 足够安全（可读、可追溯），不会出现空值/`None`

### Fresh clone 场景已模拟验证

他跑过 `cp -r novaic-common tmp/fresh-test-common && pytest` 全绿。

### 主仓 bump 正确

```
$ git submodule status novaic-common
 0eeafb3... novaic-common (heads/main)   ← pointer = 新 commit
```

---

## PR-05 整体交付总览

### Commit chain

**novaic-common**：3 个（T1 + bonus fix + 无需要再新）

```
0eeafb3 fix(common): commit bonus EntangledServiceClient call site + SDK contract test (PR-05 rework cont.)
48716d7 refactor(common): internal_client requires service_name (PR-05)
```

**novaic-agent-runtime**：3 个

```
bbf2896 refactor(runtime): migrate factory_client + cortex_bridge to internal_client (PR-05 rework)
fdaea18 fix(runtime): health_worker syntax + saga_client service_name (PR-05 rework)
26f8c00 refactor(runtime): adopt internal_client(service_name=...) (PR-05)
```

**novaic-business**：1 个

```
4622356 refactor(business): adopt internal_client(service_name="business") across entity + 6 more files (PR-05 rework)
```

**novaic-gateway**：2 个

```
3e443ea refactor(gateway): migrate app_client.py to internal_client (PR-05 rework)
2dd9df3 refactor(gateway): adopt internal_async_client(service_name=...) (PR-05)
```

**novaic-device**：2 个

```
054e9b1 refactor(device): migrate gateway_signaling.py to internal_client (PR-05 rework)
e033912 refactor(device): adopt internal_sync_client(service_name=...) (PR-05)
```

**main repo**：3 个 bump

```
a582f14 chore: re-bump novaic-common for auth.py + contract test (PR-05 rework cont.)
59ae06a chore: bump submodules + clear 10 entries from lint_httpx allowlist (PR-05 rework)
d806261 chore: bump submodule pointers for PR-05 (Internal Client)
```

### 承诺兑现对照

| 调研 v2 承诺 | 状态 |
| --- | --- |
| §1 升级 4 个 factory 函数加 `service_name` 必填 | ✅ |
| §2 23 行 call site 迁移 | ✅ + 4 行 bonus（auth.py / entity_store.py / saga_worker×2） |
| §3 不动 `X-Internal-Key`，保留手工注入 | ✅ |
| §4 10 个 DELETE 文件迁移 + allowlist 清 10 行 | ✅ |
| Review §3 命名定稿 7 个 + `runtime-saga` + `common-auth`（env 兜底） | ✅ 实际用到 9 个 |
| Review §7 提交顺序约定（同 commit 删 allowlist） | ✅（返工后） |
| 3 个 SDK 类契约单测 | ✅ |
| `clients.py` 原 3 条单测 | ✅ |

### 最终验收命令全绿

```
$ bash scripts/ci/lint_httpx.sh
httpx lint OK
$ bash scripts/ci/lint_dispatch.sh
dispatch lint OK
$ (compile check on 7 touched files)
7/7 OK
$ pytest (common + runtime SDK contracts)
6 passed
```

---

## 需要后续 PR 跟进（不属于本 PR）

以下是 PR-05 期间发现但刻意**延后**的项，已记入 [`technical-debt.md`](../../technical-debt.md)：

1. **内部 Key 统一**：`QUEUE_SERVICE_INTERNAL_KEY` / `CORTEX_INTERNAL_KEY` / 其他 → `NOVAIC_INTERNAL_KEY` + 服务端 auth 兼容灰度
2. **`common/auth.py` service_name 语义**：目前用 env var 注入，未来若有 contextvar 机制可进一步改进
3. **各服务启动脚本设置 `NOVAIC_SERVICE_NAME`**：否则 `common-auth` 调用仍会在日志里显示 `"common-auth"`；建议作为运维侧配置检查清单

---

## 下一张票

你可以开始领 PR-06（服务端消费 `X-Internal-Service` / `X-Caller-Service` header）。

PR-06 的建议先交一份调研报告（沿用 PR-05 那套流程）——本次 PR-05 已经证明调研先行是对的。

交付标准继续沿用：
- Declare done 前每个 submodule + 主仓 `git status` 确认空行
- 对照调研报告逐条打勾
- 验收命令要覆盖调研里列的**全部**契约，不是 reviewer 给的模板

---

## 评语（给下一位 reviewer 看）

- T1 阶段暴露的问题（谎报、伪绿）已通过两轮返工校正
- 第二轮返工主动补 SDK grep 扫出 4 处额外漏网，显示出正确的验收姿态
- 最后一公里的 submodule 提交闭环问题连续两轮出现，但接受反馈后已承诺纳入工作流（"declare done 前跑 git status"）
- 综合看：**可继续派任 Phase 1 其他工单（PR-06/07/08），但仍需保持调研报告先行 + reviewer 严格验收的节奏，至少到 Phase 1 全部完成为止**

— Reviewer
