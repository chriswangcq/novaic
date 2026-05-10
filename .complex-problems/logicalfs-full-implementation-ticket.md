# Split implementation into boundary-enforced phases

## Problem Definition

The LogicalFS RO/RW authority boundary is architectural and cross-cutting. It
touches Cortex workspace APIs, shell execution, sandboxd, Blob persistence,
deployment scripts, and guardrail tests. A single direct implementation pass
would risk leaving old active paths behind, which is the exact failure mode this
work must avoid.

## Proposed Solution

Split the implementation into child problems with explicit closure checks:

- Inventory active code paths and classify current state against the target
  boundary.
- Cut over or verify the active Cortex/shell path so live `RO` / `RW` goes
  through LogicalFS and sandboxd.
- Constrain direct Blob object use to cheap byte serving and LogicalFS
  persistence internals.
- Clean up legacy/fallback code, deployment references, and stale docs.
- Add architecture guardrails and tests that fail if live `RO` / `RW` bypasses
  LogicalFS.
- Run repository checks and summarize remaining non-blocking risks.

## Acceptance Criteria

- Every child problem has a concrete result and verification.
- Active shell execution path is audited by source pointers and tests.
- Direct Blob use is audited and either accepted as non-live-byte use or moved
  behind LogicalFS.
- Legacy/fallback references are removed or justified as non-active.
- Final checks include focused residue scans, targeted tests, and project-wide
  checks where feasible.

## Verification Plan

Use focused `rg` scans, source inspection with line pointers, targeted unit
tests, architecture guard tests, deployment script checks, and final
`ledger.py validate/render/status/next`.

## Risks

- Existing uncommitted work spans multiple repositories and must not be
  reverted.
- Full implementation may uncover multiple old paths and require recursive
  child tickets.
- Full matrix tests may be expensive; skipped checks must be recorded as
  residual risk or converted to follow-up problems if blocking.

## Assumptions

- The current branch is intended for this architectural migration.
- User wants no backward-compatible fallback for old live `RO` / `RW` paths.
- Blob direct use remains valid for display/artifact/attachment bytes.
