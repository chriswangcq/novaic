# Final residue closure and verification

## Problem Definition

The FSM substrate and business DSL migration can still fail if new infrastructure exists but old business paths remain active, docs drift, deploy/start scripts regress, or tests only cover narrow happy paths. This final ticket must prove the whole gap ledger is closed rather than merely implemented.

## Proposed Solution

Run a final residue audit and verification sweep across runtime worker assembly, action effect boundaries, docs, deploy/start supervision, and ledger state. Fix any small residue directly. If a discovered gap is too large to close directly, create a follow-up problem through the ledger instead of hiding it.

## Acceptance Criteria

- All newly added guardrails pass locally.
- Focused runtime/FSM/worker/assembly tests pass.
- Residue scans show no active old imperative worker constructors in business assembly and no stale coarse deploy/worker status path.
- Docs and roadmap status lints pass.
- Git diff is reviewed and final scope is understandable.
- Ledger can close P007 with explicit evidence and residual risks.

## Verification Plan

- Run focused pytest suites for worker assembly/effect boundaries and queue/session runtime behavior.
- Run compile checks over touched runtime modules.
- Run deploy/start/documentation CI lints.
- Run residue scans for old constructors, coarse worker status, stale deploy docs, and compatibility markers.
- Inspect `git diff --stat` and key diffs.

## Risks

- Broad tests may expose unrelated existing failures. If unrelated, record them precisely; if related, fix before closing.
- Residue scans may need targeted allowlists for guard scripts that intentionally mention banned strings.

## Assumptions

- The previous tickets already implemented the intended core design; P007 is a closure/audit ticket, not a new architecture rewrite.
