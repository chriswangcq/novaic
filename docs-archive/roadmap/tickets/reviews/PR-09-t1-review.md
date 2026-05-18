# PR-09 T1 Review（TriggerType + schema 迁移）

| 字段 | 值 |
| --- | --- |
| Reviewer | senior |
| Verdict | **APPROVE with Corrections**（不是打回，2 条必补 + 1 条提醒） |
| Main repo commits | `0ac4416 feat(migration)` → `3cabc66 chore: bump` → `7731246 docs: checklist` |

---

## §A  核对通过

| 项 | 证据 |
| --- | --- |
| 生产代码零 `user_response` 残留 | `rg "user_response" --type py` 除 `from_legacy` 和 docs 外全清 |
| `TriggerType` 6 值 + `from_legacy` 映射 | `novaic-common/common/wake/trigger_types.py:5-21` |
| Pydantic validator 兜底 | `novaic-agent-runtime/queue_service/routes.py:481-488` — `trigger_type: TriggerType` + validator 调 `from_legacy` |
| DB 读出点兜底 | `novaic-agent-runtime/queue_service/session_repo.py:100,268,388` — 3 处 `from_legacy(...).value` |
| 发送端硬值 | business 侧 4 处全部 `TriggerType.XXX.value` |
| `definitions.py:512` | `user_response → user_message`，`timer/event` 保留 ✅ 符合方案 A |
| Git 分层干净 | 主仓 3 个 commit（feat/chore/docs 分开），3 个子模块各 1 commit |
| 迁移 SQL | `scripts/migrations/2026-04-18-wake-triggers-rename.sql` 存在、幂等 |
| 单测绿 | `pytest novaic-common/tests/test_trigger_types.py` 1 passed |

---

## §B  必须补的 2 条

### B.1  技术债少写一条 —— `wake_triggers[].type` vs `TriggerType` 不对齐

preflight §5 承诺会同步写入 `docs/roadmap/technical-debt.md`，实际 `technical-debt.md` 只新增了 PR-08 的 `get_resolver()` TD 那一条（line 38），**没有** `timer/event` 的 TD。

**补一条**到 `docs/roadmap/technical-debt.md`，格式参考 PR-08 那条：

> **LLM tool schema 的 `wake_triggers[].type` 与 `TriggerType` 不对齐**（PR-09 引入）：`novaic-common/common/tools/definitions.py:512` 的 `wake_triggers[].type` enum 为 `["user_message", "timer", "event"]`，而 `common.wake.trigger_types.TriggerType` 为 `[user_message, subagent_send, spawn_subagent, scheduled_wake, system_wake, recovered]`。两者只共享 `user_message` 一个值。目前按独立枚举处理，未来可考虑 (a) 弃用 `timer/event` 或 (b) 扩 `TriggerType` 统一。

### B.2  DB 真实行采样疑似假勾

preflight §2 的 `[x] 先决取样：在拷贝 DB 上 sample 5-10 条真实 wake_triggers，确认 JSON 字符串是否严格带双引号` 需要真实证据。

问题：本机 `~/.novaic/data/entangled.db` 不存在（`ls ~/.novaic/data/` → `No such file or directory`）。那你这个 `[x]` 勾的 **样本是从哪来的**？

可能性：
1. 你在**另一台有数据的机器**上跑了采样 —— 请在 preflight §2 对应位置**贴上真实 sample 输出**（至少 2-3 行 `wake_triggers` 的实际 JSON 内容），证明引号格式是双引号。
2. 你基于**空 DB 或自己造的 mock DB**做了 SELECT —— 那这一勾作废。此时请把 `[x]` 改为 `[/]`，并加注："本地环境无生产数据；SQL 仅按代码侧 JSON 序列化方式验证为双引号格式（见 `schema_push.py:110` 与 `subagent_utils.py:249` 的源头写法）。生产环境合并前由运维在真实 DB 上 sample 后再确认。"

**不管哪一种，preflight 那条 `[x]` 都不能空勾放着。**

这是第二次出现"checkbox 打了但可能没真跑"的情况（第一次是 PR-06 的 metric counter）。再次提醒：**每个 `[x]` 必须对应一份可验证的 artifact**（命令输出 / 代码行 / 测试绿）。生产数据迁移 PR 对这一点的要求比平时更严。

---

## §C  提醒（不用补）

### C.1  测试仅 1 条，preflight §2 声称 2 条

preflight §2 列了 2 项：
- [x] `from_legacy("user_response") is USER_MESSAGE`
- [x] 端到端：新建 subagent，断言默认 `[{"type": "user_message"}]`

`test_trigger_types.py` 只覆盖了第 1 条。第 2 条的 E2E 需要起 Business + 调接口，属于集成测试 —— 如果你跑过手工验证（例如 `curl` + `sqlite3 SELECT`），在 preflight 里注明 "手工验证"；否则这个 `[x]` 也要加注。

不影响合并，但以后别随便勾 checkbox。

### C.2  观察期

ticket 备注明文"单独合并，单独观察 24h 再推 PR-10"。等老板确认上线跑 24h 观察期后再推 PR-10。这段时间可以先做 PR-10 的 preflight 调研（不动代码），这样 24h 过去立刻能开 T1。

---

## §D  合并前补丁清单

- [ ] `technical-debt.md` 追加 `wake_triggers[].type` 不对齐的 TD（§B.1）
- [ ] preflight §2 的 "先决取样" 勾位补证据或改 `[/]` 加注（§B.2）
- [ ] 这 2 条改完单独一个 commit：`docs: PR-09 follow-up TD + sampling note`，推到主仓；不需要动子模块
- [ ] `git status --short` 全清
