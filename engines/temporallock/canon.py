"""Canonical encoding for TemporalLock receipts (v0.1.0).

Canonical encoding
------------------
UTF-8 JSON with **sorted keys** and **no extra whitespace**
(``separators=(",", ":")``, ``sort_keys=True``, ``ensure_ascii=False``).

Hashed fields (core only, v0.1.0):

    timestamp, summary, evidence, confidence, prev_hash

The receipt's own ``hash`` field is **excluded** from the encoding.

``confidence`` is serialized as a JSON **number** with exactly **6 decimal
places** so hashes are stable across platforms and Python versions
(example: ``0.7`` becomes ``0.700000``). A placeholder-and-replace step
is used because ``json.dumps`` would otherwise emit ``0.7``.

Optional fields are allowed in implementations (extra JSONL keys) but
MUST NOT enter the core hash unless a later **versioned** schema is
introduced. v0.1.0 is core-only so chains stay verifiable long-term.

Genesis ``prev_hash`` is 64 zero hex characters.

Algorithm: SHA-256 of the canonical UTF-8 bytes; digest is lowercase hex.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Genesis previous-hash: 64 zero hex chars (SHA-256 width).
GENESIS_PREV_HASH = "0" * 64

# Confidence is always emitted with this many digits after the decimal.
CONFIDENCE_DECIMALS = 6

CORE_FIELDS = ("timestamp", "summary", "evidence", "confidence", "prev_hash")

_CONF_PLACEHOLDER = "__TL_CONFIDENCE__"


def format_confidence(confidence: float) -> str:
    """Return confidence as a fixed-precision decimal string (not quoted)."""
    return f"{float(confidence):.{CONFIDENCE_DECIMALS}f}"


def canonical_bytes(
    timestamp: str,
    summary: str,
    evidence: str,
    confidence: float,
    prev_hash: str,
) -> bytes:
    """Return the v0.1.0 canonical UTF-8 encoding of the core fields.

    Field order in the JSON object is lexicographic via ``sort_keys=True``:
    confidence, evidence, prev_hash, summary, timestamp.
    """
    payload: dict[str, Any] = {
        "confidence": _CONF_PLACEHOLDER,
        "evidence": evidence,
        "prev_hash": prev_hash,
        "summary": summary,
        "timestamp": timestamp,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    raw = raw.replace(f'"{_CONF_PLACEHOLDER}"', format_confidence(confidence))
    return raw.encode("utf-8")


def digest(
    timestamp: str,
    summary: str,
    evidence: str,
    confidence: float,
    prev_hash: str,
) -> str:
    """SHA-256 (lowercase hex) of ``canonical_bytes(...)``."""
    return hashlib.sha256(
        canonical_bytes(timestamp, summary, evidence, confidence, prev_hash)
    ).hexdigest()
