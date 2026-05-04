#!/usr/bin/env python3
"""Audit or purge historical non-Blob large-object references.

This is an explicit one-shot migration helper. It is not imported by runtime
code and it must not become a compatibility reader.

Default mode is dry-run audit. Use ``--apply`` to mutate a SQLite DB after a
backup has been written.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


LEGACY_PREFIXES = ("fs://", "/api/files/", "http://", "https://", "oss://")


@dataclass
class Finding:
    db: str
    table: str
    item_id: str
    field: str
    value: str
    action: str


def is_legacy_locator(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(LEGACY_PREFIXES)


def is_blob_locator(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("blob://")


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {str(row["name"]) for row in rows}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def _parse_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _attachment_locator(att: dict[str, Any]) -> str:
    return str(att.get("blob_ref") or att.get("url") or "")


def _remove_legacy_attachments(content: Any) -> tuple[Any, list[str]]:
    was_string = isinstance(content, str)
    parsed = _parse_json(content)
    if not isinstance(parsed, dict):
        return content, []
    attachments = parsed.get("attachments")
    if not isinstance(attachments, list):
        return content, []

    removed: list[str] = []
    kept: list[Any] = []
    for att in attachments:
        if isinstance(att, dict) and is_legacy_locator(_attachment_locator(att)):
            removed.append(_attachment_locator(att))
            continue
        kept.append(att)
    if not removed:
        return content, []
    parsed["attachments"] = kept
    return _dump_json(parsed) if was_string else parsed, removed


def _backup(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = backup_dir / f"{db_path.name}.{stamp}.bak"
    shutil.copy2(db_path, dest)
    return dest


def _audit_server_tables(conn: sqlite3.Connection, db_label: str) -> list[Finding]:
    tables = _tables(conn)
    findings: list[Finding] = []

    if "files" in tables and {"id", "storage_key"} <= _columns(conn, "files"):
        for row in conn.execute("SELECT id, storage_key FROM files"):
            value = row["storage_key"]
            if is_legacy_locator(value):
                findings.append(Finding(db_label, "files", row["id"], "storage_key", value, "delete row"))

    if "messages" in tables and {"id", "content"} <= _columns(conn, "messages"):
        for row in conn.execute("SELECT id, content FROM messages"):
            _, removed = _remove_legacy_attachments(row["content"])
            for value in removed:
                findings.append(Finding(db_label, "messages", row["id"], "content.attachments", value, "remove attachment"))

    if "environment_im_messages" in tables:
        cols = _columns(conn, "environment_im_messages")
        if {"message_id", "content"} <= cols:
            for row in conn.execute("SELECT message_id, content FROM environment_im_messages"):
                _, removed = _remove_legacy_attachments(row["content"])
                for value in removed:
                    findings.append(Finding(db_label, "environment_im_messages", row["message_id"], "content.attachments", value, "remove attachment"))
        if {"message_id", "attachments"} <= cols:
            for row in conn.execute("SELECT message_id, attachments FROM environment_im_messages"):
                _, removed = _remove_legacy_attachments(_dump_json({"attachments": _parse_json(row["attachments"]) or []}))
                for value in removed:
                    findings.append(Finding(db_label, "environment_im_messages", row["message_id"], "attachments", value, "remove attachment"))

    if "environment_resource_refs" in tables and {"ref_id", "locator"} <= _columns(conn, "environment_resource_refs"):
        for row in conn.execute("SELECT ref_id, locator FROM environment_resource_refs"):
            value = row["locator"]
            if is_legacy_locator(value):
                findings.append(Finding(db_label, "environment_resource_refs", row["ref_id"], "locator", value, "delete row"))

    return findings


def _purge_server_tables(conn: sqlite3.Connection) -> None:
    tables = _tables(conn)

    if "files" in tables and {"id", "storage_key"} <= _columns(conn, "files"):
        conn.execute(
            "DELETE FROM files WHERE storage_key LIKE 'fs://%' OR storage_key LIKE '/api/files/%' "
            "OR storage_key LIKE 'http://%' OR storage_key LIKE 'https://%' OR storage_key LIKE 'oss://%'"
        )

    if "messages" in tables and {"id", "content"} <= _columns(conn, "messages"):
        rows = conn.execute("SELECT id, content FROM messages").fetchall()
        for row in rows:
            new_content, removed = _remove_legacy_attachments(row["content"])
            if removed:
                conn.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, row["id"]))

    if "environment_im_messages" in tables:
        cols = _columns(conn, "environment_im_messages")
        if {"message_id", "content"} <= cols:
            rows = conn.execute("SELECT message_id, content FROM environment_im_messages").fetchall()
            for row in rows:
                new_content, removed = _remove_legacy_attachments(row["content"])
                if removed:
                    conn.execute(
                        "UPDATE environment_im_messages SET content = ? WHERE message_id = ?",
                        (new_content, row["message_id"]),
                    )
        if {"message_id", "attachments"} <= cols:
            rows = conn.execute("SELECT message_id, attachments FROM environment_im_messages").fetchall()
            for row in rows:
                data = {"attachments": _parse_json(row["attachments"]) or []}
                new_data, removed = _remove_legacy_attachments(_dump_json(data))
                if removed:
                    attachments = _parse_json(new_data).get("attachments", [])
                    conn.execute(
                        "UPDATE environment_im_messages SET attachments = ? WHERE message_id = ?",
                        (_dump_json(attachments), row["message_id"]),
                    )

    if "environment_resource_refs" in tables and {"ref_id", "locator"} <= _columns(conn, "environment_resource_refs"):
        conn.execute(
            "DELETE FROM environment_resource_refs WHERE locator LIKE 'fs://%' OR locator LIKE '/api/files/%' "
            "OR locator LIKE 'http://%' OR locator LIKE 'https://%' OR locator LIKE 'oss://%'"
        )


def _audit_cache(conn: sqlite3.Connection, db_label: str) -> list[Finding]:
    if "entity_items" not in _tables(conn):
        return []
    findings: list[Finding] = []
    rows = conn.execute("SELECT entity, item_id, data FROM entity_items").fetchall()
    for row in rows:
        data = _parse_json(row["data"])
        if not isinstance(data, dict):
            continue
        if row["entity"] == "files" and is_legacy_locator(data.get("storage_key")):
            findings.append(Finding(db_label, "entity_items:files", row["item_id"], "data.storage_key", data["storage_key"], "delete cache row"))
        if row["entity"] in {"messages", "environment-im-messages"}:
            for field in ("content", "attachments"):
                value = data.get(field)
                if field == "attachments":
                    value = {"attachments": value or []}
                _, removed = _remove_legacy_attachments(value)
                for locator in removed:
                    findings.append(Finding(db_label, f"entity_items:{row['entity']}", row["item_id"], f"data.{field}", locator, "remove attachment"))
    return findings


def _purge_cache(conn: sqlite3.Connection) -> None:
    if "entity_items" not in _tables(conn):
        return
    rows = conn.execute("SELECT entity, params_hash, item_id, data FROM entity_items").fetchall()
    for row in rows:
        data = _parse_json(row["data"])
        if not isinstance(data, dict):
            continue
        changed = False
        delete_row = False
        if row["entity"] == "files" and is_legacy_locator(data.get("storage_key")):
            delete_row = True
        if row["entity"] in {"messages", "environment-im-messages"}:
            for field in ("content", "attachments"):
                if field == "content":
                    new_value, removed = _remove_legacy_attachments(data.get(field))
                    if removed:
                        data[field] = new_value
                        changed = True
                elif isinstance(data.get(field), list):
                    new_data, removed = _remove_legacy_attachments(_dump_json({"attachments": data[field]}))
                    if removed:
                        data[field] = _parse_json(new_data).get("attachments", [])
                        changed = True
        if delete_row:
            conn.execute(
                "DELETE FROM entity_items WHERE entity = ? AND params_hash = ? AND item_id = ?",
                (row["entity"], row["params_hash"], row["item_id"]),
            )
        elif changed:
            conn.execute(
                "UPDATE entity_items SET data = ? WHERE entity = ? AND params_hash = ? AND item_id = ?",
                (_dump_json(data), row["entity"], row["params_hash"], row["item_id"]),
            )


def _print_findings(findings: Iterable[Finding]) -> int:
    count = 0
    for finding in findings:
        count += 1
        print(
            f"{finding.db}\t{finding.table}\t{finding.item_id}\t"
            f"{finding.field}\t{finding.action}\t{finding.value}"
        )
    return count


def _process_db(path: Path, *, kind: str, apply: bool, backup_dir: Path | None) -> int:
    if not path.exists():
        raise SystemExit(f"DB not found: {path}")
    with _connect(path) as conn:
        findings = _audit_cache(conn, str(path)) if kind == "cache" else _audit_server_tables(conn, str(path))
        count = _print_findings(findings)
        if apply and count:
            if backup_dir is None:
                raise SystemExit("--apply requires --backup-dir")
            backup_path = _backup(path, backup_dir)
            print(f"BACKUP\t{path}\t{backup_path}")
            if kind == "cache":
                _purge_cache(conn)
            else:
                _purge_server_tables(conn)
            conn.commit()
            post_count = len(_audit_cache(conn, str(path)) if kind == "cache" else _audit_server_tables(conn, str(path)))
            print(f"POST_PURGE_LEGACY_COUNT\t{path}\t{post_count}")
            return post_count
        print(f"LEGACY_COUNT\t{path}\t{count}")
        return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit/purge historical non-Blob refs from Entangled DBs.")
    parser.add_argument("--entangled-db", action="append", default=[], help="Entangled server SQLite DB path.")
    parser.add_argument("--client-cache-db", action="append", default=[], help="Tauri Entangled cache SQLite DB path.")
    parser.add_argument("--apply", action="store_true", help="Apply purge. Default is dry-run audit only.")
    parser.add_argument("--backup-dir", type=Path, help="Required with --apply.")
    args = parser.parse_args()

    total = 0
    for raw_path in args.entangled_db:
        total += _process_db(Path(raw_path), kind="server", apply=args.apply, backup_dir=args.backup_dir)
    for raw_path in args.client_cache_db:
        total += _process_db(Path(raw_path), kind="cache", apply=args.apply, backup_dir=args.backup_dir)
    if not args.entangled_db and not args.client_cache_db:
        raise SystemExit("provide --entangled-db or --client-cache-db")
    return 1 if total and not args.apply else 0


if __name__ == "__main__":
    raise SystemExit(main())
