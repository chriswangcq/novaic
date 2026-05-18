# Finalize/session-ended entry-point inventory

## Problem

All finalize, session-ended, watchdog, recovery, restart, and skill-end entry points must be enumerated before changing behavior. The current risk is hidden entry points clearing active session state without carrying or checking the intended generation.

## Success Criteria

- List every finalize/session-ended/recovery/watchdog/restart/skill-end entry point with file references.
- For each entry point, record whether it carries saga id, wake scope id, session generation, reason, remaining stack, pending input ids, and restart intent.
- Classify each entry point as safe, unsafe, or needing downstream child audit.
- Identify test files that currently exercise each entry point.
- Produce follow-up targets for any path that is not explicitly generation-checked.

## Belongs Under

This is the inventory layer for T324/P328; later child problems depend on a complete map instead of guessing at finalize paths.
