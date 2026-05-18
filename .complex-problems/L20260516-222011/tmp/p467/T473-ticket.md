# Session legacy residue final verification ticket

## Problem Definition

P467 must close the P285 session legacy residue audit by rerunning final guards after P465 inventory and P466 hidden-input/duplicate cleanup.

## Proposed Solution

Run final source guards for retired active-session tables, observed wake old effect strings, direct wake saga creation bypasses, legacy/compat/fallback language in active session harness files, and focused session tests. Save all artifacts under `.complex-problems/L20260516-222011/tmp/p467/`.

## Acceptance Criteria

- Final guard artifacts are saved.
- Production source has no `tq_active_sessions` references.
- Production source has no old `observe_create_wake_saga` effect type except test fixtures.
- Session repository has no direct wake saga creation or retired side-effect paths.
- Focused session/residue tests pass.

## Verification Plan

Run `rg` guards from repo root and focused pytest from `novaic-agent-runtime`.

## Risks

- Some test fixtures intentionally retain old strings to prove cleanup; classify them separately from production hits.

## Assumptions

- This is verification-only unless a real residue is found.
