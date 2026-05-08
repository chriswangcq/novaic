# Add targeted regression tests

## Problem Definition

The code repair needs tests that guard the exact production failure modes: implicit 5s dispatch timeout, transient SQLite busy/locked surfacing from the generic FSM store, and claim endpoints returning plaintext 500s for transient SQLite busy.

## Proposed Solution

Add focused tests in existing test modules:

- `novaic-common/tests/test_assembler_sync.py` for DispatchAssembler client timeout.
- `novaic-agent-runtime/tests/test_pr259_generic_fsm_store_outbox.py` for bounded SQLite busy retry.
- A queue-service route test for task/saga claim busy handling.

## Acceptance Criteria

- Tests are small and deterministic.
- Tests do not require production services.
- Targeted tests pass locally.

## Verification Plan

- Run the new/modified test files with pytest.
- Run compile check if needed.

## Risks

- Existing tests may rely on exact fake client signatures; adjust fakes minimally.

## Assumptions

- Pytest environment for the two subrepos is already available from previous work.
