
from __future__ import annotations

from pathlib import Path

from forgereceipts.cli import main
from forgereceipts.exchange import dump_receipt, verify_path
from forgereceipts.store import ForgeStore


def _row(tmp_path: Path) -> dict:
    store = ForgeStore(tmp_path)
    return store.append_forensics(
        summary="hash exhibit",
        file_sha256="ab" * 32,
        file_name="exhibit.bin",
        child_impact="Sample only. A receipt is not legal proof.",
        timestamp="2026-09-02T12:00:00Z",
    )


def test_verify_receipt_pass(tmp_path: Path, capsys) -> None:
    row = _row(tmp_path)
    path = tmp_path / "receipt.json"
    path.write_text(dump_receipt(row), encoding="utf-8")
    result = verify_path(path)
    assert result["ok"] is True
    assert result["verdict"] == "PASS"
    assert result["hash"] == row["hash"]
    assert main(["verify-receipt", str(path)]) == 0
    out = capsys.readouterr().out
    assert "PASS" in out
    assert row["hash"] in out
    assert "not legal proof" in out.lower()


def test_verify_receipt_fail_tamper(tmp_path: Path, capsys) -> None:
    row = _row(tmp_path)
    row = dict(row)
    row["summary"] = "TAMPERED"
    path = tmp_path / "bad.json"
    path.write_text(dump_receipt(row), encoding="utf-8")
    assert main(["verify-receipt", str(path)]) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out


def test_verify_receipt_bad_json(tmp_path: Path, capsys) -> None:
    path = tmp_path / "nope.json"
    path.write_text("this is not json {{", encoding="utf-8")
    assert main(["verify-receipt", str(path)]) == 2
    err = capsys.readouterr().err
    assert "JSON" in err
    assert "Traceback" not in err
