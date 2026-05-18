# Map ContextEvent stream and read model

## Problem Definition

ContextEvent projection is supposed to be the authoritative cross-wake LLM context source. We need to verify and record its actual active behavior: append-only storage, deterministic replay, projected messages, folded skill summaries, active stack snapshot, and budgeted read-model output.

## Proposed Solution

Inspect and map:

- `ContextEventStore.event_log_path/read_events/append_event/initialize_root`
- `project_context_events` and event handlers in `context_event_projection.py`
- `ContextEventReadModel.prepare` and `_top_first_stack`

Run the existing tests that exercise these paths. If an active mismatch or stale duplicate path is found, record it as a follow-up child problem rather than hiding it inside a broad result.

## Acceptance Criteria

- The result identifies the event log path and storage format.
- The result explains event replay validation, sequence/root/stream invariants, projected message handling, skill open/close behavior, and tool result projection metadata at this layer.
- The result explains how read-model output differs from raw projection output, including budget compaction and top-first stack normalization.
- Relevant tests are run and their evidence is recorded.
- Any active issue found is fixed if small and local, or split into a follow-up.

## Verification Plan

- Run:
  - `PYTHONPATH=novaic-cortex pytest -q novaic-cortex/tests/test_context_event_store.py`
  - `PYTHONPATH=novaic-cortex pytest -q novaic-cortex/tests/test_context_event_projection.py`
  - `PYTHONPATH=novaic-cortex pytest -q novaic-cortex/tests/test_context_event_read_model.py`
- If import paths require adjacent packages, include `novaic-common`, `novaic-logicalfs`, and `novaic-sandbox-sdk` in `PYTHONPATH`.
- Use narrow `rg`/`sed` source pointers in the result.

## Risks

- This child problem should not drift into runtime prepare-context or display projection; those have separate child problems.
- Some projection behavior around system-message insertion may be intentional and should be documented before being modified.

## Assumptions

- Event store append requires explicit clock and id providers by design.
- Empty event streams require reset rather than silently falling back to legacy context assembly.
