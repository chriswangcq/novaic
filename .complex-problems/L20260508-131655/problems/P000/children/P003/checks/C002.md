# P003 Check - 显式依赖边界与 side-effect adapter

## Status

success

## Summary

P003 的审计完成。Runtime/Queue 主路径的显式依赖边界和 side-effect adapter 已经成立；发现的主要 gap 在 Cortex registry 的 env/default clock 注入还不够极致显式。

## Evidence

- `QueueServiceDependencies.system()` / `WorkerRuntimeDependencies.system()` 是显式边界 factory。
- Session/Task/Saga constructors 接收 clock/id providers。
- Worker action engines 使用 effect executor；concrete IO 在 `*_effects.py`。
- HTTP direct constructor lint 通过。
- 18 个依赖/effect/action projection 相关测试通过。

## Criteria Map

- 隐藏输入搜索：已覆盖 env/time/uuid/httpx。
- side-effect 集中性：已覆盖 worker effect adapters 和 session outbox dispatcher。
- 识别可接受边界 factory：已区分 system factory 与业务路径。
- 标出不够极致的边界 gap：Cortex registry。

## Execution Map

- `rg` 搜索隐藏输入。
- 读取 dependencies、effects、Cortex blob/registry/lock 相关文件。
- 运行 `lint_httpx.sh`、`check_no_internal_async.py` 和 targeted tests。

## Stress Test

没有把所有 `uuid/time/env` 一概判错；按“是否在业务 decision 主路径、是否有注入边界、是否是 adapter 内部实现”分类。

## Residual Risk

Cortex registry 仍应进一步收紧，把 env policy/default clock 迁移到 startup composition root；否则未来类似隐式 env 可能再从 registry 构造器扩散。
