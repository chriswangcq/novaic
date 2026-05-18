# Build P568 Scan Manifest

## Problem Definition

P568's classification result cites scan output artifacts but does not preserve the exact shell commands that produced them. This weakens reproducibility for the stable-path compatibility audit.

## Proposed Solution

Create a P568-local manifest artifact under `.complex-problems/L20260516-222011/tmp/p568/` that records the exact scan and slice commands, the output file each command produced, and the P568 criterion supported by each artifact. Keep the work limited to ledger/evidence documentation; do not touch production code.

## Acceptance Criteria

- A manifest file exists under `.complex-problems/L20260516-222011/tmp/p568/`.
- The manifest includes exact commands for `path-compat-scan.txt` and `path-compat-slices.txt`.
- The manifest maps each artifact to the P568 criteria.
- The manifest states that P568 found no active old compatibility fallback and forwards no remediation candidate from stable-path compatibility itself.

## Verification Plan

Read the manifest and confirm it contains commands, artifact paths, criteria mapping, and classification conclusion. No code tests are required because this ticket changes only evidence documentation.

## Risks

- If the recorded commands are approximate rather than exact, the follow-up does not close the reproducibility gap.

## Assumptions

- The relevant output artifacts already exist and do not need to be regenerated.
