# Tools Probe — Runner OS Support Policy

**Status: FINAL**
**Policy version: v1.0.0 (finalized 2026-02-19)**
**Owner: Tools Team**
**Review trigger: addition of a non-Linux CI runner**

---

## 1. Supported Environments

| Environment              | `lsof`/`pgrep` source                         | Probe supported |
|--------------------------|-----------------------------------------------|-----------------|
| Ubuntu/Debian Linux (CI) | Auto-installed by `ci_preflight_probe_prereqs.sh` | **YES**     |
| macOS local dev          | Native OS binaries (no install required)      | **YES**         |
| Non-Linux CI runner      | No auto-install path                          | **NO**          |

## 2. Chosen Strategy: Option A (Fail-Fast, No Fallback)

The probe script (`leak_probe.sh`) relies on `lsof` and `pgrep` for OS-level resource
measurement. Rather than fall back to an estimated or degraded check when these binaries
are absent, the probe exits immediately with a human-readable error.

**Rationale for Option A over alternatives:**

- **Option B (Python fallback)**: `psutil` or `/proc` approximations diverge from
  `lsof`-measured truth on some Linux kernels. Accepting approximate measurements
  defeats the purpose of an OS-level leak gate.
- **Option C (pure Python probe)**: Eliminates OS measurement entirely. Acceptable only
  as a companion to Option A, not a replacement.
- **Current runner matrix**: Ubuntu-only. No macOS or Windows CI runners exist or are
  planned. Maintenance cost of multi-OS fallback exceeds benefit at this time.

## 3. CI Integration

1. The `python` job in `.github/workflows/ci.yml` calls
   `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh` before running the probe.
2. The preflight script installs `lsof` (package `lsof`) and `pgrep` (package `procps`)
   via `apt-get` on Ubuntu/Debian.
3. If either binary cannot be installed, the preflight exits non-zero and the probe step
   is blocked — no silent pass.

## 4. Non-Linux Runner Expansion Path

If a macOS or Windows CI runner is added:

1. Open a tracking issue: "Extend probe prereqs for <OS>".
2. Add an OS-detection branch to `ci_preflight_probe_prereqs.sh`:
   - **macOS**: no install needed (`lsof`/`pgrep` are native).
   - **Windows**: add Chocolatey/winget branch; note `lsof` has no native Windows
     equivalent — consider WSL or skip probe.
3. Update this document's table and bump `Policy version`.
4. Gate the PR on `tests/unit/tools_server/test_policy_doc_sync.py` passing.

## 5. Long-Term Maintenance Rules

- This file (`RUNNER_SUPPORT_POLICY.md`) is the single source of truth for runner OS
  support. Round-specific reports may reference it but must NOT re-define the policy.
- Any change to supported OS list MUST update both this file AND
  `tools_server/RELIABILITY_POLICY.md` (Environment Dependency Policy section).
- The sync-check test `tests/unit/tools_server/test_policy_doc_sync.py` is a mandatory
  CI gate: it fails if key policy tokens diverge between this file, the RELIABILITY_POLICY,
  and `ci_preflight_probe_prereqs.sh`.

## 6. Related Files

| File | Role |
|------|------|
| `scripts/tools/leak_probe.sh` | OS-level probe; uses `lsof` + `pgrep` |
| `scripts/tools/ci_preflight_probe_prereqs.sh` | Installs prereqs on CI Linux runner |
| `tools_server/RELIABILITY_POLICY.md` | Full reliability policy incl. env dep section |
| `tests/unit/tools_server/test_policy_doc_sync.py` | CI sync-check test |
| `.github/workflows/ci.yml` | CI pipeline calling preflight + probe |
