# Phase 5D Static Guards And Broad Verification

## Problem Definition

Phase 5 cleanup is not durable until broad static guards and test suites prove the removed local-authority paths cannot silently return. This phase must check both residue patterns and behavior around Cortex state authority.

## Proposed Solution

Run a final verification pass and add/tighten guards only if the audit exposes missing coverage:

- Static audits for forbidden authority residues:
  - transition log authority
  - active-stack file walking
  - temp sandbox backing-path authority
  - process-local/in-process fallback authority
  - obsolete compatibility API phrases
- Targeted tests around the touched Cortex areas:
  - operational SQLite store/projections
  - active stack/scope lifecycle
  - payload manifest
  - step formatted projection API
  - scope lock fail-closed behavior where covered
- Full `novaic-cortex/tests`.
- Cortex module `py_compile`.
- Record any remaining historical-only hits.

## Acceptance Criteria

- Static audits are recorded with command output classification.
- Targeted Cortex tests around changed areas pass.
- Full `novaic-cortex/tests` passes.
- Cortex module py_compile passes.
- Any remaining residue hits are explicitly historical/test-only/negative-guard/low-level internals, not current authority paths.
- If any guard is missing, add the smallest durable test/static guard and rerun relevant verification.

## Verification Plan

```bash
rg -n "scope_state_log|register_scope_id|get_scope_id_index|meta\\.scope_ids|_walk_scope_tree|format_for_llm|include_display|_SKILL_LOCKS|_SCOPE_LOCKS|novaic-cortex-sandbox-|fallback authority|local authority" docs/cortex docs/architecture novaic-cortex novaic-agent-runtime -S
python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)
pytest -q novaic-cortex/tests
```

Run narrower targeted tests first if full suite failures need localization.

## Risks

- Broad tests may take time; failures must be triaged instead of waved away.
- Static searches may find intentional historical terms; classify them with evidence.
- If a missing guard is discovered, this phase may need a follow-up or split rather than pretending broad verification is enough.

## Assumptions

- Behavior-changing cleanup phases are already completed; Phase 5D is verification/guard hardening unless it discovers a small missing guard.
