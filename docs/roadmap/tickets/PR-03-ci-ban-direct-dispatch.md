# PR-03  CI lint：禁止业务代码直接 POST `/api/queue/dispatch`

| 字段 | 值 |
| --- | --- |
| **Phase** | M0 |
| **Milestone** | M1（前置） |
| **承诺** | R2 |
| **Status** | `[x]` |
| **Depends on** | — |
| **Blocks** | —（约束类，越早合越好） |
| **估时** | 1 h |
| **Owner** | __ |
| **PR 标题** | `ci: ban direct POST /api/queue/dispatch outside assembler` |

## 目标

让 Assembler 成为 dispatch 的唯一出口（R2 的 `[CODE]` 强制）。CI 侧拦住再出现的旁路调用。

## 范围

- `.github/workflows/lint.yml`（新增或改）
- 或 `scripts/ci/lint_dispatch.sh`（bash + ripgrep）
- 根据团队现状可二选一

## 前置 Checklist

- [x] 确认 CI 当前用 GitHub Actions / Gitea Actions / 本地 pre-commit 中的哪一种
- [x] 在 PR-10 合并前先合本 PR（否则会立刻把现有代码标红）→ 方案：加 `allowlist` 把现有命中点全列进去，PR-11/12/13 完成后删

## 实施 Checklist

- [x] 写 lint 脚本 `scripts/ci/lint_dispatch.sh`
- [x] CI workflow 中加 job `lint-dispatch` 调用该脚本
- [x] 在 `docs/roadmap/tickets/PR-11-*.md` / `PR-12-*.md` / `PR-13-*.md` 的"文档 checklist"里提醒：合并后要删 ALLOWLIST 对应行

## 测试 Checklist

- [x] 故意在 `scripts/` 下新增一个违规字符串文件 → CI red
- [x] 删除该违规文件 → CI green
- [x] 现有代码在 allowlist 保护下通过

## 文档 Checklist

- [x] 在 [message-wake-refactor.md](../message-wake-refactor.md) M0-5 条目 → `[x]`
- [x] 本工单 Status → `[x]`

## 验收命令

```bash
# 本地模拟
./scripts/ci/lint_dispatch.sh
# 制造违规
echo 'httpx.post("/api/queue/dispatch")' > /tmp/test_violation.py
rg -l "/api/queue/dispatch" /tmp/test_violation.py
# 预期 CI 会 fail
```

## 回滚

`git revert` — 仅约束脚本，不影响功能。

## 备注

- 如果 CI 链路复杂，起步阶段可把脚本放 `pre-commit` + `CI` 双保险。
- allowlist 是临时口袋；PR-18/19 合并后 business/runtime 里应当清零。
