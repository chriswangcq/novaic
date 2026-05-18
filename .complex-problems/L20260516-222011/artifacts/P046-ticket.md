# Ticket: isolate frontend ActivityTimeline legacy detection

## Problem Definition

`ActivityTimeline.tsx` still has raw legacy direct IM tool tokens scattered through sets and helper predicates. This is needed for old archived records, but the code should centralize and label those tokens as legacy compatibility.

## Proposed Solution

- Add explicit legacy token constants built from fragments.
- Use those constants in legacy predicates and bookkeeping sets.
- Keep current shell/agentctl matching as the primary path.

## Acceptance Criteria

- Production `ActivityTimeline.tsx` has no scattered raw `im_read` / `im_reply` / `chat_reply` literals in helper bodies.
- Legacy detection remains functional through explicit constants.
- Focused ActivityTimeline tests pass.

## Verification Plan

- Focused grep over `ActivityTimeline.tsx`.
- Run ActivityTimeline unit/acceptance tests.

## Risk

Do not break rendering for old archived monitor records.
