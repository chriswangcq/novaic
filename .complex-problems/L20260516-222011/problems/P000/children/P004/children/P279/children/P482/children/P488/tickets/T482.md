# Finalize/session residue inventory ticket

## Problem Definition

P488 must produce a high-signal inventory of finalize/session compatibility residue before any more cleanup. The audit should catch old imperative branches, missing-generation fallbacks, recovery shortcuts, and direct active-session mutation around finalize, session-ended, attach, and recovery.

## Proposed Solution

Run targeted `rg` searches across runtime and queue service code using terms tied to compatibility risk. Inspect the matching files, then classify each retained hit into active FSM behavior, adapter boundary, guard/test fixture, removable residue, or ambiguous follow-up. Save both raw guard output and classification artifacts under the ledger tmp directory.

## Acceptance Criteria

- Raw guard artifact includes the searched terms and matched paths.
- Classification artifact includes exact file references and categories.
- Any ambiguous or removable production hit is named explicitly.
- No code changes are made in this inventory-only ticket.

## Verification Plan

Use `rg` over `novaic-agent-runtime`, `novaic-business`, and related tests/docs for finalize/session/attach/recovery residue terms. Use `sed`/`nl` to inspect candidate files and produce a compact classification.

## Risks

- Some compatibility-looking terms are test fixtures that intentionally preserve old behavior names.
- Over-broad grep can be noisy; classification must be evidence-based rather than keyword-only.

## Assumptions

- This ticket is inventory-only; deletion belongs to later child problems.
