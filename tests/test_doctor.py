
from __future__ import annotations

from pathlib import Path

from forgereceipts.cli import main
from forgereceipts.doctor import format_doctor, run_doctor


def test_doctor_pass(tmp_path: Path, capsys) -> None:
    report = run_doctor(tmp_path)
    assert report["ok"] is True
    assert report["verdict"] == "PASS"
    assert report["telemetry"] is False
    assert report["bind"] == "127.0.0.1"
    ids = [c["id"] for c in report["checks"]]
    assert "python" in ids
    assert "roundtrip" in ids
    assert "loopback" in ids
    assert all(c["ok"] for c in report["checks"])
    text = format_doctor(report)
    assert "ALL CHECKS PASSED" in text
    assert "not legal proof" in text.lower()
    assert main(["doctor", "--data-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "ALL CHECKS PASSED" in out


def test_doctor_json(tmp_path: Path, capsys) -> None:
    assert main(["doctor", "--json", "--data-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert '"verdict": "PASS"' in out or '"verdict":"PASS"' in out
