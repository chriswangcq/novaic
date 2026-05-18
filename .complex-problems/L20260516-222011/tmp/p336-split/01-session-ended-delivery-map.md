# Session-ended delivery chain inventory

## Problem

Before changing behavior, map the exact session-ended/finalize delivery chain and classify which files own payload construction, validation, transport, route schema, repository mutation, and tests. The result must identify every place where generation can be lost, defaulted, inferred, or silently converted.

## Success Criteria

- List every live file/function in the session-ended delivery chain from wake-finalize saga to repository call.
- Identify payload fields required at each boundary: agent id, subagent id, scope id, generation, finalize reason, remaining stack.
- Classify each boundary as safe, unsafe, or test-only.
- Produce concrete implementation targets for the remaining P336 child problems.
