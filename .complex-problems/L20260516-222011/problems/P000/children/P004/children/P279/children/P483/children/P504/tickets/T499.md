# Final Guard Classification

## Problem Definition

P504 must produce the final static evidence for imperative dispatch cleanup. It needs to rerun guard searches after cleanup and classify every hit without changing production code.

## Proposed Solution

Run targeted `rg` guard commands over `novaic-agent-runtime` for direct saga creation, direct queue publish, fallback/legacy/compat dispatch terms, active-session pointer usage, attach generation bypasses, and finalize/session-ended compatibility terms. Save raw outputs and write a classification matrix separating production boundaries, intended FSM/outbox code, test/docs guard fixtures, removable residue candidates, and ambiguous follow-up candidates.

## Acceptance Criteria

- Raw guard outputs are saved under the ledger tmp directory.
- The classification matrix references concrete files and patterns.
- Production hits are classified separately from tests/docs.
- No production file is modified by this inventory child.
- Ambiguous or removable production candidates are listed for P505.

## Verification Plan

Run the guard commands from the repo root, save raw output files, inspect hits with file context as needed, and write a concise classification artifact. Confirm `git diff` for production files is unchanged by this child.

## Risks

- Static search can overmatch guard tests, documentation, or historical ledger files.
- Required adapter boundaries may look like old direct side effects unless call direction is checked.

## Assumptions

- The runtime dispatch surface is primarily inside `novaic-agent-runtime`.
- P505 will handle any source cleanup discovered here.
