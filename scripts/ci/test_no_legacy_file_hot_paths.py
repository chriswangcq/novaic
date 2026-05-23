from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = (
    "fs://",
    "/api/files",
    "File Service",
    "legacy" + "_facade",
    "novaic-" + "storage" + "-a",
    "Storage" + "-A",
    "storage" + "_a",
    "storage" + "-a",
)

ACTIVE_PATHS = (
    ".gitmodules",
    "Entangled/packages/server-python/entangled",
    "novaic-blob-service/blob_service",
    "novaic-blob-service/README.md",
    "novaic-blob-service/scripts",
    "novaic-agent-runtime/config/services.schema.json",
    "novaic-gateway/main_gateway.py",
    "novaic-gateway/gateway",
    "novaic-gateway/nginx",
    "novaic-device/device",
    "novaic-device/main_device.py",
    "novaic-agent-runtime/task_queue",
    "novaic-agent-runtime/queue_service",
    "novaic-agent-runtime/main_novaic.py",
    "novaic-business/business",
    "novaic-common/common",
    "novaic-common/config/services.json",
    "novaic-common/common/tools",
    "novaic-common/common/utils",
    "novaic-cortex/novaic_cortex",
    "deploy",
    "scripts/start.sh",
    "scripts/build-all.sh",
    "scripts/run_all_tests.sh",
    "novaic-app/scripts/start-backends.sh",
    "novaic-app/src-tauri/resources/backends/start-backends.sh",
    "novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh",
    "novaic-app/src-tauri/resources/config/services.json",
    "novaic-app/src-tauri/gen/apple/assets/config/services.json",
)

SERVICE_SQLITE_RESIDUE = (
    "sqlite",
    "Sqlite",
    "SQLITE",
    "sqlite3",
    "aiosqlite",
    "common.db",
    "common/db",
    "gateway_db_file",
    "GATEWAY_DB_FILE",
    "'gateway.db'",
    '"gateway.db"',
    "/gateway.db",
    "device.db",
    "queue.db",
    "operational.sqlite3",
    "operational_sqlite",
    "migrate_sqlite",
    "migration_cli",
    "--db-backend",
    "--db-path",
    "db_path",
)

PACKAGED_LAUNCHER_PATHS = (
    "novaic-app/src-tauri/resources/backends/start-backends.sh",
    "novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh",
)

RETIRED_PACKAGED_LAUNCHER_TEXT = (
    "Start all backend services",
    "Starting NovAIC backends",
    "All backends started",
    "AGENT_RUNTIME_PORT",
    "Started Agent Runtime on",
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


def test_no_retired_file_hot_paths_in_active_runtime_code() -> None:
    offenders: list[str] = []
    for rel in ACTIVE_PATHS:
        for path in _source_files(ROOT / rel):
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)} contains {token!r}")

    assert offenders == []


def test_packaged_backend_launchers_do_not_claim_full_topology() -> None:
    offenders: list[str] = []
    for rel in PACKAGED_LAUNCHER_PATHS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for token in RETIRED_PACKAGED_LAUNCHER_TEXT:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {token!r}")

    assert offenders == []


def test_no_server_sqlite_residue_in_active_runtime_code() -> None:
    offenders: list[str] = []
    for rel in ACTIVE_PATHS:
        for path in _source_files(ROOT / rel):
            text = path.read_text(encoding="utf-8")
            for token in SERVICE_SQLITE_RESIDUE:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)} contains {token!r}")

    assert offenders == []


def _run_standalone() -> None:
    test_no_retired_file_hot_paths_in_active_runtime_code()
    test_packaged_backend_launchers_do_not_claim_full_topology()
    test_no_server_sqlite_residue_in_active_runtime_code()


if __name__ == "__main__":
    _run_standalone()
