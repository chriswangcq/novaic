# ActivityTimeline current versus legacy behavior inventory

## Problem
ActivityTimeline needs a read-only inventory of current shell/agentctl behavior and legacy direct-tool behavior before cleanup, so implementation does not accidentally remove useful historical trace compatibility.

## Description
Capture how `ActivityTimeline.tsx` maps shell records, old IM tool records, and reasoning text to public labels/hiding behavior.

## Success Criteria
- Identify current-path records that should be shell/agentctl shaped.
- Identify old direct-tool handling that is compatibility versus normal path.
- Identify focused tests that must be updated.
