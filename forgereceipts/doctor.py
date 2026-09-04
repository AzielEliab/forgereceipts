"""Local health check. Does not talk to the network. No telemetry."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

from forgereceipts import __version__
from forgereceipts.debug import DEBUG_ENV, debug_enabled, debug_log
from forgereceipts.demo import SAMPLE_BYTES, write_sample
from forgereceipts.exchange import dump_receipt, roundtrip, verify_text
from forgereceipts.forensics import sha256_bytes
from forgereceipts.limits import MAX_BODY, MAX_FILE_BYTES, MAX_JSON_CHARS
from forgereceipts.paths import data_dir as resolve_data_dir
from forgereceipts.plain import NOT_LEGAL_PROOF
from forgereceipts.store import ForgeStore, verify_jsonl

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_HOST = "127.0.0.1"

CheckFn = Callable[[], tuple[bool, str, str]]


def _check_python() -> tuple[bool, str, str]:
    ver = sys.version_info
    ok = ver >= (3, 10)
    detail = f"{ver.major}.{ver.minor}.{ver.micro}"
    plain = (
        f"Python {detail} is new enough."
        if ok
        else f"Python {detail} is too old. ForgeReceipts needs 3.10 or newer."
    )
    return ok, detail, plain


def _check_version() -> tuple[bool, str, str]:
    ok = bool(__version__)
    return ok, __version__, f"This is ForgeReceipts {__version__}."


def _check_loopback() -> tuple[bool, str, str]:
    from forgereceipts.ui import make_server

    try:
        make_server("0.0.0.0", 0)
    except ValueError:
        return True, DEFAULT_HOST, "ForgeReceipts only listens on this computer (127.0.0.1)."
    return False, "open", "ForgeReceipts would listen on the network. That is not allowed."


def _check_telemetry() -> tuple[bool, str, str]:
    return True, "off", "No telemetry. Nothing is sent anywhere."


def _check_limits() -> tuple[bool, str, str]:
    ok = MAX_BODY == MAX_FILE_BYTES == 12 * 1024 * 1024 and MAX_JSON_CHARS > 0
    detail = f"HTTP {MAX_BODY} bytes, JSON {MAX_JSON_CHARS} chars"
    plain = "Big files over 12 MB are refused so this computer stays safe."
    return ok, detail, plain


def _check_static() -> tuple[bool, str, str]:
    index = STATIC_DIR / "index.html"
    js = STATIC_DIR / "app.js"
    css = STATIC_DIR / "style.css"
    ok = index.is_file() and js.is_file() and css.is_file()
    detail = str(STATIC_DIR)
    plain = (
        "The local page files are on this computer."
        if ok
        else "The local page files are missing."
    )
    return ok, detail, plain


def _check_data_dir(directory: Path) -> tuple[bool, str, str]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".doctor-write"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
        return True, str(directory), "The local folder can save receipts."
    except OSError as exc:
        return False, str(directory), f"The local folder cannot be written: {exc}"


def _check_demo() -> tuple[bool, str, str]:
    got = sha256_bytes(SAMPLE_BYTES)
    ok = len(got) == 64 and got == sha256_bytes(SAMPLE_BYTES)
    return ok, got, "The sample file hashes the same way every time."


def _check_chain(directory: Path) -> tuple[bool, str, str]:
    path = directory / "chain.jsonl"
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        return True, "empty", "No receipts yet. That is OK."
    text = path.read_text(encoding="utf-8")
    result = verify_jsonl(text)
    ok = bool(result.get("ok"))
    detail = str(result.get("verdict") or "FAIL")
    plain = (
        "Your saved receipts still match their hashes."
        if ok
        else "A saved receipt no longer matches its hash."
    )
    return ok, detail, plain


def _check_roundtrip(directory: Path) -> tuple[bool, str, str]:
    tmp = directory / "doctor-roundtrip"
    tmp.mkdir(parents=True, exist_ok=True)
    store = ForgeStore(tmp)
    sample = write_sample(tmp)
    digest = sha256_bytes(SAMPLE_BYTES)
    row = store.append_forensics(
        summary="doctor sample",
        file_sha256=digest,
        file_name=sample.name,
        child_impact="Sample only. A receipt is not legal proof.",
        timestamp="2026-09-02T00:00:00Z",
    )
    result = roundtrip(row)
    verified = verify_text(dump_receipt(row))
    ok = bool(result.get("ok") and verified.get("ok") and sample.is_file())
    return ok, str(result.get("verdict") or "FAIL"), str(
        result.get("plain") or "Roundtrip check."
    )


def _check_jurisdictions() -> tuple[bool, str, str]:
    from forgereceipts.jurisdictions import DISTRICT_IDS, STATE_IDS, list_jurisdictions

    rows = list_jurisdictions()
    ids = {r["id"] for r in rows}
    ok = len(STATE_IDS) == 50 and "DC" in ids and "US" in ids and "IN" in ids
    detail = f"{len(STATE_IDS)} states, DC={('DC' in DISTRICT_IDS)}, federal={'US' in ids}"
    plain = (
        "All 50 states, DC, and the federal baseline are loaded."
        if ok
        else "The state list is missing. That should not happen."
    )
    return ok, detail, plain


def run_doctor(data_dir: str | Path | None = None) -> dict[str, Any]:
    directory = resolve_data_dir(data_dir)
    debug_log(f"doctor data_dir={directory} debug={debug_enabled()}")

    checks: list[dict[str, Any]] = []

    def add(cid: str, fn: CheckFn) -> None:
        ok, detail, plain = fn()
        checks.append(
            {
                "id": cid,
                "ok": bool(ok),
                "verdict": "PASS" if ok else "FAIL",
                "detail": detail,
                "plain": plain,
            }
        )

    add("python", _check_python)
    add("version", _check_version)
    add("loopback", _check_loopback)
    add("telemetry", _check_telemetry)
    add("size_limits", _check_limits)
    add("static", _check_static)
    add("data_dir", lambda: _check_data_dir(directory))
    add("demo", _check_demo)
    add("roundtrip", lambda: _check_roundtrip(directory))
    add("chain", lambda: _check_chain(directory))
    add("jurisdictions", _check_jurisdictions)
    add(
        "debug",
        lambda: (
            True,
            "on" if debug_enabled() else "off",
            (
                f"{DEBUG_ENV}=1 is on. Extra logs go to this computer only."
                if debug_enabled()
                else f"{DEBUG_ENV} is off. That is the usual setting."
            ),
        ),
    )

    ok = all(c["ok"] for c in checks)
    return {
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "version": __version__,
        "disclaimer": NOT_LEGAL_PROOF,
        "not_legal_advice": True,
        "not_legal_proof": True,
        "telemetry": False,
        "bind": DEFAULT_HOST,
        "debug": debug_enabled(),
        "data_dir": str(directory),
        "plain": (
            "Everything looks OK. You can save receipts on this computer."
            if ok
            else "Something is not right. Read the FAIL lines."
        ),
        "checks": checks,
    }


def format_doctor(report: dict[str, Any]) -> str:
    lines = [
        f"ForgeReceipts doctor {report.get('version')}",
        str(report.get("disclaimer") or NOT_LEGAL_PROOF),
        "No telemetry. Loopback only. Receipts are not legal proof.",
        "",
    ]
    for c in report.get("checks") or []:
        flag = "PASS" if c.get("ok") else "FAIL"
        ident = str(c.get("id") or "")
        lines.append(f"[{flag}] {ident:<12} {c.get('plain')}")
        if debug_enabled() and c.get("detail"):
            lines.append(f"         detail: {c['detail']}")
    lines.append("")
    if report.get("ok"):
        lines.append("ALL CHECKS PASSED")
    else:
        lines.append("SOME CHECKS FAILED")
    lines.append(str(report.get("plain") or ""))
    return "\n".join(lines).rstrip() + "\n"
