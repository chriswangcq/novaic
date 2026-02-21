# Dispatch - Storage-A/B Team (Round 011 Full Remote Verification)

- objective:
  - Validate storage contract and retry-boundary behavior using only canonical remote repos.

- mandatory_tasks:
  - run contract-version checks for both `https://github.com/chriswangcq/novaic-storage-a` and `https://github.com/chriswangcq/novaic-storage-b`
  - replay max-attempt breach failure path and prove deterministic stop boundary markers
  - publish round-011 replay bundle with clean-clone setup and full A/B chain

- acceptance_commands:
  - `bash scripts/verify_contract_version_a.sh`
  - `bash scripts/verify_contract_version_b.sh`
  - `bash scripts/failure_injection_max_attempt_breach.sh`

- due: `round-011`
- status: `PLANNED`
