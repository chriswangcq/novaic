from __future__ import annotations

import json

import pytest

import sandbox_sdk.client as sandbox_client
from sandbox_sdk import (
    SandboxBindMount,
    SandboxExecResult,
    SandboxExecSpec,
    SandboxdClient,
    SandboxdExecuteRequest,
    SandboxdExecuteResponse,
)


def test_execute_request_roundtrips_spec() -> None:
    spec = SandboxExecSpec(
        command="printf ok",
        cwd="/tmp/work",
        env={"A": "B"},
        timeout=7,
        display_command="say ok",
        mount=SandboxBindMount(
            source_root="/tmp/root",
            mount_point="/cortex",
            stable_cwd="/cortex/rw",
        ),
    )

    request = SandboxdExecuteRequest.from_dict(
        SandboxdExecuteRequest.from_spec(spec).to_dict()
    )

    assert request.to_spec() == spec


def test_execute_response_roundtrips_bytes() -> None:
    result = SandboxExecResult(
        stdout=b"\x00ok\n",
        stderr="错误".encode(),
        exit_code=3,
        duration_s=0.25,
    )

    response = SandboxdExecuteResponse.from_dict(
        SandboxdExecuteResponse.from_result(result).to_dict()
    )

    assert response.to_result() == result


@pytest.mark.asyncio
async def test_sandboxd_client_maps_spec_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}
    expected = SandboxdExecuteResponse(
        stdout=b"done",
        stderr=b"",
        exit_code=0,
        duration_s=0.1,
    )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(expected.to_dict()).encode()

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        seen["url"] = request.full_url  # type: ignore[attr-defined]
        seen["timeout"] = timeout
        seen["payload"] = json.loads(request.data.decode())  # type: ignore[attr-defined]
        return FakeResponse()

    monkeypatch.setattr(sandbox_client.urllib.request, "urlopen", fake_urlopen)

    result = await SandboxdClient(
        "http://sandboxd.local",
        request_timeout=11,
    ).execute(
        SandboxExecSpec(
            command="printf done",
            cwd="/tmp/work",
            env={"X": "Y"},
            timeout=5,
        )
    )

    assert result == expected.to_result()
    assert seen["url"] == "http://sandboxd.local/v1/execute"
    assert seen["timeout"] == 11
    assert seen["payload"]["command"] == "printf done"  # type: ignore[index]
