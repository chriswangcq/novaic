# Business/subscriber cleanup candidate disposition result

## Summary

Completed the candidate disposition pass. The main active stale documentation is concentrated in `docs/entangled-architecture.md` and `docs/gateway/rest-auth-and-deps.md`; Business/subscriber production code is already mostly aligned with explicit dependency boundaries for IM aggregation and notification drain ownership. Remediation should patch the active docs in P718 and retain current/historical/test-only references with evidence.

## Done

- Reviewed P715 artifacts and sampled current source/docs with focused `rg`, `nl`, and `sed` reads.
- Classified `docs/entangled-architecture.md` lines 15, 47, and 51 as active stale/ambiguous wording that should be patched by P718.
- Classified `docs/gateway/rest-auth-and-deps.md` lines 6-9 as stale/ambiguous Gateway CRUD wording that should be patched by P718.
- Classified current Business/subscriber code as already clean for the specific aggregation hidden-input concern: env parsing happens at the entrypoint boundary and `_group_for_aggregation` consumes `self.aggregation_config`.
- Classified subscriber wake/session ownership text as current and explicit: subscriber only drains Environment notifications into Queue and does not mutate Cortex scope input ownership.
- Classified roadmap/ticket references as historical unless the same claim appears in active architecture docs.

## Verification

- Read `docs/entangled-architecture.md:1-108`; found contradictory Gateway/Business/Entangled ownership wording at lines 15, 47, and 51.
- Read `docs/gateway/rest-auth-and-deps.md:1-25`; found old Gateway REST CRUD wording at lines 6-9.
- Read `docs/gateway/internal-and-workers.md:1-31`, `docs/gateway/entangled-hooks.md:1-34`, `docs/entangled/gateway-integration.md:1-31`, and `docs/architecture/gateway-v2-target-architecture.md:1-68`; these describe the current boundary clearly and should be retained.
- Read `novaic-business/main_subscriber.py:85-142`; `os.environ` is read once at process entry via `load_im_aggregation_config_from_env(os.environ)` and injected into `DispatchSubscriber`.
- Read `novaic-business/business/subscribers/dispatch_subscriber.py:99-129`, `280-315`, and `487-516`; aggregation config is a dataclass value and grouping logic uses `self.aggregation_config`, not dynamic env reads.
- Focused scans confirmed active guard tests exist for lifecycle boundaries, including `novaic-business/tests/test_pr153_lifecycle_guardrails.py` and `novaic-business/tests/test_pr117_task_proxy_removed.py`.

## Known Gaps

- P718 still needs to patch stale active docs in `docs/entangled-architecture.md` and `docs/gateway/rest-auth-and-deps.md`.
- P719 still needs to run code-boundary tests/scans and patch code only if deeper evidence contradicts this disposition.
- P720 still needs the final focused verification sweep after remediation.

## Artifacts

- P715 scan artifacts: `.complex-problems/L20260516-222011/tmp/p715/business-scan.txt`, `launch-doc-scan.txt`, and `env-config-scan.txt`.
- Current read evidence: `docs/entangled-architecture.md:15`, `docs/entangled-architecture.md:47`, `docs/entangled-architecture.md:51`, `docs/gateway/rest-auth-and-deps.md:6-9`, `novaic-business/main_subscriber.py:137-140`, `novaic-business/business/subscribers/dispatch_subscriber.py:511-516`.
