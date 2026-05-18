# Business/subscriber boundary verification sweep ticket

## Problem Definition

P716 remediation touched active docs and Business code wording. A final sweep must prove no unexamined active stale claims or hidden dependency residues remain across code, docs, scripts, and launch surfaces for the Business/subscriber boundary.

## Proposed Solution

Run focused scans over Business/subscriber terms and neighboring service ownership terms, run relevant lints/tests, inspect remaining hits, and record a classified residue table. Patch only if a tiny safe miss is found; otherwise record verification evidence and residual risk.

## Acceptance Criteria

- Focused scans cover Business/subscriber boundary terms across code, docs, scripts, and launch surfaces.
- Relevant docs/architecture lint and Business guard tests pass.
- Remaining matches are classified as current boundary, historical comparison, test guard, or unrelated.
- No unexamined active stale claim remains for Business/subscriber ownership.
- Any unresolved broad issue is explicitly named as a follow-up candidate.

## Verification Plan

Run `rg` scans for Gateway/product CRUD, Subscriber wake/session/Cortex ownership, Business Queue/Runtime ownership, aggregation env/config, and direct stale ownership words. Run `python3 scripts/ci/lint_docs_status_consistency.py` and focused Business tests used in P719. Review `git diff --stat` and changed-file diffs for scope control.

## Risks

- Broad docs/roadmap hits can create noise; classify rather than delete historical ticket records.
- Nested repo changes may include pre-existing local edits; avoid claiming or reverting unrelated edits.

## Assumptions

- P718 and P719 completed before this sweep.
- The goal is high-confidence boundary cleanup, not full-repo historical archaeology.
