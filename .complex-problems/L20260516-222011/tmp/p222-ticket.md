# Audit and classify remaining projection branches

## Problem Definition

After projection cleanup, we need to prove removed stale symbols are gone and remaining projection branches are intentional contract handling, not accidental compatibility residue.

## Proposed Solution

Run targeted repository searches for removed symbols and projection branch markers. Inspect the active branch sites and classify each as intentional, removed, or requiring follow-up.

## Acceptance Criteria

- `resolve_for_llm` is absent from active source and tests.
- Remaining display/tool output projection branch sites are enumerated.
- Each remaining site has a clear intentional rationale or creates follow-up work.
- No code changes are made unless the audit discovers an unambiguously stale branch that can be safely removed in this bounded ticket.

## Verification Plan

Use `rg` over active packages for removed symbols and projection markers, inspect relevant files with line numbers, and record the branch classification with evidence pointers.

## Risks

- Some compatibility branches are intentionally defensive and should not be deleted just because their names look generic.
- A search may surface ledger/history files; restrict active source/test classification to code paths.

## Assumptions

- This ticket audits active repository code, not historical ledger text or archived outputs.
