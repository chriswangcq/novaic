# Extracted service entrypoint discovery scan

## Problem Definition

P695 needs a read-only evidence inventory for extracted service entrypoints and launch surfaces across Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, wrappers, generated app resources, package scripts, and deployment configs.

## Proposed Solution

Run targeted repository scans using `rg`, `find`, package manifests, service config files, launch scripts, deployment units, and Python entrypoint idioms. Save raw candidate files, launch references, and a compact per-service evidence matrix under the ledger tmp tree. Do not classify roles yet beyond identifying candidate evidence presence or absence.

## Acceptance Criteria

- Candidate entrypoint files are listed for all target service names.
- Launch/config/package-script evidence is captured with stable paths.
- Generated app resources and source launch scripts are both included.
- Every target service has evidence or an explicit absence note.
- Scan commands and summaries are preserved under `.complex-problems/L20260516-222011/tmp/p695/`.

## Verification Plan

- Run shell-native scans and save raw outputs.
- Count candidate files and keyword matches.
- Verify expected service terms appear in the generated evidence matrix.
- Record a result with artifacts and residual gaps.

## Risks

- Some matches may be tests/docs rather than active launch surfaces.
- Generated resources can duplicate source scripts.
- Service names may overlap with generic text, requiring later classification.

## Assumptions

- This ticket is discovery-only and should not edit production code.
- Later sibling problems will classify boundaries and clean residue.
