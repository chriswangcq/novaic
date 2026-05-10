# Remove Residual Local State Authority And Compatibility Paths

## Problem Definition

Phase 1-4 moved Cortex state authority toward SQLite/LogicalFS/manifest boundaries, but old local NDJSON authority code, stale in-memory/temp-path wording, and compatibility residues can still mislead future agents or keep dead paths alive. Phase 5 needs a disciplined cleanup pass that removes or classifies residue without breaking the verified active paths.

## Proposed Solution

Split the cleanup into bounded child problems:

- Audit current code/docs/tests for local transition-log authority, active-stack file walking, temp backing-path claims, process-local fallback state, and compatibility branches.
- Remove dead code and tests that only support old local authority paths.
- Update current docs/comments to state the new authority boundaries and classify any historical references explicitly.
- Add or tighten architecture guards/static tests so old patterns do not re-enter.
- Run targeted tests and full Cortex tests after cleanup.

## Acceptance Criteria

- Local NDJSON transition-log authority code is physically removed or proven absent from live paths.
- Active-stack file walking and temp backing-path authority language are removed from current docs/code comments.
- Compatibility paths that are no longer required by the current architecture are deleted, not hidden behind fallback flags.
- Guards/static tests cover the forbidden residue patterns.
- Targeted Cortex tests, full Cortex tests, and compile checks pass.
- Any remaining historical wording is explicitly classified as historical, not current behavior.

## Verification Plan

- Use `rg` audits for transition log files, NDJSON append/read helpers, active-stack file walking, `/tmp/novaic-cortex-sandbox-*`, process-local fallback, and compatibility branches.
- Inspect matching current code/docs before deleting to avoid accidental removal of historical ledger artifacts.
- Run targeted Cortex tests around scope lifecycle, active stack projection, operational store, context event APIs, payload manifest, and workspace.
- Run full `novaic-cortex/tests`.
- Run `python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)`.

## Risks

- Some old strings may appear in intentionally historical docs or ledgers; deleting those would reduce auditability.
- Dead-code deletion can reveal hidden imports or tests that still depended on old modules.
- Broad cleanup can become too large for one execution pass; child problems should be created if audit, deletion, guard, and verification are not trivially one-go.

## Assumptions

- Backward compatibility with old local authority paths is not required.
- The Phase 1-4 success checks are trusted as the baseline active architecture.
- Historical ledger files may remain as evidence unless they are current docs or live source.
