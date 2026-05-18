# Business/subscriber boundary verification sweep result

## Summary

Completed the final Business/subscriber boundary verification sweep. Focused scans now show remaining Gateway/product CRUD and Subscriber/Cortex/session hits are current negative statements, explicit historical notes, test guard strings, or owning-service API docs. Relevant Business tests and lifecycle/config/docs lints pass.

## Done

- Scanned active docs/scripts/Business code for stale Gateway product CRUD, Gateway SqlEntityStore, Gateway-owned subagent, and `[Gateway] Created SUBAGENT_SEND` wording.
- Scanned active docs/scripts/Business code for Subscriber wake/session/Cortex ownership, forbidden `scope/append_input`/`subscriber_append_input`, and Business Queue/TaskManager ownership claims.
- Scanned Business/subscriber code and tests for aggregation env/config references.
- Ran focused Business guard tests and architecture/lifecycle/start config lints.
- Classified remaining scan hits:
  - Current negative/boundary statements: `docs/gateway/rest-auth-and-deps.md`, `docs/gateway/internal-and-workers.md`, `docs/gateway-architecture.md`, `docs/runtime-architecture.md`, `docs/entangled-architecture.md`, `docs/entangled/gateway-integration.md`, `docs/architecture/entangled-store-and-app-ws.md`.
  - Explicit historical notes: `docs/gateway/entangled-hooks.md`, `docs/entangled-architecture.md` old-architecture paragraphs.
  - Guard-test forbidden strings: `novaic-business/tests/test_pr153_lifecycle_guardrails.py`, `novaic-business/tests/test_pr117_task_proxy_removed.py`, `scripts/ci/lint_lifecycle_loop_ownership.sh`.
  - Owning-service Cortex API docs: `docs/cortex-architecture.md`, `docs/cortex/context-event-source.md`, `docs/cortex/internal-api-schemas.md`, `docs/cortex/http-api.md`.
  - Aggregation env references: production entrypoint config load and explicit parser in `dispatch_subscriber.py`; test monkeypatches are expected coverage.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider novaic-business/tests/test_im_aggregation.py novaic-business/tests/test_pr153_lifecycle_guardrails.py novaic-business/tests/test_pr117_task_proxy_removed.py` passed: `26 passed in 0.51s`.
- `python3 scripts/ci/lint_docs_status_consistency.py` passed.
- `bash scripts/ci/lint_lifecycle_loop_ownership.sh` passed: `LIFECYCLE_LOOP_OWNERSHIP_LINT=PASS`.
- `python3 scripts/ci/check_start_config_contract.py` passed: `start_config_contract OK`.
- Focused `rg` scans were run for Gateway CRUD/product entity residues, Subscriber wake/session/Cortex ownership, Business Queue/Runtime ownership, and aggregation env/config references.

## Known Gaps

- No active unexamined Business/subscriber stale claim was found in the swept surfaces.
- Historical roadmap/ticket directories were intentionally excluded from active cleanup scans; they remain archival evidence rather than current implementation guidance.
- Nested repos contain broader pre-existing dirty changes outside this Business/subscriber sweep; they were not reverted.

## Artifacts

- Scan command categories: Gateway CRUD/product entity, Subscriber lifecycle/Cortex ownership, aggregation env/config.
- Test/lint commands: Business focused pytest set, docs status consistency, lifecycle loop ownership lint, start config contract check.
