from __future__ import annotations

from forgereceipts.cli import main
from forgereceipts import __version__


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_refuses_non_local_host(capsys) -> None:
    assert main(["ui", "--host", "0.0.0.0"]) == 2
    err = capsys.readouterr().err
    assert "127.0.0.1" in err


def test_help_lists_ui_and_version(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as ei:
        main(["--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "ui" in out
    assert "version" in out
    assert "127.0.0.1:8787" in out or "forgereceipts ui" in out


def test_help_lists_doctor_and_verify_receipt(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as ei:
        main(["--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "doctor" in out
    assert "verify-receipt" in out
