# Ticket: Cortex Archive Diagnostics Source Map

## Problem Definition

P368 needs a precise source map of the `CORTEX_SCOPE_END` archive diagnostics path before implementation. Without it, new fields could be added to one boundary while another active path continues to infer or drop finalize diagnostics.

## Proposed Solution

Inspect the runtime wake-finalize payload builders, task handler, Cortex bridge, Cortex API request model, Cortex scope archive implementation, workspace archive projection, and focused tests. Record which fields are preserved, dropped, inferred, or synthesized, and identify exact implementation targets for P372 and P373.

## Acceptance Criteria

- Source map lists every active function/file in the runtime-to-Cortex archive diagnostics path.
- Source map identifies current handling of `session_generation`, `finalize_reason`, and remaining-stack diagnostics.
- Source map names existing tests relevant to handler/bridge and Cortex persistence.
- Source map gives concrete implementation targets for boundary propagation and persistence children.

## Verification Plan

- Use `rg`, `sed`, and focused file inspection only.
- Avoid modifying production or test code.
- Record concise evidence pointers rather than large source dumps.

## Risks

- Multiple old archive paths may exist; search broadly enough to avoid missing an active path.

## Assumptions

- P366 already mapped the high-level queue finalize side; this ticket focuses on Cortex archive diagnostics.
