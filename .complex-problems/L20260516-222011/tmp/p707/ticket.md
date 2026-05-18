# Ticket: Business service and subscriber boundary classification

## Problem Definition
Classify Business service and subscriber code as product/domain computation and event consumption. Verify entrypoints, launch surfaces, subscriber responsibilities, dependency boundaries, and separation from Queue session FSM ownership and Runtime worker orchestration.

## Proposed Solution
Inspect `novaic-business`, subscriber launch paths, Business docs, start scripts, and architecture docs. Produce a boundary map and patch or record misleading active claims if found.

## Acceptance Criteria
- Business service/subscriber entrypoints and launch references are listed with evidence.
- Business domain/API/action-hook roles are separated from Queue session FSM and Runtime worker execution.
- Subscriber input drain/aggregation roles are separated from wake/session ownership.
- Hidden env/config dependency residue is checked where subscriber behavior is classified.
- Stale misleading claims are patched or recorded.

## Verification Plan
Use focused `rg/find/sed` scans over Business/subscriber code, docs, and launch scripts; run targeted tests/lints if files are touched.
