# Session hidden input remediation ticket

## Problem Definition

P469 must remove or explicitly justify risky hidden inputs found by P468. The highest-risk candidates are saga decision adapters reading `ServiceConfig` directly at decision time (`react_think.py`, `react_actions.py`). Other `ServiceConfig` reads need classification as process-boundary/adapter-safe or remediation.

## Proposed Solution

Refactor risky decision-path configuration into explicit inputs at the saga/assembly boundary. Keep pure decision contracts unchanged where they already accept explicit values. For retained `ServiceConfig` reads in clients/tool adapters, document and test that they are adapter-boundary defaults rather than hidden inputs inside pure business decisions.

## Acceptance Criteria

- `react_think.py` and `react_actions.py` no longer read `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE` directly inside decision-building functions unless a source-backed reason proves it is an explicit adapter boundary.
- Any new configuration object or provider is injected and unit-testable.
- Focused tests prove different configured limits produce deterministic decisions without monkeypatching global `ServiceConfig`.
- Other retained `ServiceConfig` reads are classified with evidence.

## Verification Plan

Run focused tests for `react_think`, `react_actions`, session FSM/dispatch contracts, and hidden-input guards. Add tests if needed to cover injected config behavior.

## Risks

- Over-plumbing config could make saga definitions noisier.
- Under-fixing could leave decisions dependent on process globals.
- Changing round-cap config wiring can affect session finalization behavior.

## Assumptions

- Process startup may still read environment/config; decision functions should receive explicit snapshots.
- Existing pure contracts should remain pure and explicit.
