# Audit LogicalFS Sandbox Blob Layering

## Problem Definition

P005 must audit and optimize layering among Cortex, LogicalFS, sandbox service/core, and blob service. The intended boundary is that real-time RO/RW file semantics go through LogicalFS/sandbox, while cheap durable artifacts use blob. Direct materialization fallbacks or misleading compatibility routes should be removed or explicitly justified.

## Proposed Solution

Split the audit into focused child problems: map current modules/imports/call paths, scan for fallback/backdoor/direct materialization residues, remediate high-confidence stale paths, and run focused verification/static checks for the intended layering.

## Acceptance Criteria

- Current layer boundaries are mapped with file references.
- Direct fallback/backdoor paths are searched and classified.
- High-confidence stale or misleading compatibility paths are removed or tightened.
- Verification artifacts prove the intended layering where feasible.
- Any remaining exception is explicitly documented as current necessity.

## Verification Plan

Use `rg`/`find` to map imports and calls across Cortex, LogicalFS, sandbox service/core, and blob surfaces. Run focused tests or static guard commands for changed areas. If risky residue appears but cannot be safely fixed in one step, split a follow-up child.

## Risks

- The project spans multiple repositories/submodules, so a single local tree scan can miss code that lives outside this checkout.
- Some blob usage is intended for artifacts/display, so naive direct-blob removal would be harmful.
- Some compatibility code may be operationally needed until all services are deployed together.

## Assumptions

- The current workspace contains the relevant local code for this audit.
- User preference is no local fallback unless explicitly necessary.
- The audit should prefer physical cleanup over long-term compatibility residue.
