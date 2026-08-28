"""Hashing helpers for TemporalLock.

Re-exports canonical encoding from ``canon`` so callers can use
``temporallock.hashing.canonical_bytes`` and ``temporallock.hashing.digest``
as specified. Stdlib ``hashlib`` only; no extra crypto packages.
"""

from __future__ import annotations

from temporallock.canon import (
    CONFIDENCE_DECIMALS,
    CORE_FIELDS,
    GENESIS_PREV_HASH,
    canonical_bytes,
    digest,
    format_confidence,
)

__all__ = [
    "CONFIDENCE_DECIMALS",
    "CORE_FIELDS",
    "GENESIS_PREV_HASH",
    "canonical_bytes",
    "digest",
    "format_confidence",
]
