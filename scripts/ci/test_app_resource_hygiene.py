from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VMUSE_REPO = ROOT / "novaic-mcp-vmuse"
RESOURCE_TARGETS = (
    ROOT / "novaic-app/src-tauri/resources/novaic-mcp-vmuse",
    ROOT / "novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse",
)

EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", "tests"}
EXCLUDED_SUFFIXES = {".pyc"}


def _is_resource_file(path: Path) -> bool:
    rel_parts = set(path.relative_to(VMUSE_REPO).parts)
    if rel_parts & EXCLUDED_PARTS:
        return False
    if path.name == "README.md":
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if any(part.endswith(".egg-info") for part in rel_parts):
        return False
    return path.is_file()


def _expected_vmuse_files() -> dict[Path, bytes]:
    return {
        path.relative_to(VMUSE_REPO): path.read_bytes()
        for path in VMUSE_REPO.rglob("*")
        if _is_resource_file(path)
    }


def test_app_vmuse_resource_bundles_match_source_repo() -> None:
    expected = _expected_vmuse_files()
    assert expected, "novaic-mcp-vmuse source repo was not found"

    for target in RESOURCE_TARGETS:
        assert target.exists(), f"missing resource bundle: {target.relative_to(ROOT)}"
        actual = {
            path.relative_to(target): path.read_bytes()
            for path in target.rglob("*")
            if path.is_file()
        }
        assert actual == expected, f"resource bundle drifted: {target.relative_to(ROOT)}"


def test_app_resource_bundles_do_not_contain_generated_python_artifacts() -> None:
    offenders: list[str] = []
    for target in RESOURCE_TARGETS:
        if not target.exists():
            continue
        for path in target.rglob("*"):
            if path.name == "__pycache__" or path.suffix == ".pyc" or path.name.endswith(".egg-info"):
                offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
