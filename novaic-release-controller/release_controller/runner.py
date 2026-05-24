"""Command runner boundary for release-controller plans."""

from __future__ import annotations

import os
import subprocess

from release_controller.models import CommandPlan, CommandResult, CommandStep, PlanExecutionResult


class CommandRunner:
    """Execute command plans while keeping dry-run behavior testable."""

    def run(self, plan: CommandPlan) -> PlanExecutionResult:
        results: list[CommandResult] = []
        for step in plan.steps:
            if plan.dry_run:
                results.append(self._dry_run_result(step))
                continue
            result = self._run_step(step)
            results.append(result)
            if result.exit_code != 0:
                break
        return PlanExecutionResult(dry_run=plan.dry_run, results=tuple(results))

    def _dry_run_result(self, step: CommandStep) -> CommandResult:
        return CommandResult(
            name=step.name,
            argv=step.argv,
            exit_code=0,
            stdout="dry-run: command not executed",
            skipped=True,
        )

    def _run_step(self, step: CommandStep) -> CommandResult:
        env = os.environ.copy()
        env.update(step.env)
        completed = subprocess.run(
            step.argv,
            cwd=step.cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(
            name=step.name,
            argv=step.argv,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
