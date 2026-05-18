# P622 Sandbox Wire Base64 and Mount Residue Classification Check

## Summary

Success. The split results classify both required residue families with concrete scan artifacts and verification: P628 covers base64/stdout/stderr/public-history behavior, and P629 covers mount/host-path/ro-rw/logicalfs/blob boundary behavior. No risky public base64 leak or runtime/client mount bypass remains in the inspected surfaces.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p628-base64-history-scan.txt` records base64/stdout/stderr/display/blob-related hits, including SDK `stdout_b64`/`stderr_b64`, runtime durable payload handling, Cortex devicectl base64 decoding, artifact Blob refs, and UI base64 redaction code/tests.
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-scan.txt` records mount/source_root/mount_point/stable_cwd, logicalfs, blob, `/ro`/`/rw`, and host/path ownership hits across SDK, Cortex, sandbox-service, runtime, and tests.
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-classification.md` classifies private wire vs durable payload vs public history vs current multimodal perception.
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-classification.md` classifies SDK DTO, Cortex LogicalFS planning, sandbox-service namespace execution, and runtime non-ownership.
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-python-tests.txt`: 50 focused Python tests passed.
- `.complex-problems/L20260516-222011/tmp/p628-base64-history-frontend-tests.txt`: 18 frontend monitor/projection tests passed.
- `.complex-problems/L20260516-222011/tmp/p629-mount-boundary-tests.txt`: 24 SDK/service/Cortex mount/logicalfs tests passed.

## Criteria Map

- Exact scans for base64/stdout/stderr/mount/host path/ro-rw/logicalfs/blob terms: satisfied by the P628 and P629 scan artifacts and their cited slices/classification files.
- Classifies wire encoding and mount/path hits: satisfied by the P628 and P629 classification artifacts.
- Runs focused tests or cites service/SDK tests proving behavior: satisfied by the 50 + 18 + 24 passing focused tests.
- Creates follow-up if risky mount or public base64 residue remains: no follow-up required because the remaining legacy parser compatibility is documented as non-active-path compatibility and guarded by current-path tests.

## Execution Map

- P628 closed base64/public-history residue and verified that current shell/device/display paths project artifact manifests or bounded terminal text instead of raw base64 public history.
- P629 closed mount/path residue and verified that mount ownership remains SDK DTO -> Cortex LogicalFS plan -> sandboxd namespace execution, with runtime outside mount planning.
- P622 rolled the children up without adding new implementation, preserving the split evidence.

## Stress Test

The stress surface was a plausible real failure mode from the user-visible bug: screenshots or other binary data could re-enter LLM/tool history as raw base64. P628 directly covered this with backend projection tests plus frontend ActivityTimeline redaction tests. P629 separately covered the mount-bypass failure mode where runtime/client code might mount uncontrolled host paths; focused SDK/service/Cortex tests and scans show mount execution is sandboxd-owned.

## Residual Risk

- `step_result_projection.py` still has compatibility parsing for legacy inline image data/data URLs. This is a deliberate legacy reader surface, not the current shell/display history path, and current artifact/BlobRef paths are guarded by tests.
- Generated local `__pycache__` files are workspace hygiene only, not a P622 behavior risk.

## Result IDs

- R621
