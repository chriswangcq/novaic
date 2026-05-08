# P004 Ticket - 审计旧路径残留与兼容分支

## Problem Definition

审计当前代码是否仍存在旧 FSM/session/worker 路径残留、兼容分支、shadow 双写、旧 entrypoint、旧表、旧脚本、旧文档状态误导。

## Proposed Solution

只读搜索并分类：

- `legacy|compat|deprecated|fallback|shadow|retired`
- `tq_active_sessions`
- retired worker names / watchdog / old main scripts
- direct old active session vocabulary
- feature flag / allowlist / transitional wording

运行已有 residue guard lint/tests。

## Acceptance Criteria

- 分清“活旧路径”、“守卫测试命中”、“命名残留”、“文档历史残留”。
- 说明是否有旧代码还在执行。
- 说明是否仍有兼容分支需要物理删除。
- 验证 residue guard 是否通过。

## Verification Plan

- `rg` 搜索。
- 读取 residue guard tests/lint scripts。
- 运行相关 tests/lints。

## Risks

- 搜索词会命中测试和文档，必须分类，不可直接当作活代码问题。

## Assumptions

- 本票只审计，不改代码。
