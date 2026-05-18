# Shell Output and Desc Contract Audit Ticket

## Problem Definition

Shell execution must expose bounded terminal text, accept/use `desc` for monitor clarity, and avoid leaking raw binary/base64 into LLM-visible history.

## Proposed Solution

Inspect runtime shell handler and tests, scan for desc/truncation coverage, add cleanup or tests if a gap is found, and run focused verification.

## Acceptance Criteria

- Shell output contract inspected.
- `desc` behavior inspected.
- Truncation/bounded terminal text behavior inspected.
- Tests run or gaps fixed.

## Verification Plan

- Code/test scans around shell handler and output contract.
- Focused pytest for shell output contract tests.
