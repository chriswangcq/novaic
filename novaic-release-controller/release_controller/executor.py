"""Shared release execution flow for API and poller entrypoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from release_controller.models import ReleaseMode, ReleasePointer, ReleaseRun, RunStatus
from release_controller.planner import PlannedRelease
from release_controller.runner import CommandRunner, PlanExecutionResult
from release_controller.state import ReleaseStateStore


@dataclass(frozen=True)
class ReleaseExecution:
    """Final run and command execution details for a planned release."""

    run: ReleaseRun
    execution: PlanExecutionResult


def execute_planned_release(
    store: ReleaseStateStore,
    runner: CommandRunner,
    planned: PlannedRelease,
    promoted_from: str | None = None,
) -> ReleaseExecution:
    """Persist, execute, and finalize one planned release."""

    store.put_run(planned.run)
    execution = runner.run(planned.plan)
    status = RunStatus.SUCCEEDED if execution.succeeded else RunStatus.FAILED
    final_run = replace(
        planned.run,
        status=status,
        failure=execution.failure,
        finished_at=_now(),
    )
    store.put_run(final_run)
    if execution.succeeded and not planned.plan.dry_run:
        _persist_success_pointer(store, planned, final_run, promoted_from)
    return ReleaseExecution(run=final_run, execution=execution)


def _persist_success_pointer(
    store: ReleaseStateStore,
    planned: PlannedRelease,
    final_run: ReleaseRun,
    promoted_from: str | None,
) -> None:
    if planned.images is None:
        return
    pointer = ReleasePointer(
        namespace=planned.namespace or "candidate",
        commit=final_run.commit,
        images=planned.images,
        run_id=final_run.run_id,
        promoted_from=promoted_from,
        updated_at=final_run.finished_at or _now(),
    )
    if planned.mode is ReleaseMode.CANDIDATE_ONLY and planned.candidate_id:
        store.put_candidate(planned.candidate_id, pointer)
    elif planned.namespace:
        store.update_namespace_release(pointer)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
