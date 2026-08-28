"""Jeeves: propose a hardening for a stress-test receipt.

Default model is ``godlock-jeeves-heuristic-0.1`` — stdlib regex and
ABAD scoring, no network. If ``OLLAMA_HOST`` is set, a thin adapter may
try a local Ollama generate call and fall back to the heuristic on any
failure. Tests must pass with the heuristic, offline.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from godlock.abad import score_engagement
from godlock.config import JEEVES_MODEL
from godlock.receipts import Receipt

OLLAMA_TIMEOUT_S = 0.4


def analyze(receipt: Receipt, extra_keywords: list[str] | None = None) -> dict[str, Any]:
    """Return ``{receipt_id, suggested_hardening, model, notes}``."""
    host = (os.environ.get("OLLAMA_HOST") or "").strip()
    if host:
        try:
            result = _ollama_analyze(receipt, host)
            if result:
                result["receipt_id"] = receipt.id
                return result
        except Exception as exc:  # noqa: BLE001 — any network failure is a fallback
            heuristic = _heuristic(receipt, extra_keywords)
            heuristic["notes"] = (
                heuristic["notes"] + f" Ollama adapter failed ({type(exc).__name__}); heuristic used."
            )
            return heuristic
    return _heuristic(receipt, extra_keywords)


def _heuristic(receipt: Receipt, extra_keywords: list[str] | None = None) -> dict[str, Any]:
    engagement = score_engagement(receipt.text, extra_keywords=extra_keywords)
    hits = list(engagement["hits"])
    families = [h for h in hits if not h.startswith("merged_rule:")]
    if families:
        suggested = (
            "Harden ABAD coverage for: "
            + ", ".join(families)
            + f". Require an explicit {families[0]} check in the active rules."
        )
        notes = (
            f"Heuristic engagement score={engagement['score']}. "
            "Families present in the counter-argument are treated as the "
            "surface that should be hardened. Not a language model."
        )
    else:
        suggested = (
            "Add a rule requiring the counter-argument to engage at least "
            "one ABAD token (Aziel Sequence, phi, sqrt(2), Flower of Life, "
            "corkscrew, A-B-A-D)."
        )
        notes = (
            f"Heuristic engagement score={engagement['score']}. "
            "No ABAD family hit. Suggested rule is a keyword floor, not a proof."
        )
    return {
        "receipt_id": receipt.id,
        "suggested_hardening": suggested,
        "model": JEEVES_MODEL,
        "notes": notes,
        "engagement": engagement,
    }


def _ollama_analyze(receipt: Receipt, host: str) -> dict[str, Any] | None:
    """Thin optional adapter. Never required. Short timeout. Local host only."""
    base = host.rstrip("/")
    url = base + "/api/generate"
    prompt = (
        "You are Jeeves for GodLock. Propose one short hardening rule for "
        "this counter-argument. Reply with JSON keys suggested_hardening and notes only.\n\n"
        + receipt.text[:2000]
    )
    payload = json.dumps({"model": "llama3.2", "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_S) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    text = (raw.get("response") or "").strip()
    if not text:
        return None
    suggested = text.splitlines()[0][:500]
    return {
        "receipt_id": receipt.id,
        "suggested_hardening": suggested,
        "model": f"ollama:{raw.get('model', 'unknown')}",
        "notes": "Ollama adapter (optional). Prompt truncated to 2000 chars.",
    }
