# Ticket: isolate monitor activity legacy direct-tool boundary

## Problem Definition

Production activity projection/UI still contains legacy direct IM tool names to render old archived records. That is useful, but the boundary must be explicit and must not look like active runtime policy.

## Proposed Solution

Audit and clean production monitor code:

- Runtime `activity_projection.py` legacy label map.
- App `ActivityTimeline.tsx` legacy detection helpers.

Prefer explicit legacy naming and constructed/centralized constants over free-floating old direct-tool strings.

## Acceptance Criteria

- Current shell/agentctl monitor behavior remains primary.
- Legacy direct-tool detection is named as archived/historical compatibility.
- Raw direct-tool names are centralized and not scattered in generic helper logic.
- Focused backend/frontend tests pass.

## Verification Plan

- Focused `rg` over production activity projection/UI files.
- Run runtime activity projection tests.
- Run ActivityTimeline tests.

## Risk

Removing legacy rendering completely could make old monitor history unreadable. Keep compatibility, but isolate it.
