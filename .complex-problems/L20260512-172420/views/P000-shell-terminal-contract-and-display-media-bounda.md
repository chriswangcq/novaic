# P000: Shell Terminal Contract and Display Media Boundary

Status: todo
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Implement the tightened tool-output contract requested by the user: `shell` should behave like a human terminal and expose only bounded terminal text plus truncation metadata to the LLM-facing tool result. Full stdout/stderr remains recoverable from Cortex RO step/payload storage, not duplicated inside LLM-facing diagnostics. At the same time, repair the current `display` media boundary so explicit display perception is not converted into ordinary text/base64 when passed through the runtime tool wrapper.

The work must include design, implementation, tests, commit, and deployment. Use the ledger closure loop rather than assuming one large change is safe.

## Success Criteria
- `shell` LLM-facing output contains terminal text preview and small metadata only; no full raw stdout/stderr in diagnostics.
- Large shell stdout/stderr is truncated in the displayed text and exposes enough length/truncation metadata to know where to inspect further.
- Complete raw command output remains stored in Cortex step/payload records through the existing step persistence path.
- `display` results survive runtime wrapping as structured display media instead of becoming `tool-output.v1.text` containing base64.
- Current explicit `display` perception becomes provider-facing structured image content; historical/non-display paths do not inject images.
- Regression tests cover the real executor-to-wrapper-to-Cortex-to-runtime path, not only idealized direct inputs.
- Code is committed and deployed; smoke checks verify the deployed services are healthy.

## Subproblems
- P001: Shell LLM Output Is Terminal Preview Only
- P002: Display Media Survives Runtime Wrapping
- P003: Full Path Regression Tests And Audit
- P004: Commit Deploy And Smoke Verify

## Results
- none

## Latest Check
none

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md

## Follow-ups
- none
