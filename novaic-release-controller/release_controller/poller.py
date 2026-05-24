"""Branch head polling for the NovAIC release controller."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess
from typing import Protocol

from release_controller.executor import execute_planned_release
from release_controller.models import ControllerConfig, TriggerKind
from release_controller.planner import PlanningError, ReleasePlanner
from release_controller.runner import CommandRunner
from release_controller.state import ReleaseStateStore


@dataclass(frozen=True)
class BranchHead:
    """A concrete branch head commit."""

    branch: str
    commit: str


class BranchHeadProvider(Protocol):
    """Source of concrete branch heads."""

    def list_heads(self) -> tuple[BranchHead, ...]:
        ...


@dataclass(frozen=True)
class PollOutcome:
    """Result for one branch observed during a poll iteration."""

    branch: str
    commit: str
    status: str
    reason: str | None = None
    run_id: str | None = None

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "branch": self.branch,
            "commit": self.commit,
            "status": self.status,
            "reason": self.reason,
            "run_id": self.run_id,
        }


class GitBranchHeadProvider:
    """Branch head provider backed by `git ls-remote --heads`."""

    def __init__(self, config: ControllerConfig) -> None:
        self.config = config

    def list_heads(self) -> tuple[BranchHead, ...]:
        target = self.config.repo.url or self.config.repo.remote
        completed = subprocess.run(
            ("git", "ls-remote", "--heads", target),
            cwd=self.config.repo.path,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "git ls-remote failed")
        return parse_ls_remote_heads(completed.stdout)


class InMemoryBranchHeadProvider:
    """Test provider with fixed branch heads."""

    def __init__(self, heads: tuple[BranchHead, ...]) -> None:
        self._heads = heads

    def list_heads(self) -> tuple[BranchHead, ...]:
        return self._heads


class BranchPoller:
    """Run one branch polling iteration and execute changed heads."""

    def __init__(
        self,
        config: ControllerConfig,
        state: ReleaseStateStore,
        planner: ReleasePlanner,
        runner: CommandRunner,
        provider: BranchHeadProvider,
    ) -> None:
        self.config = config
        self.state = state
        self.planner = planner
        self.runner = runner
        self.provider = provider

    def poll_once(self, dry_run: bool | None = None) -> tuple[PollOutcome, ...]:
        known_heads = self.state.read_branch_heads()
        outcomes: list[PollOutcome] = []
        for head in self.provider.list_heads():
            if not self._matches_any_rule(head.branch):
                outcomes.append(
                    PollOutcome(
                        branch=head.branch,
                        commit=head.commit,
                        status="skipped",
                        reason="unmatched branch",
                    )
                )
                continue
            if known_heads.get(head.branch) == head.commit:
                outcomes.append(
                    PollOutcome(
                        branch=head.branch,
                        commit=head.commit,
                        status="skipped",
                        reason="unchanged branch head",
                    )
                )
                continue
            try:
                planned = self.planner.plan_branch_release(
                    branch=head.branch,
                    commit=head.commit,
                    trigger=TriggerKind.POLL,
                    dry_run=dry_run,
                )
                execution = execute_planned_release(self.state, self.runner, planned)
            except PlanningError as exc:
                outcomes.append(
                    PollOutcome(
                        branch=head.branch,
                        commit=head.commit,
                        status="failed",
                        reason=str(exc),
                    )
                )
                continue
            if execution.execution.succeeded:
                self.state.write_branch_head(head.branch, head.commit)
                outcomes.append(
                    PollOutcome(
                        branch=head.branch,
                        commit=head.commit,
                        status="planned",
                        run_id=execution.run.run_id,
                    )
                )
            else:
                outcomes.append(
                    PollOutcome(
                        branch=head.branch,
                        commit=head.commit,
                        status="failed",
                        reason=execution.execution.failure,
                        run_id=execution.run.run_id,
                    )
                )
        return tuple(outcomes)

    def _matches_any_rule(self, branch: str) -> bool:
        try:
            self.planner.match_branch_rule(branch)
        except PlanningError:
            return False
        return True


def parse_ls_remote_heads(output: str) -> tuple[BranchHead, ...]:
    heads: list[BranchHead] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not parts[1].startswith("refs/heads/"):
            continue
        heads.append(BranchHead(branch=parts[1].removeprefix("refs/heads/"), commit=parts[0]))
    return tuple(heads)
