# PR-256 Reliable Evolution FSM-09 Architecture Ledger Calibration

Status: `[x]` closed

## Goal

Update the active architecture ledger after PR-251..PR-255 so future agents do
not treat historical shadow/observe-only migration notes as current work.

## Scope

- Refresh `docs/architecture/agent-loop-control-plane-consistency.md` current
  state sections for PR-251..PR-255.
- Mark old shadow/observe-only wording as historical phase notes where it is
  intentionally retained.
- Update cleanup/verification commands so they match the current runtime shape.

## Out Of Scope

- Runtime code changes belong to PR-257.
- Historical ticket archaeology files may keep old wording if they are clearly
  historical and not current backlog.

## Small Tickets

- [x] **FSM-09-A Current status ledger**: add PR-251..PR-255 as closed current
  state and remove stale "still pending" lines.
- [x] **FSM-09-B Active-session note**: state that `tq_active_sessions` is the
  remaining table residue and is owned by PR-257.
- [x] **FSM-09-C Guard commands**: update residue checks for direct publish,
  legacy dispatch, and active-session table.
- [x] **FSM-09-D Review**: verify no active doc says wake creation, dispatch
  FSM cutover, or finalize ownership is still pending.

## Explicit Dependency Boundary Review

Verdict: target compliant.

Boundary:
- Core under review: documentation describing session harness state authority.
- Allowed imperative shell: repo search commands used for verification.

Hidden inputs found:
- None in runtime logic. The risk is documentation drift: future agents may
  infer a fake dependency on old shadow/observe-only state from stale text.

Required fixes:
- Make current state explicit in the active architecture ledger.
- Keep historical migration phases labeled as history instead of active truth.

Residual risks:
- None for PR-256 after PR-257 closure. Historical sections intentionally keep
  old phase wording, but each retained occurrence is labeled as historical or
  followed by the PR that removed the old path.

## Verification

- `rg` active architecture doc for stale "仍待/未切流/observe-only/direct create"
  claims around PR-251..PR-257.
- `git diff --check`

## Review Result

Pass. The active ledger now states PR-251..PR-257 as implemented, labels
observe-only/direct-publish text as historical migration notes, and points the
residue guard at live runtime sources instead of treating historical docs as
current behavior.

## Rollback

Revert PR-256 doc changes only.
