# P004 Result - 审计旧路径残留与兼容分支

## Scope

审计 Queue/Runtime worker/FSM 相关旧路径、兼容分支、shadow 双写、retired worker entrypoint、旧表和文档/脚本残留。

## Active Runtime Search

在 active runtime source 中搜索：

```bash
rg -n "legacy|compat|deprecated|fallback|shadow|retired|TRANSITIONAL|tq_active_sessions|watchdog|main_task|main_saga|WorkerSync|gateway-url|active_sessions" \
  novaic-agent-runtime/queue_service \
  novaic-agent-runtime/task_queue -g '*.py'
```

命中分类：

- `queue_service/routes.py` / `session_repo.py` / `session_rebuild.py`
  - `list_active_sessions()`、`rebuild_active_sessions_from_sagas()` 命名残留。
  - 这些读取的是 `session_ledger.list_active_states()`，不是 `tq_active_sessions` 旧表。
- `task_queue/handlers/runtime_handlers.py`
  - 注释说明 PR-69 已退休 old prompt splice continuity。
  - 这是解释性注释，不是兼容分支。
- `queue_service/main.py`
  - 注释提到 deprecated FastAPI startup hook replacement。
  - 与旧 session/FSM path 无关。
- `task_queue/sagas/react_actions.py`
  - 注释中提到 watchdogs and log readers；不是旧 watchdog process。

未发现：

- active source 中无 `tq_active_sessions` 活表引用。
- active source 中无 `shadow:` / `shadow_` 双写。
- active source 中无 `legacy|compat|fallback|enable_fsm|disable_fsm` 的 Queue coordinator 活路径。
- retired `main_task.py` / `main_saga.py` 不存在。

## Scripts / Deploy Search

`scripts/start.sh`、`deploy`、`novaic-app/scripts/start-backends.sh` 已启动：

- `task-worker`
- `saga-worker`
- `session-outbox-worker`
- `saga-outbox-worker`
- `health`
- `scheduler`

`watchdog`/`main_task.py`/`main_saga.py` 没有作为启动角色出现。

`--gateway-url` 在 Business/Device startup 中仍存在，但这是当前服务参数，不是 Runtime worker retired path。

## Guard Tests / Lints

在 `novaic-agent-runtime` 执行：

```bash
pytest -q \
  tests/test_pr255_legacy_compat_cleanup.py \
  tests/test_pr260_session_harness_generic_fsm_cutover.py \
  tests/test_pr315_queue_fsm_final_residue_guard.py \
  tests/test_pr335_worker_residue_guards.py \
  tests/test_pr338_business_handlers_lifecycle_free.py \
  tests/test_pr257_remove_active_sessions_table.py \
  tests/test_pr244_remove_pending_triggers.py
```

结果：`31 passed in 0.49s`。

在 root 执行：

```bash
bash scripts/ci/lint_retired_service_residue.sh
bash scripts/ci/lint_agent_main_path_acceptance.sh
bash scripts/ci/lint_retired_agent_paths.sh
bash scripts/ci/lint_wake_continuity_contract.sh
bash scripts/ci/lint_current_docs_residue.sh
python3 scripts/ci/lint_roadmap_ticket_archaeology.py
python3 scripts/ci/lint_docs_status_consistency.py
```

结果：相关 lint 均通过。

## Conclusion

Queue FSM/session/worker 相关旧活路径已经清理干净：旧表、shadow 双写、direct wake create、retired worker loop/entrypoint、watchdog process 均没有活路径。

## Remaining Gaps

- 命名残留：`list_active_sessions()` / `rebuild_active_sessions_from_sagas()` 仍以旧 active-session 词汇表达新 projection/diagnostic 行为。不是活旧逻辑，但影响认知。
- 解释性注释仍提到 retired prompt splice。它帮助历史理解，但从“物理极致清理”角度可继续收窄。
- `scripts/ci/lint_httpx.sh` 仍有 `TRANSITIONAL` allowlist，且允许 `novaic-business/business/provider_client.py`、`novaic-llm-factory/factory/routes/config_routes.py`、`novaic-llm-factory/factory/providers.py`。这不是 Queue FSM 路径，但属于全仓兼容/过渡残留。
