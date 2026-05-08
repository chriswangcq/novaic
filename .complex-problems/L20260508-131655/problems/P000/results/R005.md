# P000 Result - 全面审核当前代码与 FSM 基建 + 业务 DSL 的 gap

## Scope

本次审计覆盖当前代码和设计目标之间的 gap：

- FSM substrate 与状态机接入
- 业务 DSL 与 worker assembly 厚度
- 显式依赖边界与 side-effect adapter
- 旧路径残留与兼容分支
- 测试、CI、部署守卫覆盖

## Completed Audits

- P001: FSM substrate 与状态机接入
  - Generic FSM substrate 已是活路径。
  - Session/Task/Saga 均已接入 pure decision + ledger/state/outbox。
  - Wake creation 已切到 durable session outbox。
  - 57 个相关测试通过。
- P002: 业务 DSL 与 worker assembly 厚度
  - worker lifecycle 已统一到 generic worker substrate。
  - raw worker constructors 只在 `assembly_helpers.py`。
  - business handlers 已薄化为 typed boundary。
  - 66 个 worker/assembly/action-engine 测试通过。
- P003: 显式依赖边界与 side-effect adapter
  - Queue/Runtime 主路径的 clock/id/client/effect executor 边界清晰。
  - concrete IO 集中在 outbox dispatcher 和 effect adapters。
  - HTTP direct constructor lint 和 18 个相关测试通过。
- P004: 旧路径残留与兼容分支
  - Queue FSM/session/worker 活旧路径未发现。
  - retired worker entrypoint/watchdog/shadow/old table 有 guard。
  - 31 个 residue tests 和多个 docs/runtime lints 通过。
- P005: 测试 CI 部署守卫覆盖
  - runtime worker supervision、deploy fresh smoke、start config contract 守卫存在并通过。
  - `./scripts/run_all_tests.sh` 全绿：root 3、agent-runtime 530、business 176、common 140、cortex 352、blob-service 28 passed/2 skipped、llm-factory 8。

## Current Shape

当前系统不是旧 imperative harness 了。更准确地说：

- Queue session/task/saga 已经是 ledger-backed FSM coordinator。
- Worker lifecycle 已经是 component-level generic worker substrate。
- Business handler 不再拥有 loop/client/runtime 构造；业务计算被放到 handler/engine，side effects 通过 adapters。
- Start/deploy 已经知道新 worker roster：task-worker、saga-worker、session-outbox-worker、saga-outbox-worker、health、scheduler。

## Gaps Against Ideal Form

### Gap 1 - 还不是单一 Generic FSM Runner

`fsm/core.py` 和 `fsm/sqlite_store.py` 是 substrate，但 Session/Task/Saga repo 仍分别手写 transition recording、projection apply、claim candidate SQL、post-transaction publish 等 adapter 流程。

理想形态：每个 machine 提供 machine spec/reducer/effect spec，runner 统一处理 event append、state transition、outbox append、projection hook。

### Gap 2 - 业务还不是“几行 DSL”

`worker_assemblies.py` 仍 557 行，`task_execution.py` 仍 432 行，`scheduled_wake.py` 仍 218 行。虽然它们已经从 worker loop 中剥离，但仍是 Python imperative wiring/action engine，不是极薄 declarative DSL。

理想形态：worker role spec、effect binding spec、action decision spec 可声明，assembly/runner 自动装配。

### Gap 3 - Cortex registry 的依赖边界还不够极致

`WorkspaceRegistry.__init__()` 默认 `BlobPayloadPolicy.from_env()` 和 `clock or time.time`。这是 composition-ish code，不在 Queue FSM 主路径，但不符合最严格显式依赖边界。

理想形态：`main_cortex.py` 在 startup boundary 解析 env/policy/clock 并显式传给 registry；registry 只接受对象，不自行读 env/time。

### Gap 4 - 命名/注释仍有旧词汇

`list_active_sessions()`、`rebuild_active_sessions_from_sagas()` 等名字仍沿用 active session 旧词汇；active code 注释仍有少量 retired 说明。不是活旧逻辑，但会造成认知残留。

理想形态：命名完全反映 `session_state`/projection/rebuild semantics，历史解释移动到 docs/tickets，不留在热路径文件。

### Gap 5 - 全仓 transitional allowlist 仍在

`scripts/ci/lint_httpx.sh` 仍含 `TRANSITIONAL` allowlist，允许 business/provider 和 llm-factory routes/providers 里的 direct httpx constructor。

理想形态：删除 transitional allowlist，统一 HTTP client substrate。

### Gap 6 - 测试矩阵没有进入 GitHub 强制门禁

`scripts/run_all_tests.sh` 存在且本地全绿，但 `.github/workflows/lint.yml` 没有运行它或等价 pytest matrix。

理想形态：CI 至少运行 Runtime/Core FSM/worker targeted tests；最好运行 full backend matrix 或拆分并行 job。

### Gap 7 - Worker roster 还不是单一 SSOT

worker role roster 同时存在于 `scripts/start.sh`、`deploy`、`lint_runtime_worker_supervision.py`、docs 中。lint 能防漂移，但不是单一 machine-readable spec。

理想形态：一个 `runtime_workers.json/yaml` 或 Python spec 生成/校验 start/deploy/docs。

## Verification Summary

- FSM targeted tests: 57 passed.
- Worker/DSL targeted tests: 66 passed.
- Dependency/effect targeted tests: 18 passed.
- Residue guard tests: 31 passed.
- Full backend matrix: 1237 passed, 2 skipped.
- Root deploy/start/CI guard scripts passed.

## Recommendation

下一轮如果要继续向“完美形态”推进，优先级建议：

1. P1: Generic FSM Runner 统一 Session/Task/Saga transition/outbox/projection adapter。
2. P2: Worker role/effect/action declarative DSL，收薄 `worker_assemblies.py` 和 action engines。
3. P3: Cortex registry 显式依赖边界收口。
4. P4: 删除/重命名旧词汇与 transitional HTTP allowlist。
5. P5: 把测试矩阵纳入 CI，并抽 worker roster SSOT。
