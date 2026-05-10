# Phase 5C.1 Current Documentation And Comment Residue Audit

## Problem

The repo contains both current architecture docs and historical roadmap/review docs. A raw grep for fallback/legacy/file-walk terms is noisy. We need to classify current residue before editing, so historical provenance is not accidentally rewritten.

## Success Criteria

- Run focused static searches over `docs`, Cortex source comments, and relevant tests.
- Classify hits into current docs to edit, live comments/docstrings to edit, intentional guard wording, and historical docs to leave untouched.
- Specifically classify `_walk_scope_tree`, `include_display`, `/tmp/novaic-cortex-sandbox-*`, in-memory/process-local, and fallback/local authority wording.
- Produce an execution map for the remaining Phase 5C child problems.
