"""Durable JSON state store for the NovAIC release controller."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from release_controller.models import ReleasePointer, ReleaseRun


class StateError(RuntimeError):
    """Raised when release-controller state cannot be read or written."""


class ReleaseStateStore:
    """File-backed controller state using atomic JSON replacement writes."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.releases_dir = self.root / "releases"
        self.candidates_dir = self.root / "candidates"
        self._branch_heads_path = self.root / "branch-heads.json"
        self.initialize()

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.releases_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_dir.mkdir(parents=True, exist_ok=True)
        if not self._branch_heads_path.exists():
            self._write_json(self._branch_heads_path, {})

    def read_branch_heads(self) -> dict[str, str]:
        data = self._read_json(self._branch_heads_path, {})
        if not isinstance(data, Mapping):
            raise StateError("branch-heads.json must contain an object")
        result: dict[str, str] = {}
        for branch, commit in data.items():
            if not isinstance(branch, str) or not isinstance(commit, str):
                raise StateError("branch heads must map strings to strings")
            result[branch] = commit
        return result

    def write_branch_head(self, branch: str, commit: str) -> None:
        if not branch or not commit:
            raise StateError("branch and commit must be non-empty")
        heads = self.read_branch_heads()
        heads[branch] = commit
        self._write_json(self._branch_heads_path, heads)

    def put_run(self, run: ReleaseRun) -> None:
        self._write_json(self._run_path(run.run_id), run.to_mapping())

    def get_run(self, run_id: str) -> ReleaseRun | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        return ReleaseRun.from_mapping(self._read_object(path))

    def update_run(self, run_id: str, **changes: Any) -> ReleaseRun:
        current = self.get_run(run_id)
        if current is None:
            raise StateError(f"run does not exist: {run_id}")
        updated = replace(current, **changes)
        self.put_run(updated)
        return updated

    def list_runs(self, limit: int | None = None) -> tuple[ReleaseRun, ...]:
        paths = sorted(self.runs_dir.glob("*.json"), key=lambda path: path.name, reverse=True)
        runs = tuple(ReleaseRun.from_mapping(self._read_object(path)) for path in paths)
        if limit is None:
            return runs
        return runs[:limit]

    def update_namespace_release(self, pointer: ReleasePointer) -> None:
        current = self.get_current_release(pointer.namespace)
        if current is not None:
            self._write_json(self._previous_path(pointer.namespace), current.to_mapping())
        self._write_json(self._current_path(pointer.namespace), pointer.to_mapping())

    def get_current_release(self, namespace: str) -> ReleasePointer | None:
        return self._read_pointer_if_exists(self._current_path(namespace))

    def get_previous_release(self, namespace: str) -> ReleasePointer | None:
        return self._read_pointer_if_exists(self._previous_path(namespace))

    def list_current_releases(self) -> tuple[ReleasePointer, ...]:
        return self._list_release_pointers("*-current.json")

    def list_previous_releases(self) -> tuple[ReleasePointer, ...]:
        return self._list_release_pointers("*-previous.json")

    def put_candidate(self, candidate_id: str, pointer: ReleasePointer) -> None:
        if not candidate_id:
            raise StateError("candidate_id must be non-empty")
        self._write_json(self._candidate_path(candidate_id), pointer.to_mapping())

    def get_candidate(self, candidate_id: str) -> ReleasePointer | None:
        return self._read_pointer_if_exists(self._candidate_path(candidate_id))

    def list_candidates(self) -> tuple[ReleasePointer, ...]:
        paths = sorted(self.candidates_dir.glob("*.json"), key=lambda path: path.name, reverse=True)
        return tuple(ReleasePointer.from_mapping(self._read_object(path)) for path in paths)

    def _list_release_pointers(self, pattern: str) -> tuple[ReleasePointer, ...]:
        paths = sorted(self.releases_dir.glob(pattern), key=lambda path: path.name)
        return tuple(ReleasePointer.from_mapping(self._read_object(path)) for path in paths)

    def _read_pointer_if_exists(self, path: Path) -> ReleasePointer | None:
        if not path.exists():
            return None
        return ReleasePointer.from_mapping(self._read_object(path))

    def _run_path(self, run_id: str) -> Path:
        if not run_id or "/" in run_id:
            raise StateError("run_id must be a non-empty file-safe id")
        return self.runs_dir / f"{run_id}.json"

    def _current_path(self, namespace: str) -> Path:
        return self.releases_dir / f"{_safe_name(namespace)}-current.json"

    def _previous_path(self, namespace: str) -> Path:
        return self.releases_dir / f"{_safe_name(namespace)}-previous.json"

    def _candidate_path(self, candidate_id: str) -> Path:
        return self.candidates_dir / f"{_safe_name(candidate_id)}.json"

    def _read_object(self, path: Path) -> Mapping[str, Any]:
        data = self._read_json(path, None)
        if not isinstance(data, Mapping):
            raise StateError(f"{path} must contain a JSON object")
        return data

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StateError(f"invalid JSON state file: {path}: {exc}") from exc

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                json.dump(data, temp_file, indent=2, sort_keys=True)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_name, path)
        except Exception:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
            raise


def _safe_name(value: str) -> str:
    if not value or "/" in value or value in {".", ".."}:
        raise StateError("state object names must be non-empty file-safe ids")
    return value
