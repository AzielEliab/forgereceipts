
from __future__ import annotations

import json
from urllib.request import Request, urlopen

from forgereceipts.ui import make_server


def _get(url: str) -> tuple[int, str]:
    with urlopen(url, timeout=5) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, body


def _post(url: str, payload: dict) -> tuple[int, dict]:
    raw = json.dumps(payload).encode("utf-8")
    req = Request(url, data=raw, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=15) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_get_root_contains_name_and_disclaimer(base_url: str) -> None:
    status, body = _get(base_url + "/")
    assert status == 200
    assert "ForgeReceipts" in body
    assert "Not Legal Advice" in body


def test_bind_is_loopback(httpd) -> None:
    host, port = httpd.server_address[:2]
    assert host == "127.0.0.1"
    assert isinstance(port, int) and port > 0


def test_make_server_rejects_non_loopback() -> None:
    import pytest
    with pytest.raises(ValueError):
        make_server("0.0.0.0", 0)


def test_tools_pages_do_not_500(base_url: str) -> None:
    for path in (
        "/",
        "/home",
        "/incident",
        "/forensics",
        "/journal",
        "/filing",
        "/tools",
        "/verify",
        "/lock",
        "/receipts",
        "/api/tools",
        "/api/meta",
        "/static/style.css",
        "/static/app.js",
        "/manifest.webmanifest",
    ):
        status, body = _get(base_url + path)
        assert status == 200, path
        assert "Internal Server Error" not in body
        if path == "/tools":
            assert "ForgeReceipts" in body
            assert "Not Legal Advice" in body


def test_tool_posts_do_not_500(base_url: str) -> None:
    for name in (
        "vibelock",
        "codelock",
        "shadowlock",
        "veillock",
        "godlock",
        "staticclock",
        "miragegrid",
    ):
        status, data = _post(base_url + "/api/tools/" + name, {})
        assert status == 200, name
        assert "error" in data or data.get("engine") == name or "available" in data


def test_incident_roundtrip(base_url: str) -> None:
    status, data = _post(
        base_url + "/api/incident",
        {
            "summary": "exchange",
            "evidence": "notes",
            "child_impact": "child was present",
            "confidence": 0.7,
        },
    )
    assert status == 200
    assert data["receipt"]["kind"] == "incident"
    assert data["verify"]["verdict"] == "PASS"



def test_home_has_giant_actions(base_url: str) -> None:
    status, body = _get(base_url + "/")
    assert status == 200
    assert "Add file" in body
    assert "Import receipt" in body
    assert "Export receipt" in body
    assert "Saved a receipt for this file" in body
    assert "Try a sample" in body
    assert "Simple" in body
    assert "Advanced" in body
    assert "not legal proof" in body.lower()


def test_demo_saves_receipt(base_url: str) -> None:
    status, data = _post(base_url + "/api/demo", {})
    assert status == 200
    assert data["plain"] == "Saved a receipt for this file"
    assert data["receipt"]["file_name"]
    assert len(data["sha256"]) == 64
    assert data.get("not_legal_proof") is True


def test_export_import_http_roundtrip(base_url: str) -> None:
    status, created = _post(base_url + "/api/demo", {})
    assert status == 200
    digest = created["receipt"]["hash"]
    status, exported = _post(base_url + "/api/receipt/export", {"hash": digest})
    assert status == 200
    assert "forgereceipts.receipt/v1" in exported["content"]
    status, imported = _post(base_url + "/api/receipt/import", {"json": exported["content"]})
    assert status == 200
    assert imported["ok"] is True
    assert imported["receipt"]["imported_hash"] == digest


def test_bad_json_is_plain(base_url: str) -> None:
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    req = Request(
        base_url + "/api/verify",
        data=b"this is not json {{",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urlopen(req, timeout=5)
        raise AssertionError("expected HTTPError")
    except HTTPError as exc:
        assert exc.code == 400
        body = json.loads(exc.read().decode("utf-8"))
        assert "JSON" in body["error"]
        assert "Traceback" not in body["error"]
        assert body.get("plain") is True
