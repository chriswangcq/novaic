# Phase 5C.3 Live Source Comments And Docstrings Cleanup

## Problem Definition

Live source comments/docstrings still need a targeted cleanup pass so that current source does not imply process-local memory or fallback paths are production authority. The known audit hit is `novaic-cortex/novaic_cortex/registry.py`, whose module docstring still says single-process in-memory caching is safe.

## Proposed Solution

Update live source comments/docstrings only:

- Rewrite the `WorkspaceRegistry` module docstring to say it holds process-local client/cache objects only.
- Explicitly name the authority boundary: Operational SQLite plus LogicalFS/Blob-backed workspace state, not process memory.
- Run a narrow static search for source-comment residue around single-process/in-memory/fallback authority wording and adjust only misleading current comments.
- Keep intentional negative guard comments that ban fallback or describe test-only migration behavior.

## Acceptance Criteria

- `registry.py` no longer claims single-process service behavior makes in-memory caching safe.
- Current source comments/docstrings do not imply process-local memory is production authority.
- No behavior changes are introduced by this ticket.
- Static source-comment search has no unclassified current residue for the targeted terms.

## Verification Plan

```bash
rg -n "Single-process service|in-memory caching|process-local.*authority|in-process.*production|fallback authority|local authority" novaic-cortex/novaic_cortex -S
python3 -m py_compile novaic-cortex/novaic_cortex/registry.py
```

## Risks

- Broad search terms may hit intentional negative guard comments; classify them instead of deleting useful warnings.
- Comment-only edits can create false confidence if wording is changed without checking nearby implementation intent.

## Assumptions

- This ticket is limited to live source comments/docstrings, not current docs or historical documents.
