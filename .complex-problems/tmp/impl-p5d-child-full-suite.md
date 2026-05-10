# Phase 5D.4 Full Cortex Test And PyCompile Gate

## Problem

Run the full `novaic-cortex/tests` suite and Cortex module `py_compile` after static and targeted verification. This is the final broad behavior gate for Phase 5 cleanup.

This belongs under P048 because full-suite verification is independently expensive and should not be hidden inside a vague one-go result.

## Success Criteria

- Run `python3 -m py_compile` across `novaic-cortex/novaic_cortex`.
- Run full `pytest -q novaic-cortex/tests`.
- Record exact command outputs.
- If failures occur, triage whether they are caused by this remediation chain, pre-existing unrelated failures, or environment issues; create follow-up work for caused failures.
