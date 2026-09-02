
from __future__ import annotations

import json
from pathlib import Path

from forgereceipts.exchange import dump_receipt, load_receipts_from_text, roundtrip, verify_text
from forgereceipts.store import ForgeStore


def test_export_import_roundtrip(tmp_path: Path) -> None:
    store = ForgeStore(tmp_path)
    row = store.append_forensics(
        summary="roundtrip file",
        file_sha256="cd" * 32,
        file_name="photo.jpg",
        child_impact="Sample only. A receipt is not legal proof.",
        timestamp="2026-09-02T12:00:00Z",
    )
    result = roundtrip(row)
    assert result["ok"] is True
    assert result["roundtrip_hash_match"] is True
    assert result["verdict"] == "PASS"
    text = dump_receipt(row)
    loaded = load_receipts_from_text(text)[0]
    assert loaded["hash"] == row["hash"]
    assert verify_text(text)["ok"] is True
    envelope = json.loads(text)
    assert envelope["not_legal_proof"] is True
    assert envelope["receipt"]["hash"] == row["hash"]

    imported = store.append_import(loaded)
    assert imported["imported"] is True
    assert imported["imported_hash"] == row["hash"]
    # The import is a new local receipt; the exported original still verifies.
    assert verify_text(dump_receipt(row))["hash"] == row["hash"]
