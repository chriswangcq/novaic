# Session-ended delivery tests compatibility cleanup result

## Summary

No P336 delivery test currently blesses zero-generation session-ended/finalize delivery as valid. The direct delivery tests now assert rejection for missing/zero generation. Remaining zero-generation test matches are either expected rejection tests, no-active FSM state tests, pending projection metadata tests, or upstream react contract defaults delegated to P347/P337/P339.

## Done

- Searched tests for zero-generation residue:
  - `session_generation=0`
  - `"session_generation": 0`
  - `generation=0`
  - `"generation": 0`
- Inspected relevant matches:
  - `test_pr254_finalize_ownership.py` zero-generation cases are rejection tests for repository, wake-finalize payload, handler, SagaClient, and route.
  - `test_runtime_explicit_contracts.py` still asserts `ReactThinkInput` default `session_generation=0`; this is upstream react contract residue and belongs to P347/P337/P339, not P336 delivery tests.
  - Other zero-generation matches are no-active FSM state, pending projection metadata, or unrelated generic FSM tests.
- No P336 delivery-boundary test needed removal.

## Verification

- Ran `rg -n 'session_generation\\s*=\\s*0|"session_generation"\\s*:\\s*0|generation\\s*=\\s*0|"generation"\\s*:\\s*0' novaic-agent-runtime/tests -g '*.py'`.
- Inspected direct delivery and upstream react matches with `nl -ba`.
- Ran `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr254_finalize_ownership.py tests/test_runtime_explicit_contracts.py`.
- Result: `22 passed in 0.27s`.

## Known Gaps

- `test_runtime_explicit_contracts.py` and the underlying react contract defaults remain upstream work; P347 will classify and decide whether that is a blocker for P336 parent success.

## Artifacts

- Search evidence in tests.
- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
- `novaic-agent-runtime/tests/test_runtime_explicit_contracts.py`
