# Update current IM tool docs and placeholders to shell contract

## Problem

Current-facing docs and UI placeholders still imply IM capabilities are direct LLM tools. Update them to the current shell-first contract: direct tools are minimal, while IM actions are performed through `agentctl im ...` inside shell.

## Success Criteria

- Current docs no longer describe `im_read`, `im_reply`, `im_send`, `im_history`, `im_search`, or `im_context` as active direct LLM tools.
- Docs describe IM actions through shell `agentctl im read/reply/send/history/search/context`.
- UI placeholder strings no longer advertise `im_read` as a direct tool example.
- Historical roadmap docs may remain if clearly historical and not current contract docs.
- Focused residue search confirms no current-facing stale IM direct-tool wording remains in the edited surfaces.
