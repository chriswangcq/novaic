# P351 Check: Recovery Compensation Finalize Identity

## Verdict

`success`

## Criteria Map

- Source map compensation/recovery finalize paths: satisfied by P361.
- Preserve positive session generation through wake-finalize compensation: satisfied by P362.
- Reject or skip missing/invalid identity in recovery archive path: satisfied by P363.
- Aggregate verification with strict residue checks: satisfied by P364 and follow-up P365.

## Evidence

- `queue_service/saga_repo.py` compensation helper requires positive `session_generation` before creating `wake_finalize`.
- `queue_service/session_recovery.py` carries generation from `SESSION_SUSPECTED_DEAD` into recovery archive effect only when positive.
- `queue_service/session_outbox.py` validates recovery archive generation before publishing `CORTEX_SCOPE_END`.
- `queue_service/session_rebuild.py` skips startup rebuild contexts without positive explicit generation.
- Final aggregate verification after follow-up: `96 passed in 0.71s`.

## Stress Test

The check did not stop at direct recovery archive paths. It also checked saga failure compensation, wake-finalize failure recovery, startup session rebuild, and stale test residue. The discovered startup fallback was repaired under P365 before this parent was accepted.

## Residual Risk

No P351-scoped known residual risk remains. The remaining `generation or 0` occurrences seen during search are runtime-state no-active sentinels or non-finalize state reads, not synthesis of finalize mutation identity.
