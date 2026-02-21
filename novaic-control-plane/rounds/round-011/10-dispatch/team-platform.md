# Dispatch - Platform Team (Round 011 Full Remote Verification)

- objective:
  - Eliminate residual `SKIP_REMOTE` and enforce full remote commit verification coverage across all teams.

- mandatory_tasks:
  - upgrade `check_commit_reachability.py` to verify all canonical repos via GitHub remote checks (no local-clone oracle path)
  - enforce gate rule: each team must have all required commit pairs verifiable; `SKIP_REMOTE` allowed only for explicit network outage evidence
  - publish `gate_round011.sh` and updated audit outputs with deterministic PASS/FAIL markers

- acceptance_commands:
  - `python3 rounds/round-011/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `python3 rounds/round-011/split-close/repos/novaic-evidence-audit/scripts/audit_round011_reports.py`
  - `bash rounds/round-011/split-close/gate_round011.sh`

- due: `round-011`
- status: `PLANNED`
