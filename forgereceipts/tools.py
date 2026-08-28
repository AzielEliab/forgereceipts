"""Optional *Lock engine panels. Import failures are availability, not 500s.

MirageGrid is logical nodes only — never a proxy, VPN, or IP-hiding mesh.
"""

from __future__ import annotations

import json
from typing import Any


def availability() -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for name in (
        "vibelock",
        "codelock",
        "shadowlock",
        "veillock",
        "godlock",
        "staticclock",
        "miragegrid",
        "temporallock",
    ):
        try:
            __import__(name)
            flags[name] = True
        except Exception:
            flags[name] = False
    return flags


def vibelock_score() -> dict[str, Any]:
    """Score a synthetic local wav pair. No user recording is required."""
    from vibelock import analyze
    from vibelock.synth import make_pair

    pair = make_pair(duration_s=0.6, sr=16000, seed=202607)
    result = analyze(pair.audio, pair.sr, vibration=pair.vibration)
    return {
        "engine": "vibelock",
        "mode": result.mode,
        "score": float(result.score),
        "reason_codes": list(result.reason_codes),
        "notes": list(result.notes) + [
            "Synthetic local pair from vibelock.synth.make_pair. Not a human recording."
        ],
        "sample_rate": int(result.sample_rate),
        "n_samples": int(result.n_samples),
    }


def codelock_render(source: str, acknowledgment: str, seed: str = "0") -> dict[str, Any]:
    from codelock import ACK_PHRASE, CodeLockSession
    from codelock.gate import AcknowledgmentError, GateClosedError

    session = CodeLockSession(source, seed=seed)
    try:
        session.open_gate(acknowledgment)
        html_out = session.codelock_html()
        return {
            "engine": "codelock",
            "gate": "open",
            "ack_phrase": ACK_PHRASE,
            "html": html_out,
            "normalize_html": session.normalize_html(),
            "note": "View-layer only. Not encryption. Source is unchanged.",
        }
    except (AcknowledgmentError, GateClosedError) as exc:
        return {
            "engine": "codelock",
            "gate": "closed",
            "ack_phrase": ACK_PHRASE,
            "error": str(exc),
            "normalize_html": session.normalize_html(),
        }


def shadowlock_observe(jsonl_text: str) -> dict[str, Any]:
    from shadowlock import MemoryAdapter, ShadowLockSession

    records: list[dict[str, Any]] = []
    for line in jsonl_text.splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if isinstance(rec, dict):
            records.append(rec)
    session = ShadowLockSession()
    report = session.observe(MemoryAdapter(records))
    session.forget()
    payload = report.to_dict()
    payload["engine"] = "shadowlock"
    payload["note"] = "Read-only observe. Session forgotten after this report."
    return payload


def veillock_encrypt() -> dict[str, Any]:
    import numpy as np
    from veillock import VeilLockSession

    frames = np.zeros((2, 8, 8, 3), dtype=np.uint8)
    frames[0, :, :, 0] = 40
    frames[1, :, :, 1] = 80
    session = VeilLockSession()
    stream = session.encrypt_frames(frames)
    return {
        "engine": "veillock",
        "frames": len(stream.frames),
        "mode": stream.mode,
        "cipher_bytes": [len(f.ciphertext) for f in stream.frames],
        "nonces_hex": [f.nonce.hex() for f in stream.frames],
        "note": "Synthetic 8x8 RGB frames encrypted in-process. Not a live display capture.",
    }


def godlock_submit(text: str) -> dict[str, Any]:
    from godlock import GodLockEngine

    engine = GodLockEngine(persist=False)
    result = engine.submit(text)
    result["engine"] = "godlock"
    result["note"] = "In-memory only (persist=False). Not an anonymity network."
    return result


def staticclock_advise(geo: str) -> dict[str, Any]:
    from staticclock import StaticClock

    clock = StaticClock()
    advisory = clock.advise(geo)
    clock.forget()
    payload = advisory.to_dict()
    payload["engine"] = "staticclock"
    payload["note"] = "Advisory only. Then forget. Not a scheduler."
    return payload


def miragegrid_assign() -> dict[str, Any]:
    from miragegrid import MirageSession, POOL_SIZE

    with MirageSession() as session:
        node = session.node
        receipt = session.receipt
        payload = {
            "engine": "miragegrid",
            "pool_size": POOL_SIZE,
            "node_id": node.id,
            "node_label": node.label,
            "node_index": node.index,
            "session_id": session.session_id,
            "receipt_hash": getattr(receipt, "hash", None) or getattr(receipt, "digest", None),
            "note": (
                "Logical node assignment only. Not a proxy, VPN, Tor hop, "
                "or IP-hiding network. Mapping is destroyed when the session ends."
            ),
        }
    return payload


HANDLERS = {
    "vibelock": lambda body: vibelock_score(),
    "codelock": lambda body: codelock_render(
        str(body.get("source") or "plain source"),
        str(body.get("acknowledgment") or body.get("phrase") or ""),
        str(body.get("seed") or "0"),
    ),
    "shadowlock": lambda body: shadowlock_observe(str(body.get("jsonl") or "")),
    "veillock": lambda body: veillock_encrypt(),
    "godlock": lambda body: godlock_submit(str(body.get("text") or "local stress text")),
    "staticclock": lambda body: staticclock_advise(str(body.get("geo") or "Indianapolis")),
    "miragegrid": lambda body: miragegrid_assign(),
}


def run(name: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"error": f"unknown engine {name!r}", "available": availability()}
    if not availability().get(name, False):
        return {
            "engine": name,
            "available": False,
            "error": f"{name} is vendored but could not be imported (optional extra deps?)",
        }
    try:
        return handler(body or {})
    except Exception as exc:  # noqa: BLE001 — panel must not 500 the UI
        return {"engine": name, "error": str(exc), "available": True}
