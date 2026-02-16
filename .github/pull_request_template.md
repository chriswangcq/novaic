## Description

<!-- Brief summary of changes -->

---

## Phase 1 Decoupling Governance Checklist

> For PRs touching `gateway`, `tools_server`, `task_queue`, or `common`, complete the sections below.

### Scope / Non-goals

- **In scope:** <!-- What this PR achieves -->
- **Out of scope:** <!-- What this PR explicitly does not change -->

### Module ownership impact

<!-- Map changed paths to [GATEWAY_MODULE_OWNERSHIP.md](novaic-backend/docs/GATEWAY_MODULE_OWNERSHIP.md) -->

- [ ] Reviewed ownership mapping for modified modules
- **Touched paths → owners:**
  - <!-- e.g. novaic-backend/gateway/api/ → @novaic/gateway-core -->

| Path | Owner |
|------|-------|
| <!-- add rows as needed --> | |

### Internal API contract impact

<!-- See [INTERNAL_API_BASELINE.md](novaic-backend/docs/contracts/INTERNAL_API_BASELINE.md) -->

- [ ] No changes to internal API contract **OR** changes documented and contract tests updated
- [ ] Run contract tests: `cd novaic-backend && pytest tests/contract/ -v`

### Backward compatibility

- [ ] Existing callers remain compatible (no breaking changes to public/internal APIs)
- [ ] Database schema changes (if any): migration added and reversible

### Rollback plan

- <!-- How to revert if issues arise after merge (e.g. feature flag, redeploy previous image) -->

### Verification commands / tests

```bash
# Commands to validate this PR
# e.g. pytest, curl, manual steps
```

---

## Module checklist

Check all that apply when modifying these areas:

| Area | Touched? | Notes |
|------|----------|-------|
| `gateway` | [ ] | |
| `tools_server` | [ ] | |
| `task_queue` | [ ] | |
| `common` | [ ] | |
