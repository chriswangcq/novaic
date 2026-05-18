# Artifact And Display Blob Usage Map Result

## Summary

Blob usage mapping is complete. The scan shows three intended blob roles: user/runtime artifacts (`blob://runtime-artifact` and user-file/audio refs), Cortex large payload externalization (`blob://cortex-payload`), and LogicalFS object-store backing (`BlobObjectStore`) below the file authority. No direct evidence in this child shows blob being used by sandboxd as the live `/ro`/`/rw` authority, but `BlobObjectStore` and `Workspace.materialize()` remain explicit P553 classification items because they touch RO/RW-like keys or `/rw/scratch`.

## Done

- Generated scan artifact: `.complex-problems/L20260516-222011/tmp/p561/blob-usage-scan.txt`.
- Generated count artifact: `.complex-problems/L20260516-222011/tmp/p561/blob-usage-counts.md`.
- Generated source slices: `.complex-problems/L20260516-222011/tmp/p561/blob-usage-slices.txt`.
- Inspected:
  - `novaic-cortex/novaic_cortex/blob_payload.py`
  - `novaic-cortex/novaic_cortex/shell_capabilities.py`
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_no_historical_tool_image_injection.py`
  - `novaic-agent-runtime/tests/unit/task_queue/test_tool_output_contract.py`
  - `novaic-logicalfs/logicalfs/blob_store.py`
  - `docs/reference/blob-service.md`

## Verification

- Scan found 1799 broad hits across 345 files; many are tests/docs because terms include `artifact`, `display`, `/ro`, and `/rw`.
- Intended artifact/display usage:
  - Shell `devicectl` outputs runtime media/file artifacts as `tool-output.v1` manifests with blob URIs and display access hints.
  - Runtime tool handling sanitizes public display output so image base64 is omitted from tool history and preserved only in durable payload for explicit display perception projection.
  - Tests assert no historical tool image injection and no base64 in public tool text.
- Intended Cortex payload usage:
  - `blob_payload.py` externalizes large raw tool payloads to `blob://cortex-payload/...`.
- Intended blob service role:
  - Blob service returns shared `blob://{namespace}/{blob_id}` references and stores cheap bytes/objects.
  - Docs state blob does not decide live `/ro`/`/rw` semantics; LogicalFS/Cortex own those.
- Classification items for P553:
  - `logicalfs.BlobObjectStore` uses object keys such as `agents/a/rw/...` in tests; this is likely intended below LogicalFS but must not be used as a semantic workspace API from higher layers.
  - `Workspace.materialize()` writes bytes to `/rw/scratch` and should be classified for naming/API residue.

## Known Gaps

- This is a usage map, not remediation. P553 must decide whether `BlobObjectStore` exposure or `Workspace.materialize()` requires cleanup/renaming/tighter tests.
- Some scan hits are docs/roadmap history and need P553 classification before removal decisions.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p561/blob-usage-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p561/blob-usage-counts.md`
- `.complex-problems/L20260516-222011/tmp/p561/blob-usage-slices.txt`
