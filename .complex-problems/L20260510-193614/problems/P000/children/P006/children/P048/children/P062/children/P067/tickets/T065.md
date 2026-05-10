# Phase 5D.2c lock and fallback guard audit

## Problem Definition

`P067` must prove that the remaining lock/fallback boundaries are guarded: Cortex must fail closed without the production scope lock backend, process memory must not be documented or tested as authority, and removed compatibility paths such as `format_for_llm` and `scope_state_log` must stay removed.

## Proposed Solution

- Search current Cortex/runtime source, docs, and tests for scope lock backend installation, fail-closed behavior, `format_for_llm`, `scope_state_log`, and fallback wording.
- Inspect existing lock-related tests and startup code to classify coverage.
- Add the smallest missing static or behavioral guard tests if any boundary is only implied by code or docs.
- Run the relevant guard tests and static searches, then record the coverage map.

## Acceptance Criteria

- Redis/production scope lock fail-closed behavior is mapped to tests or startup/static evidence.
- Removed public compatibility wrappers (`format_for_llm`) are guarded by tests or static checks.
- Removed `scope_state_log` authority path is guarded by tests or static checks.
- Any remaining process-memory-only lock manager usage is explicitly classified as test-only or non-authoritative.
- Relevant tests/static searches pass.

## Verification Plan

```bash
rg -n "RedisScopeLockManager|install_redis_backend|get_lock_manager|in-memory-test|format_for_llm|scope_state_log|fallback|fail closed|scope-lock" novaic-cortex/tests novaic-cortex/novaic_cortex novaic-agent-runtime/tests -S --glob '!**/__pycache__/**'
PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q <lock-and-compat-guard-tests>
```

## Risks

- Some fallback wording may be historical docs rather than live contract; execution must classify it instead of blindly deleting archived rationale.
- Redis fail-closed behavior may live in startup paths rather than ordinary unit tests; if so, add a narrow test around the startup/installer boundary.

## Assumptions

- This ticket does not migrate the lock implementation; it verifies and tightens the current boundary guards.
- Historical docs can retain old terms only if clearly historical and excluded from current contract gates.
