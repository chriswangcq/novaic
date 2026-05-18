# Ticket: Business/subscriber boundary discovery and map

## Problem Definition
Discover Business service and Subscriber entrypoints, launch surfaces, product/action-hook responsibilities, event drain/aggregation roles, and dependencies. Produce a boundary map and cleanup candidate list without implementation changes.

## Proposed Solution
Scan `novaic-business`, subscriber modules, start scripts, architecture docs, and dispatch subscriber code for entrypoints, launch refs, dependency boundaries, and hidden config/env reads. Save scan outputs and boundary map.

## Acceptance Criteria
- Business and Subscriber entrypoints/launch references are listed with evidence.
- Business product/action-hook responsibilities are separated from Queue/Runtime/Cortex/Gateway/Device/Entangled ownership.
- Subscriber drain/aggregation role is separated from wake/session ownership.
- Hidden env/config dependency candidates are listed.
- P716 cleanup candidates are listed.

## Verification Plan
Use `find`, `rg`, `sed`, and targeted compile/lint where useful. Record scan commands, raw scans, boundary map, and cleanup candidates.
