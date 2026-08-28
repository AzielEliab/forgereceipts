
from __future__ import annotations

from pathlib import Path

from forgereceipts.store import ForgeStore, verify_jsonl


def test_append_and_verify(tmp_path: Path) -> None:
    store = ForgeStore(tmp_path)
    a = store.append_incident(
        summary="pickup delayed",
        evidence="text message screenshot retained locally",
        child_impact="Child waited past the ordered exchange time.",
        confidence=0.8,
        timestamp="2026-07-04T18:00:00Z",
    )
    b = store.append_incident(
        summary="correction: time was 18:05",
        evidence="re: prior receipt; clock photo",
        child_impact="Same exchange; timestamp correction only.",
        confidence=0.9,
        timestamp="2026-07-04T18:10:00Z",
    )
    assert b["prev_hash"] == a["hash"]
    result = store.verify()
    assert result.ok
    assert result.length == 2
    # extras survive reload
    store2 = ForgeStore(tmp_path)
    recs = store2.records()
    assert recs[0]["child_impact"].startswith("Child waited")
    assert recs[0]["kind"] == "incident"
    assert "CHILD_IMPACT:" in recs[0]["evidence"]


def test_verify_jsonl_pass_and_fail(tmp_path: Path) -> None:
    store = ForgeStore(tmp_path)
    store.append_incident(
        summary="s",
        evidence="e",
        child_impact="impact",
        timestamp="2026-07-01T00:00:00Z",
    )
    text = store.path.read_text(encoding="utf-8")
    ok = verify_jsonl(text)
    assert ok["verdict"] == "PASS"
    tampered = text.replace("impact", "TAMPER", 1)
    # child_impact extra key change does not break core hash; tamper evidence
    lines = text.splitlines()
    import json
    obj = json.loads(lines[0])
    obj["summary"] = "TAMPERED"
    bad = json.dumps(obj) + "\n"
    fail = verify_jsonl(bad)
    assert fail["verdict"] == "FAIL"
    assert fail["ok"] is False
