# Session-ended delivery tests compatibility cleanup

## Problem

Tests must not bless zero-generation session-ended/finalize delivery as valid. Existing tests should either assert failure for zero/missing generation or be clearly outside the session-ended delivery boundary.

## Success Criteria

- Search tests for `session_generation=0`, `"session_generation": 0`, `generation=0`, and zero-generation assertions near finalize/session-ended.
- Rewrite any P336 delivery-boundary test that treats zero generation as valid.
- Explicitly classify unrelated or upstream tests as delegated to other tickets.
