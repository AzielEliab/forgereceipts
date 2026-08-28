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
