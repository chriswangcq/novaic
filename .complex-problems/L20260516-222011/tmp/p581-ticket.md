# Ticket: Audit Cortex Display Projection Contract

## Summary

Audit current Cortex display step-result projection behavior after BlobRef-backed display perception changes.

## Problem Definition

Cortex must preserve current display perception media references without allowing history/default projections to replay image bytes. This ticket records the active projection code paths and classifies current behavior.

## Proposed Solution

Read `step_result_projection.py`, Cortex `read_formatted` API wiring, and runtime bridge expansion path. Record whether current display perception, history, and current non-display projections obey the intended contract.

## Acceptance Criteria

- Scan commands and evidence files are recorded.
- Relevant code slices are cited with line references.
- Current behavior is classified for perception versus history.
- Any replay/base64 leak is forwarded as follow-up.

## Verification Plan

Use read-only scans plus the focused tests already added for the projection contract.
