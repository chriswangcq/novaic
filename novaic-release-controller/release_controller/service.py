"""HTTP control plane for the NovAIC release controller."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException

from release_controller.executor import execute_planned_release
from release_controller.models import (
    ControllerConfig,
    ReleaseRun,
)
from release_controller.planner import PlannedRelease, PlanningError, ReleasePlanner
from release_controller.poller import BranchHeadProvider, BranchPoller, GitBranchHeadProvider
from release_controller.polling import BranchPollingLoop
from release_controller.runner import CommandRunner, PlanExecutionResult
from release_controller.state import ReleaseStateStore


def create_app(
    config: ControllerConfig,
    state: ReleaseStateStore | None = None,
    planner: ReleasePlanner | None = None,
    runner: CommandRunner | None = None,
    branch_head_provider: BranchHeadProvider | None = None,
) -> FastAPI:
    """Create a FastAPI app wired to release-controller dependencies."""

    store = state or ReleaseStateStore(config.state_dir)
    release_planner = planner or ReleasePlanner(config, store)
    command_runner = runner or CommandRunner()
    head_provider = branch_head_provider or GitBranchHeadProvider(config)
    polling_loop = BranchPollingLoop(
        enabled=config.polling_enabled,
        interval_seconds=config.poll_interval_seconds,
        poll_once=lambda: BranchPoller(
            config=config,
            state=store,
            planner=release_planner,
            runner=command_runner,
            provider=head_provider,
        ).poll_once(),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await polling_loop.start()
        try:
            yield
        finally:
            await polling_loop.stop()

    app = FastAPI(
        title="NovAIC Release Controller",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.extra["controller_config"] = config
    app.extra["polling_loop"] = polling_loop

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/v1/status")
    def status() -> dict[str, Any]:
        return {
            "state_dir": str(store.root),
            "branch_heads": store.read_branch_heads(),
            "current_releases": [
                pointer.to_mapping() for pointer in store.list_current_releases()
            ],
            "previous_releases": [
                pointer.to_mapping() for pointer in store.list_previous_releases()
            ],
            "candidates": [pointer.to_mapping() for pointer in store.list_candidates()],
            "recent_runs": [run.to_mapping() for run in store.list_runs(limit=20)],
            "polling": polling_loop.status(),
        }

    @app.get("/v1/rules")
    def rules() -> dict[str, Any]:
        return {"rules": [rule.to_mapping() for rule in config.branch_rules]}

    @app.get("/v1/runs")
    def runs() -> dict[str, Any]:
        return {"runs": [run.to_mapping() for run in store.list_runs()]}

    @app.get("/v1/runs/{run_id}")
    def run(run_id: str) -> dict[str, Any]:
        stored = store.get_run(run_id)
        if stored is None:
            raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
        return stored.to_mapping()

    @app.post("/v1/triggers")
    def trigger(payload: dict[str, Any]) -> dict[str, Any]:
        branch = _required_str(payload, "branch")
        commit = _required_str(payload, "commit")
        dry_run = _optional_bool(payload, "dry_run")
        try:
            planned = release_planner.plan_branch_release(branch, commit, dry_run=dry_run)
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        release_execution = execute_planned_release(store, command_runner, planned)
        final_run, execution = release_execution.run, release_execution.execution
        return _response(planned, final_run, execution)

    @app.post("/v1/polls/once")
    def poll_once(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        dry_run = _optional_bool(payload or {}, "dry_run")
        poller = BranchPoller(
            config=config,
            state=store,
            planner=release_planner,
            runner=command_runner,
            provider=head_provider,
        )
        try:
            outcomes = poller.poll_once(dry_run=dry_run)
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"outcomes": [outcome.to_mapping() for outcome in outcomes]}

    @app.post("/v1/promotions/prod")
    def promote_prod(payload: dict[str, Any]) -> dict[str, Any]:
        api_image = _required_str(payload, "api_image")
        factory_image = _required_str(payload, "factory_image")
        commit = _required_str(payload, "commit")
        dry_run = _optional_bool(payload, "dry_run")
        promoted_from = _optional_str(payload, "promoted_from")
        try:
            planned = release_planner.plan_prod_promotion(
                api_image=api_image,
                factory_image=factory_image,
                commit=commit,
                promoted_from=promoted_from,
                dry_run=dry_run,
            )
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        release_execution = execute_planned_release(
            store,
            command_runner,
            planned,
            promoted_from=promoted_from,
        )
        final_run, execution = release_execution.run, release_execution.execution
        return _response(planned, final_run, execution)

    @app.post("/v1/rollbacks/{namespace}")
    def rollback(namespace: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        dry_run = _optional_bool(payload or {}, "dry_run")
        try:
            planned = release_planner.plan_rollback(namespace, dry_run=dry_run)
        except PlanningError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        release_execution = execute_planned_release(store, command_runner, planned)
        final_run, execution = release_execution.run, release_execution.execution
        return _response(planned, final_run, execution)

    return app

def _response(
    planned: PlannedRelease,
    final_run: ReleaseRun,
    execution: PlanExecutionResult,
) -> dict[str, Any]:
    return {
        "run": final_run.to_mapping(),
        "mode": planned.mode.value,
        "namespace": planned.namespace,
        "candidate_id": planned.candidate_id,
        "execution": execution.to_mapping(),
    }


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=422, detail=f"{key} must be a non-empty string")
    return value


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=422, detail=f"{key} must be a non-empty string")
    return value


def _optional_bool(payload: Mapping[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise HTTPException(status_code=422, detail=f"{key} must be a boolean")
    return value
