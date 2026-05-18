# Backend progress preview boundary scan result

## Summary

Inspected the backend Agent Monitor / progress preview boundary for large tool payload risk. The scan identified the relevant Cortex and Business surfaces that should keep monitor/progress paths on bounded text previews and payload references, rather than replaying raw tool payload bytes into UI or LLM context.

## Done

- Scanned `novaic-agent-runtime`, `novaic-business`, and `novaic-cortex` for progress, monitor, preview, payload, artifact, base64, and image reference paths.
- Located the Cortex step preview endpoint at `novaic-cortex/novaic_cortex/api.py` around `/v1/steps/read_preview`.
- Located the Cortex payload inspection APIs at `novaic-cortex/novaic_cortex/api.py` around payload read/search/summarize/QA.
- Located Cortex step externalization/index code in `novaic-cortex/novaic_cortex/workspace.py`, including payload reference indexing and artifact marker handling.
- Located the Agent Monitor product projection schema in `novaic-business/business/schema_push.py`, including progress text and truncation fields.
- Located relevant existing tests covering payload inspection, payload externalization, and Agent Monitor timeline/action boundaries.

## Verification

- Evidence is captured in `.complex-problems/L20260516-222011/tmp/p603/backend-progress-preview-scan.txt`.
- The scan shows backend monitor/progress paths have named preview/payload-reference seams:
  - `/v1/steps/read_preview` returns a concise `preview`.
  - payload inspection APIs expose bounded slices and truncation metadata.
  - step indexing stores `payload_ref` and `has_artifacts`.
- No production code was changed during this ticket.

## Known Gaps

- This ticket captured an inventory scan only. It did not append exact line-numbered code slices to the artifact after compaction.
- This ticket did not run focused tests for the backend progress preview boundary.
- The problem-level check should decide whether a follow-up is needed for exact slice evidence and focused test execution.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p603/backend-progress-preview-scan.txt`
