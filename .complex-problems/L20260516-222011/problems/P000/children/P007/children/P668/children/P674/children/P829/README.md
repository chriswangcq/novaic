# Doc CI guards pass after topology changes

## Problem

Doc-focused CI guards (lint_docs_status_consistency.py, lint_current_docs_residue.sh) must pass. These check doc content against code state.

## Success Criteria

- Doc CI guards run without failures.
- No stale doc claims flagged by guards.
