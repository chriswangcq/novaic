# Sandbox and Sandboxd boundary map implementation

## Problem Definition

P701 needs an evidence-backed Sandbox/Sandboxd boundary map. Sandboxd should be classified as the foundational execution service; sandbox SDK and core modules should be distinguished from Cortex shell orchestration and LogicalFS view semantics.

## Proposed Solution

Inspect `novaic-sandbox-service`, `novaic-sandbox-sdk`, Cortex shell executor/facade code, launch scripts, and docs. Produce a boundary map that records Sandboxd service entrypoint, SDK boundary, execution responsibilities, dependencies, and any misleading ownership claims. Patch only safe stale wording/guard gaps if clearly wrong.

## Acceptance Criteria

- Sandboxd service entrypoint and launch evidence are listed with stable paths.
- Sandbox SDK/service/core responsibilities are summarized separately.
- Cortex shell code is classified as orchestration/facade, not sandbox execution service ownership.
- Sandboxd does not own LogicalFS workspace/subagent/display semantics unless code proves otherwise.
- Misleading Sandbox boundary claims are patched or explicitly recorded.
- Focused tests/syntax checks pass if files change.

## Verification Plan

- Inspect service/SDK/Cortex facade files and P695 evidence.
- Run targeted sandbox boundary scans.
- Run sandbox boundary/core/service tests or syntax checks.
- Save map and verification artifacts.

## Risks

- Sandboxd may host mount mechanics while LogicalFS owns semantics; this distinction must be precise.
- Cortex shell facade legitimately calls Sandboxd and LogicalFS; this is orchestration, not service ownership.

## Assumptions

- No compatibility is needed for misleading stale claims in active docs/scripts.
