# Follow-up: Reconcile remaining current docs with shell-first tool contract

## Problem
After code/UI cleanup, current documentation still contains old direct tool names (`im_read`, `im_reply`, `im_history`, `payload_read`, etc.) outside historical PR tickets. This can mislead future implementation toward resurrecting direct tools.

## Success Criteria
- Current docs use shell-first wording for IM, reply, history, and payload interpretation paths.
- References that are semantic invariants use neutral terms such as “reply action” instead of retired direct tool names.
- Historical roadmap ticket files are not rewritten unless linked as current guidance.
- Focused docs grep either returns no hits outside acceptable implementation/internal terms, or every remaining hit is justified as historical/contract-internal.

## Verification Plan
- Patch docs narrowly.
- Run focused `rg` over docs excluding historical roadmap tickets.
- Record acceptable residuals explicitly.
