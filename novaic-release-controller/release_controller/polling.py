"""Autonomous branch polling loop for the release controller."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from release_controller.poller import PollOutcome

PollOnce = Callable[[], tuple[PollOutcome, ...]]


class BranchPollingLoop:
    """Run branch polling periodically inside the controller process."""

    def __init__(
        self,
        *,
        enabled: bool,
        interval_seconds: int,
        poll_once: PollOnce,
    ) -> None:
        self.enabled = enabled
        self.interval_seconds = interval_seconds
        self._poll_once = poll_once
        self._task: asyncio.Task[None] | None = None
        self._iteration_count = 0
        self._last_started_at: str | None = None
        self._last_finished_at: str | None = None
        self._last_error: str | None = None
        self._last_outcomes: tuple[dict[str, Any], ...] = ()

    async def start(self) -> None:
        """Start the polling loop when enabled."""

        if not self.enabled or self._is_running:
            return
        self._task = asyncio.create_task(self._run(), name="release-controller-branch-poller")

    async def stop(self) -> None:
        """Stop the polling loop if it is running."""

        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    def status(self) -> dict[str, Any]:
        """Return a small operational snapshot for `/v1/status`."""

        return {
            "enabled": self.enabled,
            "running": self._is_running,
            "interval_seconds": self.interval_seconds,
            "iteration_count": self._iteration_count,
            "last_started_at": self._last_started_at,
            "last_finished_at": self._last_finished_at,
            "last_error": self._last_error,
            "last_outcomes": list(self._last_outcomes),
        }

    @property
    def _is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run(self) -> None:
        while True:
            await self._run_once()
            await asyncio.sleep(self.interval_seconds)

    async def _run_once(self) -> None:
        self._last_started_at = _now()
        try:
            outcomes = await asyncio.to_thread(self._poll_once)
            self._last_outcomes = tuple(outcome.to_mapping() for outcome in outcomes)
            self._last_error = None
        except Exception as exc:  # pragma: no cover - defensive status capture
            self._last_error = str(exc)
            self._last_outcomes = ()
        finally:
            self._iteration_count += 1
            self._last_finished_at = _now()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
