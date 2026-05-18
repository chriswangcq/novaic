# Cross-service semantic residue verification

## Problem

Verify that the semantic/app/device service residue cleanup is actually closed. The final verification must prove patched stale claims are gone, remaining hits are intentional, and any touched code/docs have suitable tests or focused scans.

## Success Criteria

- Focused scans prove patched stale terms/routes/claims no longer appear in active target files.
- Remaining hits are classified and not silently ignored.
- Relevant tests/lints/sync checks are run for touched code or generated resources.
- The result records residual risk and any follow-up if a broad unsafe area remains.
