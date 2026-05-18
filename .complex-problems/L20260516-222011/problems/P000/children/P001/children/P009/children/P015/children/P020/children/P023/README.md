# Update vmuse long-running command guidance to shell-first contract

## Problem

The vmuse shell tool documentation and bundled app resource copies still instruct agents to use direct `subagent_spawn(...)` for long-running commands. Update the guidance to avoid direct-tool assumptions and prefer the current NovaIC shell CLI form where available.

## Success Criteria

- Source vmuse guidance no longer recommends direct `subagent_spawn(...)` syntax.
- Bundled app resource copies are updated consistently.
- Timeout warning text avoids direct-tool syntax.
- Focused search confirms no current vmuse source/resource direct `subagent_spawn(...)` guidance remains.
