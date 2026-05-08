# P005 Result - 审计测试 CI 部署守卫覆盖

## Scope

审计当前测试矩阵、CI lint、启动脚本、部署脚本是否守住 FSM substrate + business DSL 架构边界。

## Evidence Read

- `.github/workflows/lint.yml`
  - 运行多个架构 lint：dispatch、httpx、internal async、lifecycle、scope phase、legacy columns、wake continuity、Cortex boundary、retired services、agent loop path、docs residue、deploy fresh smoke、runtime worker supervision、start/config contract、retired agent paths、lifecycle loop ownership。
  - 当前 workflow 没有运行 `scripts/run_all_tests.sh` 或 `novaic-agent-runtime` pytest。
- `scripts/ci/lint_runtime_worker_supervision.py`
  - 明确要求 `scripts/start.sh`、`deploy`、`docs/runbooks/deploy.md`、`.github/workflows/lint.yml` 包含 role-level worker supervision。
  - role markers 覆盖 task-worker control/execution、saga-worker、session-outbox-worker、saga-outbox-worker、health、scheduler、subscriber。
- `scripts/ci/lint_deploy_fresh_smoke.py`
  - 要求 deploy 使用 timestamp-aware smoke boundary，检查关键日志是否新鲜。
- `scripts/ci/check_start_config_contract.py`
  - 守住 strict_config、retired deploy files、runtime_switches allowlist、retired text。
- `scripts/start.sh` / `deploy` / `novaic-app/scripts/start-backends.sh`
  - 当前启动 roster 已包含 task/saga/session-outbox/saga-outbox/health/scheduler。
- `scripts/run_all_tests.sh`
  - 作为全仓 Python 测试矩阵存在，覆盖 root guards、agent-runtime、business、common、cortex、blob-service、llm-factory。

## Verification Run

Root lint/deploy guard：

```bash
python3 scripts/ci/lint_runtime_worker_supervision.py
python3 scripts/ci/lint_deploy_fresh_smoke.py
python3 scripts/ci/check_start_config_contract.py
bash -n scripts/start.sh
bash -n deploy
bash -n novaic-app/scripts/start-backends.sh
python3 -m compileall -q novaic-agent-runtime/main_novaic.py novaic-agent-runtime/task_queue/workers novaic-agent-runtime/queue_service scripts/ci
```

结果：

- `lint_runtime_worker_supervision OK`
- `lint_deploy_fresh_smoke OK`
- `start_config_contract OK`
- shell syntax / compileall 均通过。

全仓测试矩阵：

```bash
./scripts/run_all_tests.sh
```

结果：

- root-ci-guards: 3 passed
- agent-runtime: 530 passed
- business: 176 passed
- common: 140 passed
- cortex: 352 passed
- blob-service: 28 passed, 2 skipped
- llm-factory: 8 passed
- SUMMARY: Failed 0

## Conclusion

本地测试和架构守卫当前非常强，能覆盖大部分“新代码没接入、旧路径回流、worker roster 漂移、部署日志旧烟雾”的复发风险。启动/部署脚本也已包含新 worker roster。

## Remaining Gaps

- CI lint workflow 没有直接运行 `scripts/run_all_tests.sh`。本地全仓测试矩阵是绿的，但还不是 GitHub workflow 的强制门禁。
- worker role roster 在 `scripts/start.sh`、`deploy`、`lint_runtime_worker_supervision.py`、docs 中重复表达。lint 能防漂移，但 SSOT 还不是单一数据结构。
- 本票没有执行真实远端部署，只验证了 deploy/start/fresh-smoke 的本地脚本守卫和语法。真实部署状态需要单独部署/远端 smoke。
