"""Tiny TemporalLock-style canonical digest for MirageGrid receipts.

Copied in-tree so this package does not depend on ``temporallock``.
Hashed fields (v0.1.0): session_id, mirage_node, timestamp, integrity.
The receipt's own ``hash`` field is excluded.

UTF-8 JSON, sorted keys, no extra whitespace (separators=(",", ":")).
``mirage_node`` is a JSON number (integer 1–25).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CORE_FIELDS = ("integrity", "mirage_node", "session_id", "timestamp")


def canonical_bytes(
    session_id: str,
    mirage_node: int,
    timestamp: str,
    integrity: str,
) -> bytes:
    payload: dict[str, Any] = {
        "integrity": integrity,
        "mirage_node": int(mirage_node),
        "session_id": session_id,
        "timestamp": timestamp,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return raw.encode("utf-8")


def digest(
    session_id: str,
    mirage_node: int,
    timestamp: str,
    integrity: str,
) -> str:
    """SHA-256 (lowercase hex) of ``canonical_bytes(...)``."""
    return hashlib.sha256(
        canonical_bytes(session_id, mirage_node, timestamp, integrity)
    ).hexdigest()
