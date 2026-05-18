# Result: Foundational boundary residue remediation

## Summary

Remediated both active cleanup candidates from P703. Runtime dispatch docs now distinguish Cortex scope/context/shell orchestration from sandboxd process execution, and Cortex requirements no longer claim Redis is optional or that an in-memory lock backend is safe.

## Done

- Patched `docs/runtime/tool-chain-dispatch.md` to say Cortex owns scope/context/shell orchestration while sandboxd owns process execution.
- Patched `novaic-cortex/requirements.txt` to say Redis/distributed scope lock is required and there is no production in-memory fallback.
- Captured remediation diff and retired-phrase scan artifacts.

## Verification

- `python3 scripts/ci/lint_blob_workspace_boundary.py` passed.
- Retired phrase scan over the touched files produced no matches for:
  - `Cortex owns scope/context/sandbox`
  - `default in-memory backend`
  - `safe to leave the pkg uninstalled`
  - `CORTEX_LOCK_BACKEND=redis`

## Gaps

No remaining active cleanup candidate from P703 is left unhandled in this ticket.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p704/remediation.diff`
- `.complex-problems/L20260516-222011/tmp/p704/retired-phrase-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p704/lint-blob-workspace-boundary.txt`
