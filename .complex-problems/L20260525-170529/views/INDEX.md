# Complex Problem Ledger

Ledger: L20260525-170529
Schema: v6
Root: P000 - Make Agent Monitor activity titles structured and non-heuristic
Status: done
Updated: 2026-05-25T09:19:53+00:00

## Problem Tree
- [done] P000: Make Agent Monitor activity titles structured and non-heuristic
  - [done] P001: Add structured public title to activity projection contract and runtime
  - [done] P002: Render Agent Monitor titles from public fields, not reasoning keywords
  - [done] P003: Verify, clean, and commit structured activity title change

## Active

## Blocked

## Done
- [x] P000: Make Agent Monitor activity titles structured and non-heuristic
- [x] P001: Add structured public title to activity projection contract and runtime
- [x] P002: Render Agent Monitor titles from public fields, not reasoning keywords
- [x] P003: Verify, clean, and commit structured activity title change

## Tickets
- [done] T000: Structured public activity titles for Agent Monitor -> P000 (split)
- [done] T001: Add public_title to backend activity projection -> P001 (one_go)
- [done] T002: Consume public_title in ActivityTimeline -> P002 (one_go)
- [done] T003: Verify and commit structured activity title rollout -> P003 (one_go)

## Latest Checks
- [success] C000: P001 P001 is successful. The backend contract/runtime path now carries an explicit `public_title` field, runtime projection populates it for the relevant activity record types, and focused tests prove the field exists without removing reasoning detail text.
- [success] C001: P002 P002 is successful. The frontend now consumes explicit `public_title` as the title authority, keeps legacy structured fallbacks, and no longer infers reasoning titles from private/detail text.
- [success] C002: P003 P003 is successful. Relevant checks passed, minor lint blockers were resolved, modified subrepos are committed, and only the parent repo gitlink/ledger commit remains as the parent problem's finalization step.
- [success] C003: P000 The original problem is solved. Agent Monitor activity titles now have a structured backend-to-frontend public field, the frontend consumes that field as title authority, and reasoning text is no longer parsed for title keywords. The screenshot failure mode cannot recur through the old heuristic path.
