"""TemporalLock: append-only observation receipts.

July 2026 whitepaper implementation by Aziel Eliab.

Receipts, not truth claims. Forks are welcome and always allowed.
No consensus, no mining, no tokens, no truth scores.
"""

from __future__ import annotations

from temporallock.chain import Chain, Fork, VerifyResult, detect_forks
from temporallock.errors import AppendOnlyError, ChainError, ReceiptError, TemporalLockError
from temporallock.hashing import GENESIS_PREV_HASH, canonical_bytes, digest
from temporallock.receipt import Receipt

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "AppendOnlyError",
    "Chain",
    "ChainError",
    "Fork",
    "GENESIS_PREV_HASH",
    "Receipt",
    "ReceiptError",
    "TemporalLockError",
    "VerifyResult",
    "canonical_bytes",
    "detect_forks",
    "digest",
    "__version__",
]
