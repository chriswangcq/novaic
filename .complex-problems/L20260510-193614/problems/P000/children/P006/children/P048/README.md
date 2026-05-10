# Phase 5D Static Guards And Broad Verification

## Problem

Cleanup is only durable if regressions are guarded. After deleting or rewriting residues, the repo needs static/targeted checks that catch reintroduced old authority patterns and a broad verification pass proving cleanup did not break Cortex behavior.

## Success Criteria

- Add or tighten tests/static guards for forbidden local authority patterns where appropriate.
- Run static `rg` audits for transition-log authority, active-stack file walking, temp backing-path authority, process-local fallback, and obsolete compatibility phrases.
- Run targeted Cortex tests around changed areas.
- Run full `novaic-cortex/tests`.
- Run Cortex module `py_compile`.
- Record any remaining historical-only hits explicitly.
