# Phase 5D.4 full Cortex test and pycompile gate

## Problem Definition

`P064` is the broad final verification gate for Phase 5 cleanup. It must compile the live Cortex Python package and run the full `novaic-cortex/tests` suite after all static, guard, and targeted state-authority checks.

## Proposed Solution

- Run `python3 -m py_compile` across every Python file under `novaic-cortex/novaic_cortex`.
- Run the full `novaic-cortex/tests` suite with explicit sibling-package `PYTHONPATH`.
- Record exact command output, duration summary, and any failures.
- If failures occur, triage them as remediation-caused, pre-existing, or environment/setup issues in the result body.
- Clean generated `__pycache__` directories after the verification commands.

## Acceptance Criteria

- Cortex package pycompile succeeds.
- Full Cortex pytest suite succeeds, or failures are honestly recorded and triaged.
- Exact commands and output summaries are recorded.
- Generated cache residue is cleaned after the run.

## Verification Plan

```bash
find novaic-cortex/novaic_cortex -name '*.py' -print0 | xargs -0 python3 -m py_compile
PYTHONPATH="novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk" pytest -q novaic-cortex/tests
find novaic-cortex novaic-agent-runtime -type d -name __pycache__ -prune -exec rm -rf {} +
```

## Risks

- Full suite may expose unrelated pre-existing failures; record and classify rather than burying them.
- The suite may be slower than targeted gates; allow enough timeout and do not replace it with a smaller subset.

## Assumptions

- Network is not required for the unit suite; Redis-related behavior is covered via fakes/mocks or startup validation tests.
