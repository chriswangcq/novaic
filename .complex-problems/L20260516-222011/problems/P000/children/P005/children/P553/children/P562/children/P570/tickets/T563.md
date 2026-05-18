# Build P566 And P567 Scan Manifests

## Problem Definition

P562 requires exact scan commands and outputs for all child classifications. P568 has a manifest, but P566 and P567 currently only cite output artifacts.

## Proposed Solution

Create evidence-only manifests under the existing P566 and P567 temp directories. Each manifest should list exact reproducible commands for the child scan and slice artifacts, output paths, and mapping back to child and parent criteria.

## Acceptance Criteria

- `.complex-problems/L20260516-222011/tmp/p566/scan-command-manifest.md` exists.
- `.complex-problems/L20260516-222011/tmp/p567/scan-command-manifest.md` exists.
- Each manifest includes exact command blocks, output artifact paths, criteria mapping, and classification conclusion.
- No production code changes are made.

## Verification Plan

Read both manifests back and confirm all required sections are present. No tests are required because this is ledger evidence documentation only.

## Risks

- Commands must be concrete and reproducible, not vague descriptions.

## Assumptions

- The existing scan/slice artifacts remain valid and do not need regeneration.
