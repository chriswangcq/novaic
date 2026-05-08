# Split Post-Deploy Runtime DSL Audit

## Problem Definition

The post-deploy audit spans production state, code residue, architecture boundary correctness, and hygiene checks. Performing it as one undifferentiated pass would risk hiding gaps.

## Proposed Solution

Split the audit into four child problems:

1. Production deployment and runtime worker topology verification.
2. Old-path and compatibility residue scan for worker/action/handler surfaces.
3. FSM/worker/DSL boundary audit against live code and status documentation.
4. CI, generated artifact, ledger, and documentation hygiene verification.

Each child records evidence, commands, findings, and residual risk. The root closes only after all children pass success checks.

## Acceptance Criteria

- Child problems cover production state, code residue, architecture boundary, and hygiene checks.
- Each child has concrete evidence and verification commands.
- Any discovered issue becomes a child/follow-up problem rather than being buried in a summary.
- Root success check maps all original criteria to child results.

## Verification Plan

- Use the ledger split flow.
- Execute every child problem through `ledger.py next`.
- Run production deploy/status checks, targeted source scans, tests/lints, and focused diff/status review as appropriate.

## Risks

- Remote service checks can be transient; distinguish transient deployment noise from code/design failure.
- Grep-only scans can miss semantic issues, so pair scans with targeted file inspection.

## Assumptions

- The deploy command that just completed is the relevant production baseline for this audit.
- The audit should report and close actionable implementation gaps when found, but should not invent new future architecture work beyond the current FSM/worker/DSL closure scope.
