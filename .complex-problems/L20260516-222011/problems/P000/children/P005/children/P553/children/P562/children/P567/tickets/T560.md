# Classify Cortex Shell Fallback And Executor Bypass Residue

## Problem Definition

P567 must classify Cortex local shell fallback, direct subprocess/process execution, and sandbox executor bypass residue.

## Proposed Solution

Run targeted scans over `novaic-cortex/novaic_cortex` and Cortex tests for subprocess/fallback/process runner/sandbox executor terms. Read relevant slices and classify hits.

## Acceptance Criteria

- Scan commands and outputs are recorded.
- Production local execution fallback is either absent or explicitly classified.
- Sandbox executor wiring and not-configured paths are classified.
- Any remediation candidate is passed to P554.

## Verification Plan

Use `rg` scans and line-numbered reads for `subprocess`, `create_subprocess`, `process_runner`, `sandbox_executor`, `fallback`, `local`, and `SandboxdClient`.

## Risks

- Tests may include fake runners and local test doubles that are not production fallback.
- `local` can be a noisy term.

## Assumptions

- Cortex shell execution should fail explicitly if sandboxd is not configured.
