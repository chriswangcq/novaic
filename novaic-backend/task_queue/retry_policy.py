"""
Unified retry policy for Task/Saga workers.

Centralizes:
- retryable error classification
- max-attempt decision
- exponential backoff calculation
"""

from dataclasses import dataclass
from typing import Optional

from common.config import ServiceConfig
from common.exceptions import BusinessError
from task_queue.exceptions import is_retryable_error


@dataclass(frozen=True)
class RetryDecision:
    """Retry decision returned by policy evaluation."""

    retry: bool
    reason: str
    backoff_seconds: float
    attempt: int
    max_attempts: int


class RetryPolicy:
    """Config-driven retry policy shared by workers."""

    def __init__(
        self,
        *,
        max_attempts: Optional[int] = None,
        backoff_base: Optional[float] = None,
        backoff_max: Optional[float] = None,
    ):
        configured_max = int(
            max_attempts
            if max_attempts is not None
            else getattr(ServiceConfig, "DEFAULT_MAX_RETRIES", 3)
        )
        self.max_attempts = max(1, configured_max)
        self.backoff_base = float(
            backoff_base
            if backoff_base is not None
            else getattr(ServiceConfig, "RETRY_BACKOFF_BASE", 1.0)
        )
        self.backoff_max = float(
            backoff_max
            if backoff_max is not None
            else getattr(ServiceConfig, "RETRY_BACKOFF_MAX", 30.0)
        )

    def evaluate(
        self,
        error: Exception,
        *,
        attempt: int,
        max_attempts: Optional[int] = None,
    ) -> RetryDecision:
        """
        Evaluate whether this failure should be retried.

        Args:
            error: captured exception
            attempt: 1-based attempt index
            max_attempts: optional per-task/per-saga max override
        """
        effective_max = max(1, int(max_attempts or self.max_attempts))

        if isinstance(error, BusinessError):
            return RetryDecision(
                retry=False,
                reason="business_error",
                backoff_seconds=0.0,
                attempt=attempt,
                max_attempts=effective_max,
            )

        if not is_retryable_error(error):
            return RetryDecision(
                retry=False,
                reason="non_retryable_error",
                backoff_seconds=0.0,
                attempt=attempt,
                max_attempts=effective_max,
            )

        if attempt >= effective_max:
            return RetryDecision(
                retry=False,
                reason="max_attempts_exhausted",
                backoff_seconds=0.0,
                attempt=attempt,
                max_attempts=effective_max,
            )

        return RetryDecision(
            retry=True,
            reason="retryable_error",
            backoff_seconds=self.backoff_seconds(attempt),
            attempt=attempt,
            max_attempts=effective_max,
        )

    def backoff_seconds(self, attempt: int) -> float:
        """Exponential backoff with ceiling."""
        normalized_attempt = max(1, int(attempt))
        value = self.backoff_base * (2 ** (normalized_attempt - 1))
        return min(value, self.backoff_max)
