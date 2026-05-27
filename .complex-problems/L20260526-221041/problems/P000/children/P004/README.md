# Verify and clean up reasoning streaming end to end

## Problem

The streaming change touches multiple repos and can regress non-streaming LLM calls, saga decisions, projection privacy, or App monitor UX. The final pass must prove the path and clean up any transitional or misleading code residue.

## Success Criteria

- Focused tests pass in all touched repos.
- Cross-boundary contracts are documented or represented by tests clearly enough for future agents.
- Diff review shows no long-term fallback branch, no stale misleading path, and no accidental raw partial reasoning in LLM input history.
- The ledger contains evidence, stress testing, residual risk, and result IDs for closure.
