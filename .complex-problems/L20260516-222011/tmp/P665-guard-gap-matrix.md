# P665 Guard Gap Matrix

| Contract | Root CI/static guard | Module guard tests | Status | Notes / next action |
| --- | --- | --- | --- | --- |
| Blob is byte store; LogicalFS/workspace is live `/ro` `/rw` authority | `scripts/ci/lint_blob_workspace_boundary.py` via `.github/workflows/lint.yml` | `novaic-cortex/tests/test_blob_boundary_guard.py`, `cortex_tests/blob_boundary_policy.py`, `novaic-logicalfs/tests/test_blob_store.py` | Covered | Root guard scans live runtime source roots; module tests own policy details. |
| Sandbox service must not own Cortex/Blob/LogicalFS/workspace identity semantics | `scripts/ci/lint_blob_workspace_boundary.py` includes `novaic-sandbox-service/sandbox_service` | `novaic-sandbox-service/tests/test_sandbox_boundary.py` | Covered | Sandbox boundary tests reject imports/terms such as Cortex/Blob/LogicalFS, agent/user/scope/subagent, `/ro`, `/rw`. |
| Cortex owns state semantics/context, no legacy DFS fallback | `scripts/ci/lint_cortex_boundary.sh` | `novaic-cortex/tests/test_context_event_no_compat.py`, `test_context_event_read_source_guards.py`, `test_context_event_api_contract.py` | Covered | Event-stream read source guards protect the recent context-source model. |
| Shell visible output is bounded terminal text; artifacts stay manifest/Blob refs | No broad root guard; protected by focused tests | `novaic-agent-runtime/tests/unit/task_queue/test_shell_output_contract.py`, `novaic-cortex/tests/test_shell_capabilities_blob_contract.py`, `novaic-cortex/tests/test_tool_output_projection.py` | Covered-by-tests | Static root guard would be noisy; tests verify executable behavior. |
| `display` is explicit perception path; history/current context must not inline image bytes | No broad root guard; protected by focused runtime/Cortex tests | `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`, `test_tool_handlers_display_chat_history.py`, `novaic-cortex/tests/test_tool_output_projection.py` | Covered-by-tests | Tests cover current-round image projection and history replay text/image-ref behavior. |
| Queue/Runtime session state via FSM/outbox, no active-session/legacy dual path | `scripts/ci/lint_retired_runtime_vocabulary.py`, lifecycle lints | Many PR-25x/26x/27x/31x runtime guard tests, including `test_pr315_queue_fsm_final_residue_guard.py`, `test_pr323_generic_worker_contracts.py` | Covered | Root vocabulary guard plus runtime source assertions. |
| Message lifecycle ownership: subscriber does not mutate Cortex input lifecycle | `scripts/ci/lint_lifecycle_loop_ownership.sh`, `lint_chat_messages_read.sh` | Business/runtime lifecycle guard tests | Covered | Static lint encodes subscriber/runtime ownership boundary. |
| Deploy/service topology stays fresh and retired packages removed | `scripts/ci/lint_deploy_fresh_smoke.py`, runtime worker supervision lint | Runtime path/service tests | Covered | Fresh-smoke lint checks `novaic-logicalfs`, `sandboxd.log`, and retired `novaic-sandbox-core` removal. |
| Generated artifacts must not remain in active source/resource trees | `scripts/ci/lint_generated_artifacts.sh` via workflow | N/A | Needs-fix | Current workspace contains many `__pycache__`, `.pytest_cache`, `.pyc` artifacts. Guard exists but currently fails in this dirty tree; P666 must physically clean generated artifacts and re-run with `pipefail`. |
| Retired file-service/storage hot paths stay removed | `scripts/ci/test_no_legacy_file_hot_paths.py` | Common resource ref/tool definition tests | Covered | Pytest-style root guard covers active runtime code. |
| Docs/current-status claims do not regress into stale active docs | `lint_current_docs_residue.sh`, `lint_docs_status_consistency.py`, `lint_roadmap_ticket_archaeology.py` | N/A | Covered | P659 also patched stale current-facing docs. |

## Concrete gaps

1. Generated Python/test artifacts are physically present across active source/resource trees. The guard exists, but the tree is not clean. This matches the user's principle that residual generated files mislead AI/code scans and should be physically removed.

## No-change decisions

- No new root static guard for shell/display base64 projection: behavior is dynamic and already covered by focused tests; a broad static ban on `base64` or `_mcp_content` would false-positive valid tests and lower-layer code.
- No new root static guard for `/rw/scratch`: lower-layer LogicalFS tests validly use arbitrary logical paths; Cortex/shell subagent scratch contract is better protected by specific docs/tests and not by a broad string ban.
