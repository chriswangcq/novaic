import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def test_file_storage_base64_write_read(tmp_path):
    from file_service.storage import FileStorage

    storage = FileStorage(base_dir=str(tmp_path / "files"), url_prefix="/api/files")
    url = storage.save_from_base64(
        base64_data="aGVsbG8tZmlsZS1zZXJ2aWNl",
        category="documents",
        agent_id="agent-unit",
        mime_type="application/pdf",
    )
    assert url.startswith("/api/files/")

    loaded = storage.load_bytes(url)
    assert loaded is not None
    assert loaded == b"hello-file-service"
