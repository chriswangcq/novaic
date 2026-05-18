# Legacy imperative dispatch and compatibility residue cleanup

## Problem

Search for old imperative dispatch/finalize/session branches that bypass or duplicate the FSM decision path, and remove or tighten high-confidence stale residue.

## Success Criteria

- Static scan for direct SagaOrchestrator/session mutation/finalize compatibility branches is recorded.
- High-confidence stale code is removed or replaced with explicit FSM/outbox path.
- If ambiguous, create a smaller follow-up problem instead of speculative deletion.
