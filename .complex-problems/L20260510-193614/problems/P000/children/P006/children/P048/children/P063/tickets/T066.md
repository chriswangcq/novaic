# Phase 5D.3 targeted Cortex state authority test gate

## Problem Definition

`P063` must run the focused Cortex state-authority test gate across the remediation chain before the full suite: operational SQLite store/projections, scope lifecycle, active stack, payload manifest, step formatted projection behavior, sandbox path contract, and scope lock fail-closed behavior.

## Proposed Solution

- Build one explicit targeted pytest command with sibling package `PYTHONPATH` so the test environment matches the split repository layout.
- Include tests touched or depended on by Phase 4, Phase 5B, Phase 5C, and Phase 5D.2.
- Run the targeted command, record exact pass/fail output, and triage any failure inside the result body.
- Do not broaden to the full Cortex suite here; that belongs to `P064`.

## Acceptance Criteria

- Operational store, scope projection, active stack, scope lifecycle, and status/read routing tests are included.
- Payload manifest, step formatted projection, step output projection, sandbox path, and scope lock/fallback guard tests are included.
- The targeted test command passes, or failures are recorded with concrete triage.
- The result records the exact command and output summary.

## Verification Plan

```bash
PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q \
  novaic-cortex/tests/test_operational_store.py \
  novaic-cortex/tests/test_active_stack_projection.py \
  novaic-cortex/tests/test_context_event_api_skill_lifecycle.py \
  novaic-cortex/tests/test_context_event_read_source_guards.py \
  novaic-cortex/tests/test_context_event_no_compat.py \
  novaic-cortex/tests/test_context_event_api_steps_write.py \
  novaic-cortex/tests/test_tool_output_projection.py \
  novaic-cortex/tests/test_step_result_projection.py \
  novaic-cortex/tests/test_resolve_for_llm.py \
  novaic-cortex/tests/test_sandbox_requires_mount_namespace.py \
  novaic-cortex/tests/test_sandboxd_wiring.py \
  novaic-cortex/tests/test_tool_schemas_limits.py \
  novaic-cortex/tests/test_lock_and_compat_boundary_guards.py
```

## Risks

- The targeted gate may miss unrelated regressions; `P064` owns full-suite coverage.
- Duplicate coverage is acceptable here because this gate is intended to aggregate state-authority surfaces into one failure-localizing command.

## Assumptions

- The split repository layout requires explicit `PYTHONPATH` for `novaic-logicalfs` and `novaic-sandbox-sdk`.
