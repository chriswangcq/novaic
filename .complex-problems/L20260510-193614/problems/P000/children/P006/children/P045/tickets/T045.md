# Audit And Classify Cleanup Residue

## Problem Definition

Phase 5 cleanup needs a precise evidence map before deleting anything. The repo may contain live old authority code, tests that still validate old paths, current docs with stale wording, and historical ledger/audit artifacts that should remain. P045 must classify the hits so later children can delete or update only the right things.

## Proposed Solution

- Run static searches for old local state authority and compatibility patterns.
- Inspect representative hits to separate live source/test/current-doc residue from historical artifacts.
- Produce a classified target list for Phase 5B, Phase 5C, and Phase 5D.
- Record what should be removed, what should be rewritten, and what should be kept as historical evidence.

## Acceptance Criteria

- Audits cover transition-log authority, active-stack file walking, temp sandbox backing paths, process-local fallback state, and compatibility branches.
- Every important hit class is mapped to one of: remove in code, update in current docs/comments, add guard, or keep historical.
- The result is concrete enough for P046-P048 to execute without rediscovering the whole space.

## Verification Plan

- Run `rg` searches over live source/tests/current docs.
- Use `git grep`/`rg` with explicit excludes for `.complex-problems` when distinguishing current artifacts.
- Inspect code snippets around high-risk matches before classifying.
- Record commands and classification in the result body.

## Risks

- Broad `rg` output may include many historical ledgers; classify by path rather than deleting blindly.
- Some terms such as `payload_ref` are current prompt-facing terms and should not be treated as residue.

## Assumptions

- This ticket is audit-only; no code deletion occurs here.
- Later Phase 5 children will execute cleanup using this target list.
