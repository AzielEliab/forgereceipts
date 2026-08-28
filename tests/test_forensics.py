
from __future__ import annotations

from pathlib import Path

from forgereceipts.forensics import reverify_bytes, reverify_path, sha256_bytes, sha256_path
from forgereceipts.store import ForgeStore


def test_file_hash_reverify(tmp_path: Path) -> None:
    blob = b"petitioner exhibit bytes"
    digest = sha256_bytes(blob)
    p = tmp_path / "exhibit.bin"
    p.write_bytes(blob)
    assert sha256_path(p) == digest
    store = ForgeStore(tmp_path / "data")
    row = store.append_forensics(summary="hash exhibit", file_sha256=digest, file_name="exhibit.bin")
    assert row["file_sha256"] == digest
    assert reverify_path(p, digest)["verdict"] == "PASS"
    assert reverify_bytes(blob, digest)["ok"] is True
    p.write_bytes(b"changed")
    assert reverify_path(p, digest)["verdict"] == "FAIL"
