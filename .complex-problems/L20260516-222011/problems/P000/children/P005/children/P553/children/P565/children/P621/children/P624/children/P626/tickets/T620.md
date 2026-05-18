# Verify Runtime Shell Handler SDK Wiring

## Problem Definition

P626 must prove that active runtime shell/tool handlers route shell execution through the sandbox SDK/service boundary.

## Proposed Solution

Scan runtime production code for sandbox SDK imports/usages, inspect the shell handler and dependency construction code, classify the active path, and run focused tests if they directly cover shell handler execution/projection.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Source slices for dependency construction and shell handler execution are cited.
- The active shell execution path is traced to sandbox SDK/service, not local subprocess.
- Focused runtime tests pass or missing coverage is documented.
- Any bypass creates a follow-up.

## Verification Plan

Run focused runtime shell/tool handler tests that were used for shell output and no historical tool image regressions.

## Risks

- Shell wrapper code may live behind factory/dependency modules rather than in the handler itself.
- Test names may still reference old PRs and need classification, not immediate deletion.

## Assumptions

- SDK internals were already audited by P623.
