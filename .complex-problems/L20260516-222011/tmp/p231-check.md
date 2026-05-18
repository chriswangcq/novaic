# Check: tool step write path durable payload refs are verified

## Summary

`P231` is solved by `R223`. Both halves of the active tool step write path are verified: runtime handoff produces compact public projections with durable raw payloads, and Cortex workspace persistence writes and indexes `step_ref`/`payload_ref` metadata while rejecting inline tool results.

## Evidence

- `R219` / `C233`: workspace persistence writes payload records/manifests, rejects inline tool `result`, requires payload refs, and indexes refs; tests `28 passed`.
- `R222` / `C236`: runtime shell/display handoff separates compact public content from raw heavy output; shell tests `19 passed`, display/media tests `14 passed`.
- Representative regressions tested: large shell stdout, media-like shell stdout, and display image `_mcp_content` history injection.

## Criteria Map

- Active tool handler to Cortex write path is mapped with file/function pointers: satisfied by runtime handler pointers from `R222` and workspace pointers from `R219`.
- Step write implementation evidence shows `payload_ref`/`step_ref` are required, generated, or preserved for heavy tool output: satisfied by `workspace.py` evidence and child checks.
- Tests or focused probes verify durable payload refs are emitted for representative shell/display-like output: satisfied by the combined Cortex/runtime focused tests.

## Execution Map

- Split ticket `T223` created `P235` and `P236`.
- `P235` closed with result `R219` and check `C233`.
- `P236` closed with result `R222` and check `C236`.
- Parent result `R223` summarized those child outcomes.

## Stress Test

The parent-level failure mode is that raw heavy output either bypasses runtime projection or is stored inline by workspace. Child checks cover both gates: runtime tests prove shell/display output is compact before persistence, and workspace tests prove inline tool results are rejected and payload refs are indexed.

## Residual Risk

Non-blocking for `P231`: this does not prove every default context assembly expansion stays compact after storage; that is handled by sibling `P233`. Event projection is sibling `P232`.

## Result IDs

- `R223`
- `R219`
- `R222`
