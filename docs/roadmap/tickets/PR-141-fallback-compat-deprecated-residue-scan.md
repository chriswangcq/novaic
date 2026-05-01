# PR-141 — Fallback / Compatibility / Deprecated Branch Residue Scan

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | all active source repos |
| Depends on | PR-140 |

## Goal

Find fallback or compatibility branches that preserve old behavior after the new path is already authoritative. The target is not every defensive error path; the target is dual behavior that increases maintenance entropy.

## Scan Plan

1. [x] Search active code for `fallback`, `compat`, `deprecated`, `legacy`, `old path`, and related terms.
2. [x] Classify hits as real old branch, defensive validation, test archaeology, or doc-only.
3. [x] Mark delete-now candidates separately from intentionally retained migration guards.
4. [x] Identify candidates for new CI guardrails.

## Findings

- Clear delete candidates overlapping PR-140:
  - `novaic-agent-runtime/main_saga.py` hidden Runtime Orchestrator argument.
  - `novaic-agent-runtime/config/services.schema.json` `tools_server` residue.
  - `novaic-common/common/tools/__init__.py` `tools_server` docstring.
  - App Runtime Orchestrator startup/config residue.
- Additional active compatibility branches that need owner decisions:
  - `novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py` has QUEUE_SERVICE_URL fallback wording.
  - `novaic-business/business/internal/agent.py` has a tool-registry compatibility fallback.
  - `novaic-business/business/internal/helpers.py` supports a legacy SubAgent dataclass.
  - `novaic-business/business/internal/subagent_utils.py` contains concurrency fallback language.
  - `novaic-device/device/agent_binding.py` supports legacy list format for `mounted_tools`.
  - `novaic-device/device/vm_routes.py` falls back to `agent.vm.ports`.
  - `novaic-gateway/gateway/infra/auth.py` has Clerk RS256 to HS256 fallback and query-token fallback.
  - `novaic-gateway/services/health_routes.py` has desktop-bootstrap compatibility behavior.
  - `novaic-common/common/auth.py` keeps an ignored `db` parameter for backward compatibility.
  - `novaic-common/common/db/database.py` and `novaic-gateway/gateway/db/access.py` keep compatibility aliases.
- Test-only, generated, dependency-lock, Android/QEMU, and third-party hits were classified as noise.

## Follow-up Decision

Split cleanup into two classes: delete obvious old product paths first, then review security/transport defensive fallbacks individually before removal. Do not keep compatibility branches without an explicit current invariant.

## Unit / Guardrail Tests

- [x] Added `novaic-business/tests/test_pr141_compat_cleanup.py` for removed tools-config fallback route and dict-only SubAgent conversion.
- [x] Added `novaic-common/tests/test_pr141_no_compat_aliases.py` for removed auth/db compatibility aliases.
- [x] Added `novaic-device/tests/test_pr141_no_common_auth_db_param.py` for removed ignored auth db parameter usage.
- [x] Added `novaic-gateway/tests/test_pr141_no_db_access_alias.py` for removed gateway db alias.
- [x] Ran all PR-141 tests in affected repos.

## Smoke / Deploy

- [x] Removed no-owner compatibility paths: Business tools-config fallback route, legacy SubAgent dataclass conversion, ignored common auth `db` parameter, common `fetch_all` alias, and gateway `get_database` alias.
- [x] Reworded Runtime/Business comments that preserved deleted fallback history as live-looking guidance.
- [ ] Deploy with the final batch.

## Git / Merge

- [ ] Commit cleanup.
- [ ] Push cleanup.

## Closure — 2026-05-01

PR-141 is implemented for the delete-now class. Remaining hits are either defensive error paths, third-party/QEMU resources, security/transport behavior that needs its own owner decision, or explicitly covered by later residue tickets.
