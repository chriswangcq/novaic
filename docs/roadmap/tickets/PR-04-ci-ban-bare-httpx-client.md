# PR-04  CI lint：禁止业务代码裸 `httpx.Client()` / `httpx.AsyncClient()`

| 字段 | 值 |
| --- | --- |
| **Phase** | M0 |
| **Milestone** | M1（前置） |
| **承诺** | R7 |
| **Status** | `[x]` |
| **Depends on** | — |
| **Blocks** | — |
| **估时** | 1 h |
| **Owner** | __ |
| **PR 标题** | `ci: ban bare httpx.Client() in service code` |

## 目标

强制所有内部 HTTP 调用走 `common.http.clients.internal_client(service_name=...)`，避免再出现没带 `X-Internal-Key` 的 401 盲区（hihi 事件根因之一）。

## 范围

- `scripts/ci/lint_httpx.sh` + CI workflow

## 前置 Checklist

- [x] 先 grep 现有命中 `rg 'httpx\.(Async)?Client\(' novaic-*/`，整理成 allowlist（老代码不阻断合并）

## 实施 Checklist

- [x] 写 lint：
  ```bash
  #!/usr/bin/env bash
  set -e
  PATTERN='httpx\.(Async)?Client\('
  ALLOWLIST=(
    'novaic-common/common/http/clients.py'
    'tests/'
    # TRANSITIONAL — remove line-by-line as PRs migrate:
    # (此处列出老点，合 PR 后逐步删)
  )
  # 复用 PR-03 的逻辑，模板相同
  ```
- [x] 把现有命中全部列入 transitional allowlist
- [x] 约定：每次有 PR 把某处 `httpx.Client()` 改成 `internal_client(...)` 时，**必须在同 PR 里从 allowlist 删除对应行**

## 测试 Checklist

- [x] 新增违规 → CI red
- [x] allowlist 保护下现有代码通过

## 文档 Checklist

- [x] [message-wake-refactor.md](../message-wake-refactor.md) M0-6 → `[x]`
- [x] 本工单 Status → `[x]`

## 验收命令

```bash
./scripts/ci/lint_httpx.sh
# 新加违规点应报错
```

## 回滚

`git revert` — 仅约束脚本。

## 备注

- 与 PR-03 可以合成同一个 "CI policy" PR，但拆开更清晰。
- 每次清理一个 allowlist 项都是一次"技术债还款"的可见度。
