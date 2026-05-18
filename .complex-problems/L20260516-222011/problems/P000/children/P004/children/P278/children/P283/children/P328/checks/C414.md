# Finalize/session-ended generation ownership audit check

## Summary

`P328` is successful. The original risk was that stale finalize/session-ended/watchdog/recovery/nested-skill closure events could clear, restart, or archive a newer active session. The split work closed the boundary across inventory, repository/FSM mutation, outbox delivery, runtime handlers, archive diagnostics, and aggregate source/test guards.

## Evidence

- `R388` summarizes all six successful child branches.
- `C341` maps finalize/session-ended entry points and identifies downstream risk targets.
- `C342` verifies repository/FSM generation checks occur at the mutation boundary.
- `C351` verifies session-ended delivery preserves explicit generation identity and rejects malformed delivery payloads.
- `C371` verifies runtime handler enforcement and aggregate focused test closure.
- `C385` verifies finalize reason and remaining stack archive binding.
- `C413` verifies aggregate regression coverage, clean narrow source guard, and fully classified widened guard.

## Criteria Map

- Map all finalize/session-ended entry points and generation/session keys: satisfied by `P334` / `R320` / `C341`.
- Verify current-generation checks before clearing active state, restarting pending input, or archiving remaining stack: satisfied by `P335`, `P336`, `P337`, and `P338`.
- Identify whether remaining stack and reason are recorded at the generation boundary: satisfied by `P338` / `R362` / `C385`.
- Add or identify tests proving stale finalize/session-ended events do not close the wrong active generation: satisfied by `P335`, `P336`, `P337`, `P338`, and final aggregate `P339`.
- Remove stale compatibility behavior that silently falls back to generation `1` or current active generation: satisfied by `P339` / `C413`, including the follow-up chain that fixed guard-discovered live residue.

## Execution Map

- `T324` split into `P334`-`P339`.
- `P334` established the inventory and found the initial generation-zero/fallback risk.
- `P335` closed repository/FSM finalize atomicity.
- `P336` closed session-ended outbox delivery generation contracts.
- `P337` closed runtime handler enforcement and upstream React/runtime finalize paths.
- `P338` closed remaining-stack/finalize-reason archive identity binding.
- `P339` ran the aggregate regression/guard closure and followed multiple not-success checks until no live unclassified generation residue remained.

## Stress Test

- This was not accepted as a one-go result. Several child checks deliberately rejected partial results and created follow-ups.
- The cross-repo branch initially failed with live generation coercion residue; later checks fixed those paths and reran guards.
- The final widened guard remained broad enough to catch non-session false positives, which were classified instead of removed from visibility.

## Residual Risk

- Non-blocking: generic FSM generations, retry counters, health counters, round numbers, and audit/projection adapters remain. They are explicitly classified as outside finalize/session-ended session-generation authority.
- No blocking acceptance-criteria gap remains for `P328`.

## Result IDs

- `R388`
- Supporting evidence: `R320`, `R321`, `R330`, `R349`, `R362`, `R387`
