#!/usr/bin/env python3
"""Lint the Blob/LogicalFS authority boundary from the repository root.

Blob is the byte store. LogicalFS is the live workspace authority. This guard
keeps direct Blob object authority and BlobRef production confined to the
explicitly allowed boundary files.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "novaic-cortex" / "cortex_tests" / "blob_boundary_policy.py"
RUNTIME_ROOTS = (
    REPO_ROOT / "novaic-cortex" / "novaic_cortex",
    REPO_ROOT / "novaic-logicalfs" / "logicalfs",
    REPO_ROOT / "novaic-sandbox-service" / "sandbox_service",
)


def _load_policy() -> ModuleType:
    spec = importlib.util.spec_from_file_location("blob_boundary_policy", POLICY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load policy module: {POLICY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


POLICY = _load_policy()


def _iter_runtime_sources() -> list[Path]:
    files: list[Path] = []
    for root in RUNTIME_ROOTS:
        if not root.exists():
            continue
        files.extend(
            path
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    return sorted(files)


def _policy_path(path: Path) -> str:
    cortex_root = REPO_ROOT / "novaic-cortex"
    if path.is_relative_to(cortex_root):
        return POLICY.normalized_source_path(str(path.relative_to(cortex_root)))
    return POLICY.normalized_source_path(str(path.relative_to(REPO_ROOT)))


def _direct_object_authority_violations(policy_path: str, text: str) -> list[str]:
    if POLICY.is_allowed_object_authority_path(policy_path):
        return []
    return [
        pattern
        for pattern in POLICY.FORBIDDEN_DIRECT_OBJECT_PATTERNS
        if pattern in text
    ]


def _blob_reference_boundary_violations(policy_path: str, text: str) -> list[str]:
    if POLICY.is_allowed_blob_reference_path(policy_path):
        return []
    return [
        pattern
        for pattern in POLICY.ALLOWED_BLOB_REFERENCE_PATTERNS
        if pattern in text
    ]


def main() -> int:
    violations: list[str] = []

    for source in _iter_runtime_sources():
        policy_path = _policy_path(source)
        text = source.read_text()

        direct_hits = _direct_object_authority_violations(policy_path, text)
        if direct_hits:
            violations.append(
                f"{policy_path}: direct Blob object authority: {', '.join(direct_hits)}"
            )

        blob_hits = _blob_reference_boundary_violations(policy_path, text)
        if blob_hits:
            violations.append(
                f"{policy_path}: BlobRef/Blob API outside allowed flow: {', '.join(blob_hits)}"
            )

    if violations:
        print("Blob workspace boundary violations:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Blob workspace boundary OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
