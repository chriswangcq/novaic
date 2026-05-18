# Audit Runtime Sandbox SDK Call Sites

## Problem Definition

P624 must verify that active `novaic-agent-runtime` shell/tool execution paths use the sandbox SDK/service boundary and do not keep direct subprocess execution, host path mounting, or legacy local fallback paths.

## Proposed Solution

Scan runtime production code for sandbox SDK imports/usages and risky execution/fallback/mount terms, inspect the active shell/tool handler slices, classify all hits, and run focused runtime shell-output/tool-handler tests.

## Acceptance Criteria

- Exact runtime scan commands and outputs are recorded.
- Active runtime source slices that instantiate/call sandbox SDK are cited.
- Direct subprocess/local fallback/host mount hits are classified as intended, test-only, risky, or removable.
- Focused runtime tests pass or produce a follow-up for missing coverage.
- Any active runtime bypass of sandboxd creates a remediation follow-up.

## Verification Plan

Run focused runtime tests covering shell execution/output projection and no historical image/tool retry regressions.

## Risks

- Runtime tests may include local/fallback words in historical names or fixtures.
- Some subprocess use may be unrelated worker orchestration rather than shell execution.

## Assumptions

- `novaic-sandbox-sdk` itself was audited by P623.
