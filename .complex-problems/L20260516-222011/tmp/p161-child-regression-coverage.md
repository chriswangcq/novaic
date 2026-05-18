# LLM payload handoff regression coverage audit

## Problem

Even if the current builder and handler look correct, regressions can reintroduce stale context handoff. The runtime test suite must contain a focused guard that would fail if prepare-context output stopped being the sole authority for provider messages/tools.

## Success Criteria

- Existing tests covering prepare-result-to-LLM handoff are identified with line pointers.
- Missing direct guards are added or a follow-up is split if coverage cannot be completed safely.
- The focused runtime test slice is run and reported.
- The check explicitly states what plausible regression the tests would catch.
