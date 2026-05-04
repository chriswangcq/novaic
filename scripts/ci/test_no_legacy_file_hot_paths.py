from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = (
    "fs://",
    "/api/files",
    "File Service",
    "legacy_facade",
)

ACTIVE_PATHS = (
    "novaic-storage-a/blob_service",
    "novaic-gateway/main_gateway.py",
    "novaic-gateway/gateway",
    "novaic-gateway/nginx",
    "novaic-agent-runtime/task_queue",
    "novaic-agent-runtime/main_novaic.py",
    "novaic-common/common/tools",
    "novaic-common/common/utils",
    "novaic-cortex/novaic_cortex",
    "deploy",
    "scripts/start.sh",
    "novaic-app/scripts/start-backends.sh",
    "novaic-app/src-tauri/resources/backends/start-backends.sh",
    "novaic-app/src-tauri/resources/config/services.json",
)


def _source_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return [
        child
        for child in path.rglob("*")
        if child.is_file()
        and "__pycache__" not in child.parts
        and child.suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".conf", ".sh"}
    ]


def test_no_legacy_file_hot_paths_in_active_runtime_code() -> None:
    offenders: list[str] = []
    for rel in ACTIVE_PATHS:
        for path in _source_files(ROOT / rel):
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)} contains {token!r}")

    assert offenders == []
