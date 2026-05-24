#!/usr/bin/env python3
"""Guard namespace-aware registry/runtime contracts."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "novaic-common" / "common"
SERVER = COMMON / "service_registry_server.py"
CLIENT = COMMON / "service_registry_client.py"
RUNTIME = COMMON / "service_runtime.py"
DISCOVERY = COMMON / "service_discovery.py"
RUN_ALL = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def main() -> int:
    errors: list[str] = []
    server = SERVER.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    discovery = DISCOVERY.read_text(encoding="utf-8")
    run_all = RUN_ALL.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    require(server, '"/v1/registry/namespaces/{namespace}/instances"', "server namespace register route", errors)
    require(
        server,
        '"/v1/registry/namespaces/{namespace}/instances/{service_name}/{instance_id}/heartbeat"',
        "server namespace heartbeat route",
        errors,
    )
    require(
        server,
        '"/v1/registry/namespaces/{namespace}/services/{service_name}/discover"',
        "server namespace discover route",
        errors,
    )
    forbidden_server_routes = [
        '@app.post("/v1/registry/instances"',
        '@app.post("/v1/registry/instances/{service_name}/{instance_id}/heartbeat"',
        '@app.delete("/v1/registry/instances/{service_name}/{instance_id}"',
        '@app.get("/v1/registry/services/{service_name}/instances"',
        '@app.get("/v1/registry/services/{service_name}/discover"',
        '@app.post("/v1/registry/services/{service_name}/prune-stale"',
    ]
    for marker in forbidden_server_routes:
        if marker in server:
            errors.append(f"server contains legacy no-namespace route: {marker}")

    require(client, "namespace: str", "client constructor namespace argument", errors)
    require(client, "self._namespace", "client namespace state", errors)
    require(client, "/v1/registry/namespaces/", "client namespace route prefix", errors)
    for stale in ["/v1/registry/instances", "/v1/registry/services/"]:
        if stale in client.replace("/v1/registry/namespaces/", ""):
            errors.append(f"client appears to contain legacy route fragment: {stale}")

    require(runtime, 'parser.add_argument("--namespace", required=True)', "runtime required namespace arg", errors)
    require(runtime, 'parser.add_argument("--release-id", required=True)', "runtime required release arg", errors)
    require(runtime, "namespace=args.namespace", "runtime namespace-bound client", errors)
    for marker in ["release_id", "image_digest", "image_ref", "environment", "compose_project"]:
        require(runtime, marker, f"runtime metadata {marker}", errors)

    require(discovery, "namespace: str", "service instance namespace field", errors)
    require(discovery, "PRIMARY KEY (namespace, service_name, instance_id)", "namespace primary key", errors)
    require(discovery, "ON CONFLICT (namespace, service_name, instance_id)", "namespace upsert conflict", errors)
    require(discovery, "namespace, service_name, status, last_seen_at DESC", "namespace discover index", errors)

    marker = "scripts/ci/lint_namespace_registry_runtime.py"
    require(run_all, marker, "run_all namespace guard", errors)
    require(workflow, marker, "workflow namespace guard", errors)

    if errors:
        print("lint_namespace_registry_runtime FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("lint_namespace_registry_runtime OK")
    return 0


def require(text: str, marker: str, label: str, errors: list[str]) -> None:
    if marker not in text:
        errors.append(f"missing {label}: {marker!r}")


if __name__ == "__main__":
    raise SystemExit(main())
