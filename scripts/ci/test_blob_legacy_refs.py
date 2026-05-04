from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.blob_legacy_refs import _process_db


def _server_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE files (id TEXT PRIMARY KEY, storage_key TEXT)")
    conn.execute("CREATE TABLE messages (id TEXT PRIMARY KEY, content TEXT)")
    conn.execute("CREATE TABLE environment_im_messages (message_id TEXT PRIMARY KEY, content TEXT, attachments TEXT)")
    conn.execute("CREATE TABLE environment_resource_refs (ref_id TEXT PRIMARY KEY, locator TEXT)")
    conn.execute("INSERT INTO files VALUES ('f_old', 'fs://images/a.png')")
    conn.execute(
        "INSERT INTO messages VALUES ('m1', ?)",
        (json.dumps({"text": "hello", "attachments": [{"url": "fs://images/a.png"}, {"blob_ref": "blob://user-file/b1"}]}),),
    )
    conn.execute(
        "INSERT INTO environment_im_messages VALUES ('im1', ?, ?)",
        (
            json.dumps({"text": "hello", "attachments": [{"url": "/api/files/a.png"}]}),
            json.dumps([{"url": "https://files.example/a.png"}, {"blob_ref": "blob://user-file/b2"}]),
        ),
    )
    conn.execute("INSERT INTO environment_resource_refs VALUES ('r1', 'oss://bucket/key')")
    conn.commit()
    conn.close()


def _cache_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE entity_items (entity TEXT NOT NULL, params_hash INTEGER NOT NULL, item_id TEXT NOT NULL, data TEXT NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY (entity, params_hash, item_id))"
    )
    conn.execute(
        "INSERT INTO entity_items VALUES ('files', 1, 'f_old', ?, 1)",
        (json.dumps({"id": "f_old", "storage_key": "fs://images/a.png"}),),
    )
    conn.execute(
        "INSERT INTO entity_items VALUES ('messages', 1, 'm1', ?, 2)",
        (json.dumps({"id": "m1", "content": {"text": "hello", "attachments": [{"url": "/api/files/a.png"}]}}),),
    )
    conn.commit()
    conn.close()


def test_purge_server_db_removes_legacy_refs(tmp_path: Path) -> None:
    db = tmp_path / "entangled.db"
    _server_db(db)

    assert _process_db(db, kind="server", apply=False, backup_dir=None) == 5
    assert _process_db(db, kind="server", apply=True, backup_dir=tmp_path / "backups") == 0

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT count(*) FROM files").fetchone()[0] == 0
    content = json.loads(conn.execute("SELECT content FROM messages WHERE id='m1'").fetchone()[0])
    assert content["attachments"] == [{"blob_ref": "blob://user-file/b1"}]
    env_content = json.loads(conn.execute("SELECT content FROM environment_im_messages WHERE message_id='im1'").fetchone()[0])
    env_attachments = json.loads(conn.execute("SELECT attachments FROM environment_im_messages WHERE message_id='im1'").fetchone()[0])
    assert env_content["attachments"] == []
    assert env_attachments == [{"blob_ref": "blob://user-file/b2"}]
    assert conn.execute("SELECT count(*) FROM environment_resource_refs").fetchone()[0] == 0


def test_purge_cache_db_removes_legacy_refs(tmp_path: Path) -> None:
    db = tmp_path / "entangled_cache.db"
    _cache_db(db)

    assert _process_db(db, kind="cache", apply=False, backup_dir=None) == 2
    assert _process_db(db, kind="cache", apply=True, backup_dir=tmp_path / "backups") == 0

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT count(*) FROM entity_items WHERE entity='files'").fetchone()[0] == 0
    data = json.loads(conn.execute("SELECT data FROM entity_items WHERE entity='messages'").fetchone()[0])
    assert data["content"]["attachments"] == []
