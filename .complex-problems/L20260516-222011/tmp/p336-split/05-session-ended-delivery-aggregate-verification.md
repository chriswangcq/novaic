# Session-ended delivery aggregate verification

## Problem

After the implementation children land, verify the entire session-ended delivery boundary as an integrated contract rather than isolated snippets. The check should catch "new logic exists but old path is still active" failures.

## Success Criteria

- Run focused session-ended/finalize tests across saga payload builder, handler/client, route schema, repository finalize, and legacy compat guards.
- Exercise at least one valid session-ended delivery path end to end through handler/client/repository fakes or existing route tests.
- Run source guards for forbidden generation fallback expressions in the P336 delivery boundary.
- Record residual risks and explicitly map any remaining upstream defaulting to P337/P339 rather than calling P336 done.
