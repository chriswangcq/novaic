# P236: Audit runtime tool handler durable payload handoff

Status: done
Parent: P231
Root: P000
Source Ticket: T223 (split)
Source Check: none
Package: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236
Body: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/README.md
Ticket(s): T225

## Problem
Runtime tool handlers and the bridge to Cortex must pass heavy shell/display-like output as durable payload metadata/projections rather than embedding raw output in normal message history.

This belongs under `P231` because even correct workspace persistence fails if runtime handlers bypass it or send raw data as the public tool result.

## Success Criteria
- Runtime tool handler/bridge code paths for shell and display-like outputs are mapped with file/function pointers.
- Evidence shows heavy raw output is separated from public compact projection and carried as durable payload input where applicable.
- Focused runtime tests pass for shell/display projection and no raw base64/large stdout in normal tool messages.

## Subproblems
- P237: Audit runtime shell handoff uses compact projection plus durable payload
- P238: Audit runtime display and media handoff avoids raw image text

## Results
- R222

## Latest Check
C236

## Bodies
- Problem: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/README.md
- Ticket T225: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/tickets/T225.md
- Result R222: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/results/R222.md
- Check C236: problems/P000/children/P003/children/P129/children/P229/children/P231/children/P236/checks/C236.md

## Follow-ups
- none
