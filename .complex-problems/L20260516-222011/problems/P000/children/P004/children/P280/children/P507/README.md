# Finalize and recovery ownership map

## Problem

P280 needs a concrete map of normal finalize, suspected-dead/watchdog, recovery archive, recovery wake creation, and remaining-stack archival paths before any ownership claim can be trusted.

## Success Criteria

- Code paths are mapped with file references and brief flow descriptions.
- The map identifies the owner for each side effect: FSM decision, session ledger, session outbox, saga compensation, Cortex archive, or worker boundary.
- Any ambiguous or multi-owner path is listed as a candidate for the remediation child.
- No production code is changed in this mapping child.
