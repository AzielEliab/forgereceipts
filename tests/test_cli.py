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


def test_bare_command_is_a_welcome(capsys) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "forgereceipts ui" in out
    assert "http://127.0.0.1:8787" in out
    assert "Add file" in out
    assert "arguments are required" not in out
    assert "Aziel Eliab" in out


def test_unknown_command_has_a_next_step(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as ei:
        main(["bogus"])
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert 'Unknown command "bogus"' in err
    assert "forgereceipts --help" in err
    assert "Traceback" not in err


def test_unknown_flag_has_a_next_step(capsys) -> None:
    import pytest

    with pytest.raises(SystemExit) as ei:
        main(["--not-a-real-flag-xyz"])
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "not recognized" in err
    assert "forgereceipts --help" in err
    assert "Traceback" not in err
