# Ticket: Display BlobRef Perception Design Map

## Summary

Map the display perception call path and decide the clean implementation boundary for resolving BlobRef media without durable base64.

## Problem Definition

Display bytes currently flow from Blob Service into runtime display executor and then into Cortex durable payload as base64. Before changing this, we need a precise call path and ownership decision so the implementation is small, connected, and does not introduce another half-wired adapter.

## Proposed Solution

Read runtime display handler, Cortex step payload write/read, Cortex step-result projection, runtime step-result expansion, and multimodal conversion. Document where metadata should persist and where Blob bytes should be fetched for current display perception.

## Acceptance Criteria

- Call path is recorded with line references.
- The chosen boundary has explicit dependencies and does not hide Blob fetches inside generic history formatting.
- Implementation guidance is concrete enough for the next child ticket.

## Verification Plan

Inventory/design check over cited code slices. No code changes in this ticket.
