# Round 011 Charter

## Window
- Round ID: `round-011`
- Round status: `ACTIVE`
- Cadence notes: follows round-010 PASS; promotes commit reachability from local-clone oracle to full SSH remote verification

## Objective
- Replace the Round 010 local-clone oracle in `check_commit_reachability.py` with SSH `git ls-remote` against the actual GitHub remote. Every reported `commit_sha` must be verifiable as a ref tip (REACHABLE) or flagged as UNREACHABLE when the remote answers but the SHA is absent. SKIP_REMOTE is only permitted when SSH itself fails (genuine network outage).

## Scope
- Platform: upgrade reachability script, add SSH-based negative fixture, publish gate_round011.sh
- All teams: update commit_sha values to real remote HEAD SHAs so all pairs resolve to REACHABLE

## Out of Scope
- Code feature work in split repos
- Migrating new paths beyond what is needed to pass the gate

## Success Criteria
- `bash rounds/round-011/split-close/gate_round011.sh` exits 0 and prints `ROUND011_GATE_RUNNER_PASS`
- All 7 teams have reachable_count >= 1 and unreachable_count = 0
- SKIP_REMOTE count = 0 (SSH reaches all repos)
