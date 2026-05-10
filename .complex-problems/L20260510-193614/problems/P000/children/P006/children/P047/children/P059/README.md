# Phase 5C.3 Live Source Comments And Docstrings Cleanup

## Problem

Some live source comments/docstrings can still imply process-local or fallback behavior is production authority. These comments must match the runtime design: SQLite/Redis/LogicalFS/Blob are authority boundaries; process memory is only a cache/client holder.

## Success Criteria

- Update live comments/docstrings that imply single-process/in-memory production authority.
- Keep comments that explicitly ban fallback or describe migration behavior, but clarify them when necessary.
- Avoid behavior changes except where a comment reveals a direct contradiction already handled by earlier phases.
- Static source-comment search has no unclassified current residue.
