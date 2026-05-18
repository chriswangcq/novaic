# LogicalFS Public Contract Cleanup

## Problem

Patch LogicalFS public docs/metadata so it clearly presents live `/ro` and `/rw` file-operation authority rather than stale snapshot/view/patch-first wording.

## Success Criteria

- LogicalFS README/package metadata/contracts wording matches the current live RO/RW substrate role.
- It does not claim Cortex semantics ownership.
- Focused tests or docs checks pass.
