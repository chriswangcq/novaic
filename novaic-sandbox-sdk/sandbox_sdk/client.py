"""HTTP client for sandboxd."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from sandbox_sdk.contracts import SandboxdExecuteRequest, SandboxdExecuteResponse
from sandbox_sdk.types import SandboxExecResult, SandboxExecSpec


class SandboxdClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxdClient:
    base_url: str
    request_timeout: int = 30

    async def execute(self, spec: SandboxExecSpec) -> SandboxExecResult:
        return await asyncio.to_thread(self._execute_sync, spec)

    def _execute_sync(self, spec: SandboxExecSpec) -> SandboxExecResult:
        url = self.base_url.rstrip("/") + "/v1/execute"
        payload = json.dumps(
            SandboxdExecuteRequest.from_spec(spec).to_dict(),
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SandboxdClientError(f"sandboxd returned HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise SandboxdClientError(f"sandboxd request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise SandboxdClientError("sandboxd request timed out") from exc

        try:
            data = json.loads(raw.decode("utf-8"))
            return SandboxdExecuteResponse.from_dict(data).to_result()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise SandboxdClientError("sandboxd returned an invalid response") from exc
