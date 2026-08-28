
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
