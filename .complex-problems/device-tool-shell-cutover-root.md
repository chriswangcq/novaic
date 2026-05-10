# Dynamic device tool schema cutover to shell

## Problem

Static builtin schemas are now reduced to the core surface, but mounted HD/device tools can still be dynamically merged into LLM-visible tools during context preparation. This leaves an old direct-tool path active at runtime even though the static schema looks clean.

## Success Criteria

- Runtime no longer merges mounted device schemas into the LLM request.
- Shell exposes a generic `devicectl hd ...` capability for mounted device operations.
- The shell command can call the existing Device Service proxy using explicit env.
- Direct device executors remain internal compatibility only.
- Tests prove mounted device tools are not LLM-visible and shell device command works.
