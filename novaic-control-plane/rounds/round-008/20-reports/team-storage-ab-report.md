# Round 008 Report - Storage-A/B Team

---

## Task 1 — code/behavior: Replace `local:` URL scheme with canonical `file:///`

### problem_fixed
Round 007 normalized URLs from `file:///Users/...` to `local:novaic-storage-[ab]`. Round 008 policy prohibits `local:` scheme entirely. Storage-A/B reports (rounds 003–007) and associated split-fix/evidence docs contained 43 non-canonical `local:` occurrences, causing canonical URL audit failures.

### solution_applied
Python scan + in-place replacement across 8 files converted every `local:novaic-storage-a` → `file:///Users/wangchaoqun/novaic/novaic-storage-a` and `local:novaic-storage-b` → `file:///Users/wangchaoqun/novaic/novaic-storage-b`. Created executable audit script `run_canonical_url_audit.sh` for repeatable machine verification. Re-scan confirmed zero remaining violations.

### target_state_proof

- type: `code/behavior`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-storage-a`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-storage-b`
- branch: `split/round-003-storage-a`
- branch: `split/round-003-storage-b`
- commit_sha: `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
- commit_sha: `c67abaf6286dd2bc369c38c51fab7f8bf4858257`
- migrated_paths: `novaic-control-plane/rounds/round-008/split-fix/run_canonical_url_audit.sh`
- command: `cd /Users/wangchaoqun/novaic && bash novaic-control-plane/rounds/round-008/split-fix/run_canonical_url_audit.sh`
- expected_marker: `LOCAL_SCHEME_VIOLATIONS=0`
- expected_marker: `CANONICAL_URL_AUDIT=PASS`
- artifact_path: `novaic-control-plane/rounds/round-008/split-fix/storage-ab-canonical-url-audit.md`
- status: `DONE`

---

## Task 2 — failure-path: Assert retry-stop on max-attempt breach

### problem_fixed
The existing failure-injection test only proved successful retries when Storage-A eventually came back online. There was no test asserting that the resolver stops at exactly `STORAGE_B_RESOLVE_MAX_RETRIES` attempts when Storage-A is permanently offline, leaving the retry-stop boundary unverified.

### solution_applied
Created `novaic-storage-b/scripts/failure_injection_max_attempt_breach.sh`. It starts Storage-B pointed at a permanently offline port, creates a tool result referencing the dead URL, calls `for-llm`, then asserts: (1) `RETRY_MAX_BREACH_RESOLVER_NULL=PASS` — no `image_url` in response, confirming resolver returned `None` gracefully; (2) `RETRY_MAX_BREACH_ATTEMPTS_SEEN=3` — log contains exactly 3 retry-attempt lines; (3) `RETRY_MAX_BREACH_STOP=PASS` — no attempt number exceeds max. Committed at `c67abaf6286dd2bc369c38c51fab7f8bf4858257`.

### target_state_proof

- type: `failure-path`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-storage-b`
- branch: `split/round-003-storage-b`
- commit_sha: `c67abaf6286dd2bc369c38c51fab7f8bf4858257`
- migrated_paths: `novaic-storage-b/scripts/failure_injection_max_attempt_breach.sh`
- command: `cd /Users/wangchaoqun/novaic/novaic-storage-b && bash scripts/failure_injection_max_attempt_breach.sh`
- expected_marker: `RETRY_MAX_BREACH_RESOLVER_NULL=PASS`
- expected_marker: `RETRY_MAX_BREACH_ATTEMPTS_SEEN=3`
- expected_marker: `RETRY_MAX_BREACH_STOP=PASS`
- artifact_path: `novaic-storage-b/artifacts/storage-ab-max-attempt-breach-latest.md`
- status: `DONE`

---

## Task 3 — operability: Non-author replay package with canonical URL map

### problem_fixed
Round 007 replay script predated Round 008 canonical URL policy, lacked the max-attempt breach step, and used a `grep -q` pipeline that triggered SIGPIPE on PASS (causing false FAIL in bundle runs). No single reproducible package existed for non-author verification of the complete Round 008 evidence chain.

### solution_applied
Created `novaic-control-plane/rounds/round-008/20-reports/storage_ab_round008_replay_bundle.sh`. It runs 5 steps (Storage-A smoke, Storage-B restore, Storage-B smoke, cross-repo retry injection, max-attempt breach), uses temp-file output buffering to avoid SIGPIPE false failures, and embeds a canonical URL map header. Verified at 2026-02-21T02:53:42Z: `STEPS_PASSED=5`, `STEPS_FAILED=0`.

### target_state_proof

- type: `operability`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-storage-a`
- repo_url: `file:///Users/wangchaoqun/novaic/novaic-storage-b`
- branch: `split/round-003-storage-a`
- branch: `split/round-003-storage-b`
- commit_sha: `b7cde077160cb3cfdeb03ba845e5a05cde1f82c7`
- commit_sha: `c67abaf6286dd2bc369c38c51fab7f8bf4858257`
- migrated_paths: `novaic-control-plane/rounds/round-008/20-reports/storage_ab_round008_replay_bundle.sh`
- command: `cd /Users/wangchaoqun/novaic && bash novaic-control-plane/rounds/round-008/20-reports/storage_ab_round008_replay_bundle.sh`
- expected_marker: `REPLAY_STORAGE_A_SMOKE=PASS`
- expected_marker: `REPLAY_STORAGE_B_RESTORE=PASS`
- expected_marker: `REPLAY_STORAGE_B_SMOKE=PASS`
- expected_marker: `REPLAY_RETRY_INJECTION=PASS`
- expected_marker: `REPLAY_MAX_BREACH=PASS`
- expected_marker: `STEPS_PASSED=5`
- expected_marker: `STEPS_FAILED=0`
- expected_marker: `STORAGE_AB_ROUND008_REPLAY=PASS`
- artifact_path: `novaic-control-plane/rounds/round-008/20-reports/storage_ab_round008_replay_bundle.sh`
- status: `DONE`

---

## questions_for_program_owner

- question: Should `file:///` absolute paths remain the canonical `repo_url` form for all future rounds, or is migration to `https://github.com/<org>/<repo>` required before a specific round?
- why_blocking: Two consecutive rounds changed URL policy in opposite directions (round-007: `file:///` → `local:`; round-008: `local:` → `file:///`). If policy will change again to `https://`, teams need the target org/repo names now to avoid a third normalization sweep.
- options:
  - Keep `file:///` as canonical for local repos indefinitely.
  - Declare GitHub migration mandatory by a specific round, provide org/repo names now.
  - Allow both `file:///` and `https://` as long as the value is stable within a repo's lifetime.
- recommended_option: Option 2 — declare GitHub migration target and round now, so teams can migrate once cleanly.
- impact_if_unanswered: Risk of a third URL normalization sweep across all historical reports in a future round.
- requested_by_round: `round-008`

---

## Team status
- status: `DONE`
- blocker: `none`
