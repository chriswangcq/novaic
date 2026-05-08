# P004 Check - 旧路径残留与兼容分支

## Status

success

## Summary

P004 的旧路径残留审计完成。Queue FSM/session/worker 的活旧逻辑已经清干净，剩余主要是命名/注释/全仓 lint allowlist 级别的残留。

## Evidence

- active Runtime source 搜索没有发现旧表、shadow 双写、legacy/compat/fallback 活路径。
- 31 个 residue/cutover guard tests 通过。
- retired service / agent main path / wake continuity / docs archaeology lint 通过。

## Criteria Map

- 活旧路径：未发现。
- 守卫测试命中：已分类为 guard，不是活代码。
- 命名残留：`active_sessions` 词汇仍在诊断/重建命名中。
- 文档历史残留：roadmap archaeology 已被 lint fenced。
- 兼容分支：Queue FSM path 无；全仓 HTTP lint 仍有 transitional allowlist。

## Execution Map

- `rg` 搜索 active source + scripts/deploy/docs。
- 读取 residue guard tests。
- 运行 targeted residue tests/lints。

## Stress Test

对巨大 grep 输出做了二次收窄：先全仓搜索，再限定 active Runtime source，避免把历史文档/测试守卫误判成活路径。

## Residual Risk

如果追求“物理极致”，下一步应重命名 active-session 旧词汇、收窄 retired 注释、删除或拆票清理全仓 `TRANSITIONAL` allowlist。
