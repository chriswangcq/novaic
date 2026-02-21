# Dispatch - Agent Runtime Team (Round 011 Full Remote Verification)

- objective:
  - Keep tiered concurrency evidence stable and fully verifiable from canonical remote repo.

- mandatory_tasks:
  - run unit-tier replay tests from clean clone of `https://github.com/chriswangcq/novaic-agent-runtime`
  - keep dedup failure-path replay deterministic with required tier markers
  - publish round-011 evidence bundle with CI-ready commands and remote commit proof

- acceptance_commands:
  - `PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py`
  - `PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py`

- due: `round-011`
- status: `PLANNED`
