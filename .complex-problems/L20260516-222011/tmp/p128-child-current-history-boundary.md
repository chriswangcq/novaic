# Verify runtime current versus historical media boundary

## Problem

Current-round display can become provider media, but historical/non-display tool results must remain bounded text/manifest. Verify the runtime enforces this boundary.

## Success Criteria

- Current display uses `display_perception` and can produce provider image content.
- Historical display and non-display tools do not create provider image messages.
- Shell/blob/payload results stay bounded text/manifest in LLM context.
- Targeted tests pass.
