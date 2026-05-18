# Cortex residue inventory ticket

## Problem Definition

Build a precise Cortex-only inventory for compatibility residue so downstream cleanup does not mix live code with tests, docs, virtualenv files, generated caches, or historical ledger artifacts.

## Proposed Solution

Run targeted guards over `novaic-cortex` and related Cortex-facing packages, excluding `.venv`, caches, generated files, and `.complex-problems`. Classify hits by file and responsibility area: context event lifecycle, archive/diagnostics, API/CLI/bridge, tests, docs/history, and non-live artifacts.

## Acceptance Criteria

- Guard outputs are saved under `.complex-problems/L20260516-222011/tmp/p416/`.
- Inventory excludes virtualenv/generated/cache noise.
- Live Cortex surfaces are separated from tests/docs/history.
- Downstream child problems receive a concrete file/surface map.
- Any unexpectedly broad live slice is called out for further splitting.

## Verification Plan

- Use `rg` with explicit exclusion globs.
- Summarize file buckets and inspect representative hits.
- Do not edit source files in this ticket.

## Risks

- Regex guards can overmatch legitimate diagnostics or test fixtures.
- Cortex-adjacent packages may live outside `novaic-cortex`; include them only if clearly Cortex-facing.

## Assumptions

- This ticket is inventory-only; cleanup happens in later child problems.
